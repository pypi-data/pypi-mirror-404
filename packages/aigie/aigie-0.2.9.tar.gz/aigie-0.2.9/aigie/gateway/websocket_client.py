"""
WebSocket Gateway Client - Real-Time Validation with Persistent Connections.

This module provides a WebSocket client for real-time validation with
<100ms latency target. It maintains persistent connections to the backend
gateway for low-latency pre-execution validation and receives push-based
interventions.

Key Features:
- Persistent WebSocket connection management
- Pre-execution validation hooks
- Real-time intervention receiving
- Reconnection with exponential backoff (2s interval, max 5 attempts)
- Validation result caching (max 100 results)
- Intervention caching (max 50 interventions)
- Keepalive ping every 30s

Architecture:
- Non-blocking: Runs in parallel with execution
- Fast: <100ms target latency for validation
- Resilient: Auto-reconnection, graceful degradation
- Observable: Detailed metrics and logging
"""

import asyncio
import json
import logging
import time
import hashlib
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable, Union

logger = logging.getLogger("aigie.gateway.websocket")


class WebSocketConnectionState(str, Enum):
    """WebSocket connection state for the gateway client."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ValidationResult:
    """Result of a tool call validation."""
    request_id: str
    tool_name: str
    decision: str  # "allow", "block", "modify", "delay"
    confidence: float = 1.0
    reason: Optional[str] = None
    modified_args: Optional[Dict[str, Any]] = None
    delay_ms: Optional[int] = None
    signals: List[Dict[str, Any]] = field(default_factory=list)
    latency_ms: float = 0.0
    cached: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tool_name": self.tool_name,
            "decision": self.decision,
            "confidence": self.confidence,
            "reason": self.reason,
            "modified_args": self.modified_args,
            "delay_ms": self.delay_ms,
            "signals": self.signals,
            "latency_ms": self.latency_ms,
            "cached": self.cached,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationResult":
        return cls(
            request_id=data.get("request_id", ""),
            tool_name=data.get("tool_name", ""),
            decision=data.get("decision", "allow"),
            confidence=data.get("confidence", 1.0),
            reason=data.get("reason"),
            modified_args=data.get("modified_args"),
            delay_ms=data.get("delay_ms"),
            signals=data.get("signals", []),
            latency_ms=data.get("latency_ms", 0.0),
            cached=data.get("cached", False),
        )


@dataclass
class Intervention:
    """An intervention signal pushed from the backend."""
    intervention_id: str
    trace_id: str
    intervention_type: str  # "block", "modify", "warn", "escalate"
    reason: str
    action: Optional[Dict[str, Any]] = None
    severity: str = "medium"  # "low", "medium", "high", "critical"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intervention_id": self.intervention_id,
            "trace_id": self.trace_id,
            "intervention_type": self.intervention_type,
            "reason": self.reason,
            "action": self.action,
            "severity": self.severity,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Intervention":
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.utcnow()
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.utcnow()

        return cls(
            intervention_id=data.get("intervention_id", ""),
            trace_id=data.get("trace_id", ""),
            intervention_type=data.get("intervention_type", "warn"),
            reason=data.get("reason", ""),
            action=data.get("action"),
            severity=data.get("severity", "medium"),
            metadata=data.get("metadata", {}),
            timestamp=timestamp,
            acknowledged=data.get("acknowledged", False),
        )


@dataclass
class WebSocketMetrics:
    """Metrics for WebSocket gateway client operations."""
    connections_attempted: int = 0
    connections_successful: int = 0
    connections_failed: int = 0
    reconnections: int = 0
    validations_sent: int = 0
    validations_received: int = 0
    validations_cached: int = 0
    validations_timed_out: int = 0
    validations_blocked: int = 0
    interventions_received: int = 0
    interventions_acknowledged: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    total_latency_ms: float = 0.0
    _latency_samples: List[float] = field(default_factory=list)

    def record_validation(self, latency_ms: float, decision: str, cached: bool = False):
        """Record a validation request."""
        self.validations_received += 1
        self.total_latency_ms += latency_ms
        self._latency_samples.append(latency_ms)

        # Keep only last 1000 samples
        if len(self._latency_samples) > 1000:
            self._latency_samples.pop(0)

        if cached:
            self.validations_cached += 1
        if decision == "block":
            self.validations_blocked += 1

    @property
    def avg_latency_ms(self) -> float:
        if not self._latency_samples:
            return 0.0
        return sum(self._latency_samples) / len(self._latency_samples)

    @property
    def p50_latency_ms(self) -> float:
        if not self._latency_samples:
            return 0.0
        sorted_samples = sorted(self._latency_samples)
        idx = len(sorted_samples) // 2
        return sorted_samples[idx]

    @property
    def p95_latency_ms(self) -> float:
        if not self._latency_samples:
            return 0.0
        sorted_samples = sorted(self._latency_samples)
        idx = int(len(sorted_samples) * 0.95)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]

    @property
    def p99_latency_ms(self) -> float:
        if not self._latency_samples:
            return 0.0
        sorted_samples = sorted(self._latency_samples)
        idx = int(len(sorted_samples) * 0.99)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connections_attempted": self.connections_attempted,
            "connections_successful": self.connections_successful,
            "connections_failed": self.connections_failed,
            "reconnections": self.reconnections,
            "validations_sent": self.validations_sent,
            "validations_received": self.validations_received,
            "validations_cached": self.validations_cached,
            "validations_timed_out": self.validations_timed_out,
            "validations_blocked": self.validations_blocked,
            "interventions_received": self.interventions_received,
            "interventions_acknowledged": self.interventions_acknowledged,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "avg_latency_ms": self.avg_latency_ms,
            "p50_latency_ms": self.p50_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
        }


class LRUCache:
    """Simple LRU cache for validation results."""

    def __init__(self, max_size: int = 100):
        self._max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._max_size:
                # Remove oldest item
                self._cache.popitem(last=False)
        self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)


class GatewayWebSocketClient:
    """
    Real-time WebSocket validation client with <100ms latency target.

    Features:
    - Persistent WebSocket connection to gateway
    - Pre-execution validation for tool calls
    - Real-time intervention receiving via push
    - Automatic reconnection with exponential backoff
    - Validation result caching
    - Intervention caching
    - Keepalive ping mechanism
    """

    # Configuration defaults
    DEFAULT_RECONNECT_INTERVAL_SEC = 2.0
    DEFAULT_MAX_RECONNECT_ATTEMPTS = 5
    DEFAULT_VALIDATION_TIMEOUT_MS = 100
    DEFAULT_CONNECT_TIMEOUT_SEC = 10
    DEFAULT_PING_INTERVAL_SEC = 30
    DEFAULT_VALIDATION_CACHE_SIZE = 100
    DEFAULT_INTERVENTION_CACHE_SIZE = 50

    def __init__(
        self,
        api_url: str,
        api_key: str,
        *,
        validation_timeout_ms: float = DEFAULT_VALIDATION_TIMEOUT_MS,
        connect_timeout_sec: float = DEFAULT_CONNECT_TIMEOUT_SEC,
        ping_interval_sec: float = DEFAULT_PING_INTERVAL_SEC,
        reconnect_interval_sec: float = DEFAULT_RECONNECT_INTERVAL_SEC,
        max_reconnect_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS,
        validation_cache_size: int = DEFAULT_VALIDATION_CACHE_SIZE,
        intervention_cache_size: int = DEFAULT_INTERVENTION_CACHE_SIZE,
        enable_validation_cache: bool = True,
        enable_interventions: bool = True,
        fallback_on_error: str = "allow",  # "allow" or "block"
    ):
        """
        Initialize the WebSocket gateway client.

        Args:
            api_url: Base API URL (converted to WebSocket URL)
            api_key: API key for authentication
            validation_timeout_ms: Timeout for validation requests (default: 100ms)
            connect_timeout_sec: Timeout for WebSocket connection
            ping_interval_sec: Interval for keepalive pings (default: 30s)
            reconnect_interval_sec: Base interval for reconnection attempts (default: 2s)
            max_reconnect_attempts: Maximum reconnection attempts (default: 5)
            validation_cache_size: Max cached validation results (default: 100)
            intervention_cache_size: Max cached interventions (default: 50)
            enable_validation_cache: Whether to cache validation results
            enable_interventions: Whether to process intervention signals
            fallback_on_error: Default decision when gateway unavailable
        """
        # Convert HTTP URL to WebSocket URL
        ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = ws_url.rstrip("/api").rstrip("/")
        self._ws_url = f"{ws_url}/api/v1/gateway/ws"

        self._api_key = api_key
        self._validation_timeout_ms = validation_timeout_ms
        self._connect_timeout_sec = connect_timeout_sec
        self._ping_interval_sec = ping_interval_sec
        self._reconnect_interval_sec = reconnect_interval_sec
        self._max_reconnect_attempts = max_reconnect_attempts
        self._enable_validation_cache = enable_validation_cache
        self._enable_interventions = enable_interventions
        self._fallback_decision = fallback_on_error

        # Connection state
        self._state = WebSocketConnectionState.DISCONNECTED
        self._websocket = None
        self._connection_id: Optional[str] = None
        self._reconnect_attempts = 0
        self._last_connect_time: Optional[datetime] = None

        # Request/response tracking
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._request_counter = 0

        # Caches
        self._validation_cache = LRUCache(max_size=validation_cache_size)
        self._intervention_cache = LRUCache(max_size=intervention_cache_size)

        # Intervention callbacks
        self._intervention_callbacks: List[Callable[[Intervention], Awaitable[None]]] = []

        # Trace subscriptions
        self._subscribed_traces: set = set()

        # Background tasks
        self._receive_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        # Metrics
        self._metrics = WebSocketMetrics()

        # Lock for thread safety
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Check if connected to gateway."""
        return self._state == WebSocketConnectionState.CONNECTED and self._websocket is not None

    @property
    def state(self) -> WebSocketConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def connection_id(self) -> Optional[str]:
        """Get the current connection ID."""
        return self._connection_id

    @property
    def metrics(self) -> WebSocketMetrics:
        """Get client metrics."""
        return self._metrics

    async def connect(self, url: Optional[str] = None) -> bool:
        """
        Establish WebSocket connection to gateway.

        Args:
            url: Optional override URL for connection

        Returns:
            True if connected successfully, False otherwise
        """
        if self._state == WebSocketConnectionState.CONNECTED:
            return True

        async with self._lock:
            if self._state == WebSocketConnectionState.CONNECTED:
                return True

            self._state = WebSocketConnectionState.CONNECTING
            self._metrics.connections_attempted += 1
            target_url = url or self._ws_url

            logger.info(f"Connecting to gateway WebSocket: {target_url}")

            try:
                import websockets
            except ImportError:
                logger.warning(
                    "websockets package not installed. "
                    "Install with: pip install websockets"
                )
                self._state = WebSocketConnectionState.FAILED
                self._metrics.connections_failed += 1
                return False

            try:
                # Build connection URL with auth
                connect_url = f"{target_url}?api_key={self._api_key}&client_type=sdk&client_version=2.0.0"

                self._websocket = await asyncio.wait_for(
                    websockets.connect(
                        connect_url,
                        ping_interval=None,  # We handle pings ourselves
                        ping_timeout=10,
                        close_timeout=5,
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
                self._metrics.messages_received += 1

                self._state = WebSocketConnectionState.CONNECTED
                self._reconnect_attempts = 0
                self._last_connect_time = datetime.utcnow()
                self._metrics.connections_successful += 1

                logger.info(f"Connected to gateway (connection_id: {self._connection_id})")

                # Start background tasks
                self._receive_task = asyncio.create_task(self._receive_loop())
                self._ping_task = asyncio.create_task(self._ping_loop())

                # Resubscribe to previously subscribed traces
                for trace_id in self._subscribed_traces:
                    await self._send_subscribe(trace_id)

                return True

            except asyncio.TimeoutError:
                logger.error(f"Connection timeout after {self._connect_timeout_sec}s")
                self._state = WebSocketConnectionState.FAILED
                self._metrics.connections_failed += 1
                self._schedule_reconnect()
                return False

            except Exception as e:
                logger.error(f"Failed to connect to gateway: {e}")
                self._state = WebSocketConnectionState.FAILED
                self._metrics.connections_failed += 1
                self._schedule_reconnect()
                return False

    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        async with self._lock:
            self._state = WebSocketConnectionState.DISCONNECTED

            # Cancel background tasks
            for task in [self._receive_task, self._ping_task, self._reconnect_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            self._receive_task = None
            self._ping_task = None
            self._reconnect_task = None

            # Close WebSocket
            if self._websocket:
                try:
                    await self._websocket.close()
                except Exception:
                    pass
                self._websocket = None

            # Cancel pending requests
            for future in self._pending_requests.values():
                if not future.done():
                    future.cancel()
            self._pending_requests.clear()

            self._connection_id = None
            logger.info("Disconnected from gateway WebSocket")

    async def validate_tool_call(
        self,
        tool_name: str,
        args: Dict[str, Any],
        *,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        timeout_ms: Optional[float] = None,
        use_cache: bool = True,
    ) -> ValidationResult:
        """
        Validate a tool call before execution.

        This is the main entry point for pre-execution validation.
        Target latency: <100ms.

        Args:
            tool_name: Name of the tool being called
            args: Tool call arguments
            trace_id: Optional trace ID for context
            span_id: Optional span ID for context
            timeout_ms: Request timeout in milliseconds
            use_cache: Whether to use cached results

        Returns:
            ValidationResult with decision and any modifications
        """
        start_time = time.perf_counter()
        timeout = (timeout_ms or self._validation_timeout_ms) / 1000.0

        # Generate request ID
        self._request_counter += 1
        request_id = f"val_{self._request_counter}_{int(time.time() * 1000)}"

        # Check cache first
        if use_cache and self._enable_validation_cache:
            cache_key = self._make_cache_key(tool_name, args)
            cached = self._validation_cache.get(cache_key)
            if cached:
                latency_ms = (time.perf_counter() - start_time) * 1000
                cached.latency_ms = latency_ms
                cached.cached = True
                self._metrics.record_validation(latency_ms, cached.decision, cached=True)
                return cached

        # Check connection
        if not self.is_connected:
            return self._make_fallback_result(
                request_id=request_id,
                tool_name=tool_name,
                reason="Not connected to gateway",
                start_time=start_time,
            )

        self._metrics.validations_sent += 1

        try:
            # Create future for response
            future = asyncio.get_event_loop().create_future()
            self._pending_requests[request_id] = future

            # Send validation request
            message = {
                "type": "validate_tool_call",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "tool_name": tool_name,
                    "arguments": args,
                    "trace_id": trace_id,
                    "span_id": span_id,
                },
            }

            await self._websocket.send(json.dumps(message))
            self._metrics.messages_sent += 1

            # Wait for response
            response_data = await asyncio.wait_for(future, timeout=timeout)

            latency_ms = (time.perf_counter() - start_time) * 1000
            result = ValidationResult(
                request_id=request_id,
                tool_name=tool_name,
                decision=response_data.get("decision", "allow"),
                confidence=response_data.get("confidence", 1.0),
                reason=response_data.get("reason"),
                modified_args=response_data.get("modified_args"),
                delay_ms=response_data.get("delay_ms"),
                signals=response_data.get("signals", []),
                latency_ms=latency_ms,
                cached=False,
            )

            # Cache the result
            if self._enable_validation_cache:
                cache_key = self._make_cache_key(tool_name, args)
                self._validation_cache.put(cache_key, result)

            # Record metrics
            self._metrics.record_validation(latency_ms, result.decision)

            return result

        except asyncio.TimeoutError:
            self._metrics.validations_timed_out += 1
            return self._make_fallback_result(
                request_id=request_id,
                tool_name=tool_name,
                reason=f"Validation timeout ({timeout * 1000:.0f}ms)",
                start_time=start_time,
            )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return self._make_fallback_result(
                request_id=request_id,
                tool_name=tool_name,
                reason=f"Validation error: {str(e)}",
                start_time=start_time,
            )

        finally:
            self._pending_requests.pop(request_id, None)

    async def receive_intervention(self) -> Optional[Intervention]:
        """
        Receive the next pending intervention.

        Returns the oldest unacknowledged intervention, or None if none pending.
        """
        # Check intervention cache for unacknowledged interventions
        for key in list(self._intervention_cache._cache.keys()):
            intervention = self._intervention_cache.get(key)
            if intervention and not intervention.acknowledged:
                return intervention
        return None

    def on_intervention(self, callback: Callable[[Intervention], Awaitable[None]]) -> None:
        """
        Register callback for intervention signals.

        Interventions are pushed from the backend when issues
        are detected during execution.

        Args:
            callback: Async callback function that receives Intervention
        """
        self._intervention_callbacks.append(callback)

    def remove_intervention_callback(self, callback: Callable[[Intervention], Awaitable[None]]) -> bool:
        """Remove an intervention callback."""
        try:
            self._intervention_callbacks.remove(callback)
            return True
        except ValueError:
            return False

    async def acknowledge_intervention(self, intervention_id: str) -> bool:
        """
        Acknowledge an intervention.

        Args:
            intervention_id: ID of the intervention to acknowledge

        Returns:
            True if acknowledged successfully
        """
        intervention = self._intervention_cache.get(intervention_id)
        if intervention:
            intervention.acknowledged = True
            self._metrics.interventions_acknowledged += 1

            # Send acknowledgment to backend
            if self.is_connected:
                try:
                    message = {
                        "type": "acknowledge_intervention",
                        "timestamp": datetime.utcnow().isoformat(),
                        "payload": {"intervention_id": intervention_id},
                    }
                    await self._websocket.send(json.dumps(message))
                    self._metrics.messages_sent += 1
                except Exception as e:
                    logger.warning(f"Failed to send intervention acknowledgment: {e}")

            return True
        return False

    def subscribe_to_trace(self, trace_id: str) -> None:
        """Subscribe to interventions for a specific trace."""
        self._subscribed_traces.add(trace_id)
        if self.is_connected:
            asyncio.create_task(self._send_subscribe(trace_id))

    def unsubscribe_from_trace(self, trace_id: str) -> None:
        """Unsubscribe from trace interventions."""
        self._subscribed_traces.discard(trace_id)
        if self.is_connected:
            asyncio.create_task(self._send_unsubscribe(trace_id))

    async def _send_subscribe(self, trace_id: str) -> None:
        """Send subscribe message."""
        if self._websocket:
            try:
                await self._websocket.send(json.dumps({
                    "type": "subscribe",
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload": {"trace_id": trace_id},
                }))
                self._metrics.messages_sent += 1
            except Exception as e:
                logger.warning(f"Failed to subscribe to trace {trace_id}: {e}")

    async def _send_unsubscribe(self, trace_id: str) -> None:
        """Send unsubscribe message."""
        if self._websocket:
            try:
                await self._websocket.send(json.dumps({
                    "type": "unsubscribe",
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload": {"trace_id": trace_id},
                }))
                self._metrics.messages_sent += 1
            except Exception as e:
                logger.warning(f"Failed to unsubscribe from trace {trace_id}: {e}")

    async def _receive_loop(self) -> None:
        """Background task to receive messages from gateway."""
        while self._state == WebSocketConnectionState.CONNECTED and self._websocket:
            try:
                message = await self._websocket.recv()
                self._metrics.messages_received += 1
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
                            intervention = Intervention.from_dict(payload)
                            # Cache the intervention
                            self._intervention_cache.put(
                                intervention.intervention_id,
                                intervention
                            )
                            # Notify callbacks
                            for callback in self._intervention_callbacks:
                                asyncio.create_task(
                                    self._safe_callback(callback, intervention)
                                )
                        except Exception as e:
                            logger.warning(f"Failed to parse intervention: {e}")

                elif msg_type == "pong":
                    # Keepalive response, ignore
                    pass

                elif msg_type == "ping":
                    # Respond to server ping
                    await self._websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    }))
                    self._metrics.messages_sent += 1

                elif msg_type == "error":
                    logger.warning(f"Gateway error: {data.get('error')}")

                elif msg_type == "mode_change":
                    # Mode change notification from backend
                    payload = data.get("payload", {})
                    logger.info(f"Mode change notification: {payload}")
                    # This will be handled by ModeController

            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._state == WebSocketConnectionState.CONNECTED:
                    logger.error(f"Receive error: {e}")
                    await self._handle_disconnect()
                break

    async def _ping_loop(self) -> None:
        """Background task for keepalive pings."""
        while self._state == WebSocketConnectionState.CONNECTED and self._websocket:
            try:
                await asyncio.sleep(self._ping_interval_sec)
                if self._websocket and self._state == WebSocketConnectionState.CONNECTED:
                    await self._websocket.send(json.dumps({
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat(),
                        "payload": {"connection_id": self._connection_id},
                    }))
                    self._metrics.messages_sent += 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Ping error: {e}")
                break

    async def _handle_disconnect(self) -> None:
        """Handle unexpected disconnection."""
        self._state = WebSocketConnectionState.DISCONNECTED
        self._schedule_reconnect()

    def _schedule_reconnect(self) -> None:
        """Schedule a reconnection attempt."""
        if self._reconnect_attempts < self._max_reconnect_attempts:
            if self._reconnect_task is None or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        """Attempt to reconnect to gateway with exponential backoff."""
        while self._reconnect_attempts < self._max_reconnect_attempts:
            self._state = WebSocketConnectionState.RECONNECTING
            self._reconnect_attempts += 1
            self._metrics.reconnections += 1

            # Exponential backoff: 2s, 4s, 8s, 16s, 32s
            wait_time = self._reconnect_interval_sec * (2 ** (self._reconnect_attempts - 1))
            wait_time = min(wait_time, 60)  # Cap at 60 seconds

            logger.info(
                f"Reconnecting in {wait_time:.1f}s "
                f"(attempt {self._reconnect_attempts}/{self._max_reconnect_attempts})"
            )

            await asyncio.sleep(wait_time)

            if await self.connect():
                logger.info("Reconnection successful")
                return

        logger.error(f"Max reconnection attempts ({self._max_reconnect_attempts}) reached")
        self._state = WebSocketConnectionState.FAILED

    def _make_cache_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Create a cache key for validation results."""
        content = json.dumps({"tool": tool_name, "args": args}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def _make_fallback_result(
        self,
        request_id: str,
        tool_name: str,
        reason: str,
        start_time: float,
    ) -> ValidationResult:
        """Create a fallback validation result."""
        latency_ms = (time.perf_counter() - start_time) * 1000
        return ValidationResult(
            request_id=request_id,
            tool_name=tool_name,
            decision=self._fallback_decision,
            confidence=0.0,
            reason=reason,
            latency_ms=latency_ms,
            cached=False,
        )

    async def _safe_callback(
        self,
        callback: Callable[[Intervention], Awaitable[None]],
        intervention: Intervention,
    ) -> None:
        """Safely call a callback function."""
        try:
            await callback(intervention)
        except Exception as e:
            logger.warning(f"Intervention callback error: {e}")

    def clear_validation_cache(self) -> None:
        """Clear the validation result cache."""
        self._validation_cache.clear()

    def clear_intervention_cache(self) -> None:
        """Clear the intervention cache."""
        self._intervention_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self._metrics.to_dict(),
            "state": self._state.value,
            "connection_id": self._connection_id,
            "pending_requests": len(self._pending_requests),
            "validation_cache_size": len(self._validation_cache),
            "intervention_cache_size": len(self._intervention_cache),
            "subscribed_traces": len(self._subscribed_traces),
            "reconnect_attempts": self._reconnect_attempts,
            "last_connect_time": self._last_connect_time.isoformat() if self._last_connect_time else None,
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._metrics = WebSocketMetrics()

    async def __aenter__(self) -> "GatewayWebSocketClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
