"""
Gateway Module - Real-Time Agent Validation

This module provides client-side components for real-time agent validation,
enabling proactive error prevention and intervention.

Key Components:
- GatewayClient: WebSocket client for backend validation
- ToolCallMiddleware: Middleware for intercepting tool calls
- StreamingObserver: Observer for streaming span events

Architecture Philosophy:
- Non-blocking: Runs in parallel with execution, never gates it
- Fast detection: Sub-100ms validation latency target
- Graceful fallback: Fail-open on connection issues
- Learning integration: Feeds patterns back to backend
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

__all__ = [
    # Client
    "GatewayClient",
    "GatewayConnectionState",
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
