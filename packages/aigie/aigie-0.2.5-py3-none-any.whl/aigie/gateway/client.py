"""
Gateway Client - WebSocket Client for Real-Time Validation

Provides persistent WebSocket connection to the backend gateway
for low-latency pre-execution validation.

Architecture Principles (inspired by market leaders):
- Netflix Zuul: Edge service with circuit breakers
- Stripe Radar: Real-time validation with rules + ML
- Cloudflare: Sub-millisecond edge decisions
- Google SRE: Graceful degradation, error budgets

Key Features:
- Non-blocking: Runs in parallel, never gates execution
- Fast: <100ms target latency for validation
- Resilient: Auto-reconnection, fallback strategies
- Observable: Detailed metrics and logging
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable

from .validation import (
    GatewayDecision,
    PreExecutionRequest,
    PreExecutionResponse,
    InterventionSignal,
)
from .fallback import FallbackMode, FallbackStrategy

logger = logging.getLogger("aigie.gateway.client")


class GatewayConnectionState(str, Enum):
    """WebSocket connection state."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class GatewayMetrics:
    """Metrics for gateway client operations."""
    validations_sent: int = 0
    validations_received: int = 0
    validations_timed_out: int = 0
    validations_blocked: int = 0
    validations_modified: int = 0
    fallbacks_used: int = 0
    interventions_received: int = 0
    reconnections: int = 0
    total_latency_ms: float = 0.0
    _latency_samples: List[float] = field(default_factory=list)

    def record_validation(self, latency_ms: float, decision: GatewayDecision):
        """Record a validation request."""
        self.validations_received += 1
        self.total_latency_ms += latency_ms
        self._latency_samples.append(latency_ms)
        if len(self._latency_samples) > 1000:
            self._latency_samples.pop(0)

        if decision == GatewayDecision.BLOCK:
            self.validations_blocked += 1
        elif decision == GatewayDecision.MODIFY:
            self.validations_modified += 1

    @property
    def avg_latency_ms(self) -> float:
        if self.validations_received == 0:
            return 0.0
        return self.total_latency_ms / self.validations_received

    @property
    def p95_latency_ms(self) -> float:
        if not self._latency_samples:
            return 0.0
        sorted_samples = sorted(self._latency_samples)
        idx = int(len(sorted_samples) * 0.95)
        return sorted_samples[idx]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validations_sent": self.validations_sent,
            "validations_received": self.validations_received,
            "validations_timed_out": self.validations_timed_out,
            "validations_blocked": self.validations_blocked,
            "validations_modified": self.validations_modified,
            "fallbacks_used": self.fallbacks_used,
            "interventions_received": self.interventions_received,
            "reconnections": self.reconnections,
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
        }


class GatewayClient:
    """
    WebSocket client for real-time gateway validation.

    Features:
    - Persistent WebSocket connection for low latency
    - Automatic reconnection with exponential backoff
    - Request/response correlation
    - Intervention signal subscription
    - Graceful fallback on connection issues
    - Circuit breaker pattern
    """

    # Default timeouts
    DEFAULT_VALIDATION_TIMEOUT_MS = 100  # 100ms target
    DEFAULT_CONNECT_TIMEOUT_SEC = 10
    DEFAULT_PING_INTERVAL_SEC = 30

    def __init__(
        self,
        api_url: str,
        api_key: str,
        validation_timeout_ms: float = DEFAULT_VALIDATION_TIMEOUT_MS,
        connect_timeout_sec: float = DEFAULT_CONNECT_TIMEOUT_SEC,
        ping_interval_sec: float = DEFAULT_PING_INTERVAL_SEC,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 10,
        fallback_mode: FallbackMode = FallbackMode.ALLOW,
        enable_interventions: bool = True,
    ):
        """
        Initialize the gateway client.

        Args:
            api_url: Base API URL (converted to WebSocket URL)
            api_key: API key for authentication
            validation_timeout_ms: Timeout for validation requests (default: 100ms)
            connect_timeout_sec: Timeout for WebSocket connection
            ping_interval_sec: Interval for keepalive pings
            auto_reconnect: Whether to automatically reconnect
            max_reconnect_attempts: Maximum reconnection attempts
            fallback_mode: Fallback mode when gateway unavailable
            enable_interventions: Whether to process intervention signals
        """
        # Convert HTTP URL to WebSocket URL
        ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = ws_url.rstrip("/api").rstrip("/")
        self._ws_url = f"{ws_url}/api/v1/gateway/ws"

        self._api_key = api_key
        self._validation_timeout_ms = validation_timeout_ms
        self._connect_timeout_sec = connect_timeout_sec
        self._ping_interval_sec = ping_interval_sec
        self._auto_reconnect = auto_reconnect
        self._max_reconnect_attempts = max_reconnect_attempts
        self._enable_interventions = enable_interventions

        # Connection state
        self._state = GatewayConnectionState.DISCONNECTED
        self._websocket = None
        self._connection_id: Optional[str] = None
        self._reconnect_attempts = 0

        # Request/response tracking
        self._pending_requests: Dict[str, asyncio.Future] = {}

        # Fallback strategy
        self._fallback = FallbackStrategy(
            mode=fallback_mode,
            enable_local_loop_detection=True,
        )

        # Intervention callbacks
        self._intervention_callbacks: List[Callable[[InterventionSignal], Awaitable[None]]] = []

        # Background tasks
        self._receive_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        # Metrics
        self._metrics = GatewayMetrics()

        # Circuit breaker
        self._circuit_open = False
        self._circuit_failures = 0
        self._circuit_open_until: Optional[datetime] = None
        self._circuit_failure_threshold = 5
        self._circuit_reset_timeout_sec = 30

    @property
    def is_connected(self) -> bool:
        """Check if connected to gateway."""
        return self._state == GatewayConnectionState.CONNECTED and self._websocket is not None

    @property
    def state(self) -> GatewayConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def metrics(self) -> GatewayMetrics:
        """Get client metrics."""
        return self._metrics

    async def connect(self) -> bool:
        """
        Establish WebSocket connection to gateway.

        Returns:
            True if connected successfully, False otherwise
        """
        if self._state == GatewayConnectionState.CONNECTED:
            return True

        self._state = GatewayConnectionState.CONNECTING
        logger.info(f"Connecting to gateway: {self._ws_url}")

        try:
            import websockets

            # Build query parameters
            params = f"?api_key={self._api_key}&client_type=sdk&client_version=2.0.0"

            self._websocket = await asyncio.wait_for(
                websockets.connect(
                    self._ws_url + params,
                    ping_interval=self._ping_interval_sec,
                    ping_timeout=10,
                ),
                timeout=self._connect_timeout_sec,
            )

            # Wait for welcome message
            welcome_msg = await asyncio.wait_for(
                self._websocket.recv(),
                timeout=5.0
            )
            welcome_data = json.loads(welcome_msg)
            self._connection_id = welcome_data.get("connection_id")

            self._state = GatewayConnectionState.CONNECTED
            self._reconnect_attempts = 0
            self._circuit_failures = 0
            self._circuit_open = False

            logger.info(f"Connected to gateway (connection_id: {self._connection_id})")

            # Start background tasks
            self._receive_task = asyncio.create_task(self._receive_loop())
            self._ping_task = asyncio.create_task(self._ping_loop())

            return True

        except ImportError:
            logger.warning("websockets package not installed, gateway disabled")
            self._state = GatewayConnectionState.FAILED
            return False

        except Exception as e:
            logger.error(f"Failed to connect to gateway: {e}")
            self._state = GatewayConnectionState.FAILED

            if self._auto_reconnect:
                self._reconnect_task = asyncio.create_task(self._reconnect())

            return False

    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        self._state = GatewayConnectionState.DISCONNECTED

        # Cancel background tasks
        for task in [self._receive_task, self._ping_task, self._reconnect_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close WebSocket
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:
                pass
            self._websocket = None

        # Cancel pending requests
        for future in self._pending_requests.values():
            future.cancel()
        self._pending_requests.clear()

        logger.info("Disconnected from gateway")

    async def validate(
        self,
        request: PreExecutionRequest,
        timeout_ms: Optional[float] = None
    ) -> PreExecutionResponse:
        """
        Validate a tool call before execution.

        This is the main entry point for pre-execution validation.
        Target latency: <100ms.

        Args:
            request: Pre-execution validation request
            timeout_ms: Request timeout in milliseconds

        Returns:
            PreExecutionResponse with decision and signals
        """
        start_time = time.perf_counter()
        timeout = (timeout_ms or self._validation_timeout_ms) / 1000.0

        # Check circuit breaker
        if self._is_circuit_open():
            self._metrics.fallbacks_used += 1
            return self._fallback.get_fallback_response(
                request,
                reason="Circuit breaker open"
            )

        # Check connection
        if not self.is_connected:
            self._metrics.fallbacks_used += 1
            return self._fallback.get_fallback_response(
                request,
                reason="Not connected to gateway"
            )

        self._metrics.validations_sent += 1

        try:
            # Create future for response
            request_id = request.request_id
            future = asyncio.get_event_loop().create_future()
            self._pending_requests[request_id] = future

            # Send validation request
            message = {
                "type": "validate",
                "timestamp": datetime.utcnow().isoformat(),
                "payload": request.to_dict(),
            }

            await self._websocket.send(json.dumps(message))

            # Wait for response
            response_data = await asyncio.wait_for(future, timeout=timeout)

            latency_ms = (time.perf_counter() - start_time) * 1000
            response = PreExecutionResponse.from_dict(response_data)
            response.latency_ms = latency_ms

            # Record metrics
            self._metrics.record_validation(latency_ms, response.decision)
            self._record_circuit_success()

            # Cache for fallback
            self._fallback.cache_decision(request, response)

            # Record tool call for loop detection
            self._fallback.record_tool_call(
                request.trace_context.trace_id,
                request.tool_call.name
            )

            return response

        except asyncio.TimeoutError:
            self._metrics.validations_timed_out += 1
            self._record_circuit_failure()

            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Validation timed out after {latency_ms:.1f}ms")

            self._metrics.fallbacks_used += 1
            return self._fallback.get_fallback_response(
                request,
                reason=f"Validation timeout ({latency_ms:.0f}ms)"
            )

        except Exception as e:
            self._record_circuit_failure()
            logger.error(f"Validation error: {e}")

            self._metrics.fallbacks_used += 1
            return self._fallback.get_fallback_response(
                request,
                reason=f"Validation error: {str(e)}"
            )

        finally:
            self._pending_requests.pop(request_id, None)

    def on_intervention(
        self,
        callback: Callable[[InterventionSignal], Awaitable[None]]
    ):
        """
        Register callback for intervention signals.

        Interventions are pushed from the backend when issues
        are detected during execution.

        Args:
            callback: Async callback function
        """
        self._intervention_callbacks.append(callback)

    def subscribe_to_trace(self, trace_id: str):
        """Subscribe to interventions for a specific trace."""
        if self.is_connected:
            asyncio.create_task(self._send_subscribe(trace_id))

    def unsubscribe_from_trace(self, trace_id: str):
        """Unsubscribe from trace interventions."""
        if self.is_connected:
            asyncio.create_task(self._send_unsubscribe(trace_id))

    async def _send_subscribe(self, trace_id: str):
        """Send subscribe message."""
        if self._websocket:
            await self._websocket.send(json.dumps({
                "type": "subscribe",
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {"trace_id": trace_id},
            }))

    async def _send_unsubscribe(self, trace_id: str):
        """Send unsubscribe message."""
        if self._websocket:
            await self._websocket.send(json.dumps({
                "type": "unsubscribe",
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {"trace_id": trace_id},
            }))

    async def _receive_loop(self):
        """Background task to receive messages from gateway."""
        while self._state == GatewayConnectionState.CONNECTED and self._websocket:
            try:
                message = await self._websocket.recv()
                data = json.loads(message)

                msg_type = data.get("type")

                if msg_type == "validation_result":
                    # Handle validation response
                    payload = data.get("payload", {})
                    request_id = payload.get("request_id")
                    if request_id in self._pending_requests:
                        future = self._pending_requests[request_id]
                        if not future.done():
                            future.set_result(payload)

                elif msg_type == "intervention":
                    # Handle intervention signal
                    if self._enable_interventions:
                        self._metrics.interventions_received += 1
                        payload = data.get("payload", {})
                        try:
                            intervention = InterventionSignal.from_dict(payload)
                            for callback in self._intervention_callbacks:
                                asyncio.create_task(callback(intervention))
                        except Exception as e:
                            logger.warning(f"Failed to parse intervention: {e}")

                elif msg_type == "pong" or msg_type == "ping":
                    # Keepalive, ignore
                    pass

                elif msg_type == "error":
                    logger.warning(f"Gateway error: {data.get('error')}")

            except Exception as e:
                if self._state == GatewayConnectionState.CONNECTED:
                    logger.error(f"Receive error: {e}")
                    await self._handle_disconnect()
                break

    async def _ping_loop(self):
        """Background task for keepalive pings."""
        while self._state == GatewayConnectionState.CONNECTED and self._websocket:
            try:
                await asyncio.sleep(self._ping_interval_sec)
                if self._websocket:
                    await self._websocket.send(json.dumps({
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat(),
                        "payload": {},
                    }))
            except Exception:
                break

    async def _handle_disconnect(self):
        """Handle unexpected disconnection."""
        self._state = GatewayConnectionState.DISCONNECTED
        if self._auto_reconnect:
            self._reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self):
        """Attempt to reconnect to gateway."""
        while self._reconnect_attempts < self._max_reconnect_attempts:
            self._state = GatewayConnectionState.RECONNECTING
            self._reconnect_attempts += 1
            self._metrics.reconnections += 1

            # Exponential backoff
            wait_time = min(2 ** self._reconnect_attempts, 60)
            logger.info(f"Reconnecting in {wait_time}s (attempt {self._reconnect_attempts})")

            await asyncio.sleep(wait_time)

            if await self.connect():
                return

        logger.error("Max reconnection attempts reached")
        self._state = GatewayConnectionState.FAILED

    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if not self._circuit_open:
            return False

        # Check if reset timeout has passed
        if self._circuit_open_until and datetime.utcnow() > self._circuit_open_until:
            self._circuit_open = False
            self._circuit_failures = 0
            logger.info("Circuit breaker reset")
            return False

        return True

    def _record_circuit_failure(self):
        """Record a failure for circuit breaker."""
        self._circuit_failures += 1
        if self._circuit_failures >= self._circuit_failure_threshold:
            self._circuit_open = True
            self._circuit_open_until = datetime.utcnow() + \
                asyncio.timedelta(seconds=self._circuit_reset_timeout_sec)
            logger.warning(f"Circuit breaker opened after {self._circuit_failures} failures")

    def _record_circuit_success(self):
        """Record a success for circuit breaker."""
        self._circuit_failures = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self._metrics.to_dict(),
            "state": self._state.value,
            "connection_id": self._connection_id,
            "pending_requests": len(self._pending_requests),
            "circuit_open": self._circuit_open,
            "circuit_failures": self._circuit_failures,
            "fallback": self._fallback.get_stats(),
        }
