"""
Gateway Module - Real-Time Agent Validation

This module provides client-side components for real-time agent validation,
enabling proactive error prevention and intervention.

Key Components:
- GatewayClient: HTTP client for backend validation
- GatewayWebSocketClient: WebSocket client for real-time validation (<100ms latency)
- ToolCallMiddleware: Middleware for intercepting tool calls
- StreamingObserver: Observer for streaming span events

Architecture Philosophy:
- Non-blocking: Runs in parallel with execution, never gates it
- Fast detection: Sub-100ms validation latency target
- Graceful fallback: Fail-open on connection issues
- Learning integration: Feeds patterns back to backend

WebSocket Client Features:
- Persistent WebSocket connection management
- Pre-execution validation hooks
- Real-time intervention receiving
- Reconnection with exponential backoff (2s interval, max 5 attempts)
- Validation result caching (max 100 results)
- Intervention caching (max 50 interventions)
- Keepalive ping every 30s
"""

from .client import GatewayClient, GatewayConnectionState
from .middleware import ToolCallMiddleware, ToolCallResult
from .validation import (
    PreExecutionRequest,
    PreExecutionResponse,
    GatewayDecision,
    ValidationSignal,
    SignalType,
    InterventionSignal,
)
from .fallback import FallbackMode, FallbackStrategy
from .handlers import (
    InterventionHandler,
    BlockHandler,
    ModifyHandler,
    DelayHandler,
    EscalateHandler,
    HandlerChain,
    HandlerResult,
    InterventionType,
    ExecutionBlockedError,
    InterventionHandlerError,
)
from .websocket_client import (
    GatewayWebSocketClient,
    WebSocketConnectionState,
    ValidationResult,
    Intervention,
    WebSocketMetrics,
    LRUCache,
)

__all__ = [
    # HTTP Client
    "GatewayClient",
    "GatewayConnectionState",
    # WebSocket Client
    "GatewayWebSocketClient",
    "WebSocketConnectionState",
    "ValidationResult",
    "Intervention",
    "WebSocketMetrics",
    "LRUCache",
    # Middleware
    "ToolCallMiddleware",
    "ToolCallResult",
    # Validation models
    "PreExecutionRequest",
    "PreExecutionResponse",
    "GatewayDecision",
    "ValidationSignal",
    "SignalType",
    "InterventionSignal",
    # Fallback
    "FallbackMode",
    "FallbackStrategy",
    # Handlers
    "InterventionHandler",
    "BlockHandler",
    "ModifyHandler",
    "DelayHandler",
    "EscalateHandler",
    "HandlerChain",
    "HandlerResult",
    "InterventionType",
    "ExecutionBlockedError",
    "InterventionHandlerError",
]
