"""
Tool Call Middleware - Parallel Monitoring & Intervention

CRITICAL ARCHITECTURE: This middleware runs IN PARALLEL with tool execution.
We NEVER block or gate the execution path - we OBSERVE and INTERVENE.

The middleware monitors tool calls in parallel with their execution. When issues
are detected (loops, drift, errors), we trigger interventions (rerun, redirect,
correct) rather than blocking the execution.

Architecture (Inspired by Market Leaders):
- Netflix Hystrix: Fail-open design, circuit breakers that never block happy path
- Stripe Radar: Fraud detection runs in parallel, flags don't block payments
- Datadog APM: Zero-latency observability through async processing
- Google Dapper: Distributed tracing with minimal overhead

Key Principles:
- PARALLEL EXECUTION: Monitor alongside, never in critical path
- OBSERVE MODE DEFAULT: Log issues without blocking (block_on_high_risk=False)
- FAST DETECTION: <50ms for pattern matching
- REACTIVE INTERVENTION: When issues detected, trigger fixes
- FAIL-OPEN: Connection issues never block tool calls
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from enum import Enum

from .client import GatewayClient, GatewayConnectionState
from .validation import (
    GatewayDecision,
    PreExecutionRequest,
    PreExecutionResponse,
    TraceContext,
    ToolCallInfo,
    AgentContext,
    InterventionSignal,
)
from .fallback import FallbackMode, FallbackStrategy

if TYPE_CHECKING:
    from ..interceptor.protocols import (
        InterceptionContext,
        PreCallResult,
        PostCallResult,
    )

logger = logging.getLogger("aigie.gateway.middleware")


class ToolCallResultType(str, Enum):
    """Result types for tool call validation."""
    ALLOW = "allow"
    BLOCK = "block"
    MODIFY = "modify"
    RETRY = "retry"


@dataclass
class ToolCallResult:
    """Result of tool call validation."""
    result_type: ToolCallResultType
    original_args: Dict[str, Any]
    modified_args: Optional[Dict[str, Any]] = None
    reason: str = ""
    signals: List[Any] = field(default_factory=list)
    confidence: float = 1.0
    latency_ms: float = 0.0
    intervention: Optional[InterventionSignal] = None

    @property
    def should_proceed(self) -> bool:
        """Check if tool call should proceed."""
        return self.result_type in (ToolCallResultType.ALLOW, ToolCallResultType.MODIFY)

    @property
    def args(self) -> Dict[str, Any]:
        """Get the arguments to use (modified if applicable)."""
        return self.modified_args if self.modified_args else self.original_args


class ToolCallMiddleware:
    """
    Middleware for intercepting and validating tool calls.

    This middleware can be used:
    1. As a pre-call hook in InterceptorChain
    2. Directly wrapping tool execution
    3. With LangChain tool instrumentation

    Key Features:
    - Non-blocking parallel validation
    - Configurable handling modes
    - Intervention signal processing
    - Pattern learning integration
    """

    def __init__(
        self,
        gateway_client: GatewayClient,
        validation_timeout_ms: float = 100.0,
        block_on_high_risk: bool = False,  # False = observe mode (non-blocking)
        enable_modifications: bool = True,
        fallback_mode: FallbackMode = FallbackMode.ALLOW,
    ):
        """
        Initialize the middleware.

        Args:
            gateway_client: Gateway client for validation
            validation_timeout_ms: Timeout for validation requests
            block_on_high_risk: Whether to block high-risk calls (default: False for non-blocking)
            enable_modifications: Whether to apply argument modifications
            fallback_mode: Fallback mode when gateway unavailable
        """
        self._gateway = gateway_client
        self._validation_timeout_ms = validation_timeout_ms
        self._block_on_high_risk = block_on_high_risk
        self._enable_modifications = enable_modifications
        self._fallback = FallbackStrategy(mode=fallback_mode)

        # Track current context for building requests
        self._current_trace_id: Optional[str] = None
        self._current_span_id: Optional[str] = None
        self._iteration_count = 0
        self._recent_actions: List[Dict[str, Any]] = []
        self._total_tokens = 0

        # Intervention handling
        self._pending_interventions: Dict[str, InterventionSignal] = {}
        self._intervention_handlers: List[Callable[[InterventionSignal], Any]] = []

        # Statistics
        self._stats = {
            "tool_calls_validated": 0,
            "validations_blocked": 0,
            "validations_modified": 0,
            "interventions_applied": 0,
            "total_latency_ms": 0.0,
        }

    def set_trace_context(
        self,
        trace_id: str,
        span_id: Optional[str] = None
    ):
        """Set current trace context for validation requests."""
        self._current_trace_id = trace_id
        self._current_span_id = span_id

    def update_context(
        self,
        iteration_count: Optional[int] = None,
        total_tokens: Optional[int] = None,
        recent_action: Optional[Dict[str, Any]] = None
    ):
        """Update agent context for validation requests."""
        if iteration_count is not None:
            self._iteration_count = iteration_count
        if total_tokens is not None:
            self._total_tokens = total_tokens
        if recent_action is not None:
            self._recent_actions.append(recent_action)
            if len(self._recent_actions) > 10:
                self._recent_actions.pop(0)

    async def validate_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_type: Optional[str] = None,
    ) -> ToolCallResult:
        """
        Validate a tool call before execution.

        This method runs in parallel with execution by default
        (block_on_high_risk=False). It:
        1. Sends validation request to gateway
        2. Checks for pending interventions
        3. Returns result without blocking (unless high-risk detected)

        Args:
            tool_name: Name of the tool
            tool_args: Tool arguments
            tool_type: Type of tool (langchain, openai_function, etc.)

        Returns:
            ToolCallResult with validation outcome
        """
        start_time = time.perf_counter()
        self._stats["tool_calls_validated"] += 1

        # Build request
        request = self._build_request(tool_name, tool_args, tool_type)

        # Check for pending intervention for this trace
        intervention = self._check_pending_intervention()

        # Validate with gateway (or fallback)
        try:
            if self._gateway.is_connected:
                response = await self._gateway.validate(
                    request,
                    timeout_ms=self._validation_timeout_ms
                )
            else:
                response = self._fallback.get_fallback_response(
                    request,
                    reason="Gateway not connected"
                )
        except Exception as e:
            logger.warning(f"Validation error: {e}")
            response = self._fallback.get_fallback_response(
                request,
                reason=f"Validation error: {str(e)}"
            )

        latency_ms = (time.perf_counter() - start_time) * 1000
        self._stats["total_latency_ms"] += latency_ms

        # Determine result
        result = self._process_response(
            response,
            tool_name,
            tool_args,
            intervention,
            latency_ms
        )

        # Record recent action
        self.update_context(recent_action={
            "tool": tool_name,
            "decision": result.result_type.value,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return result

    def _build_request(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_type: Optional[str] = None
    ) -> PreExecutionRequest:
        """Build validation request from current context."""
        return PreExecutionRequest(
            trace_context=TraceContext(
                trace_id=self._current_trace_id or "unknown",
                span_id=self._current_span_id,
            ),
            tool_call=ToolCallInfo(
                name=tool_name,
                arguments=tool_args,
                tool_type=tool_type,
            ),
            context=AgentContext(
                recent_actions=self._recent_actions.copy(),
                iteration_count=self._iteration_count,
                total_tokens_used=self._total_tokens,
            ),
        )

    def _process_response(
        self,
        response: PreExecutionResponse,
        tool_name: str,
        tool_args: Dict[str, Any],
        intervention: Optional[InterventionSignal],
        latency_ms: float
    ) -> ToolCallResult:
        """Process validation response into ToolCallResult."""
        # Priority: intervention > gateway response

        # Check intervention first
        if intervention:
            self._stats["interventions_applied"] += 1
            return self._apply_intervention(intervention, tool_args, latency_ms)

        # Process gateway response
        if response.decision == GatewayDecision.BLOCK:
            self._stats["validations_blocked"] += 1

            if self._block_on_high_risk:
                return ToolCallResult(
                    result_type=ToolCallResultType.BLOCK,
                    original_args=tool_args,
                    reason=response.reason,
                    signals=response.signals,
                    confidence=response.confidence,
                    latency_ms=latency_ms,
                )
            else:
                # Observe mode: log but don't block
                logger.warning(
                    f"Tool call '{tool_name}' would be blocked: {response.reason} "
                    f"(observe mode - allowing)"
                )
                return ToolCallResult(
                    result_type=ToolCallResultType.ALLOW,
                    original_args=tool_args,
                    reason=f"Observed risk (not blocking): {response.reason}",
                    signals=response.signals,
                    confidence=response.confidence,
                    latency_ms=latency_ms,
                )

        elif response.decision == GatewayDecision.MODIFY:
            self._stats["validations_modified"] += 1

            if self._enable_modifications and response.modifications:
                modified_args = {**tool_args, **response.modifications}
                return ToolCallResult(
                    result_type=ToolCallResultType.MODIFY,
                    original_args=tool_args,
                    modified_args=modified_args,
                    reason=response.reason,
                    signals=response.signals,
                    confidence=response.confidence,
                    latency_ms=latency_ms,
                )

        elif response.decision == GatewayDecision.DELAY:
            # For now, treat delay as allow with logged warning
            if response.delay_ms:
                logger.info(f"Tool call delayed: {response.reason} (delay_ms={response.delay_ms})")

        # Default: allow
        return ToolCallResult(
            result_type=ToolCallResultType.ALLOW,
            original_args=tool_args,
            reason=response.reason,
            signals=response.signals,
            confidence=response.confidence,
            latency_ms=latency_ms,
        )

    def _apply_intervention(
        self,
        intervention: InterventionSignal,
        tool_args: Dict[str, Any],
        latency_ms: float
    ) -> ToolCallResult:
        """Apply an intervention signal to the tool call."""
        intervention_type = intervention.intervention_type

        if intervention_type == "break_loop":
            return ToolCallResult(
                result_type=ToolCallResultType.BLOCK,
                original_args=tool_args,
                reason=f"Loop break intervention: {intervention.reason}",
                confidence=intervention.confidence,
                latency_ms=latency_ms,
                intervention=intervention,
            )

        elif intervention_type == "retry_current_step":
            return ToolCallResult(
                result_type=ToolCallResultType.RETRY,
                original_args=tool_args,
                modified_args=intervention.payload.get("modified_args"),
                reason=f"Retry intervention: {intervention.reason}",
                confidence=intervention.confidence,
                latency_ms=latency_ms,
                intervention=intervention,
            )

        elif intervention_type == "inject_correction":
            # Apply correction to arguments if provided
            corrections = intervention.payload.get("corrections", {})
            if corrections:
                modified_args = {**tool_args, **corrections}
                return ToolCallResult(
                    result_type=ToolCallResultType.MODIFY,
                    original_args=tool_args,
                    modified_args=modified_args,
                    reason=f"Correction intervention: {intervention.reason}",
                    confidence=intervention.confidence,
                    latency_ms=latency_ms,
                    intervention=intervention,
                )

        # Default: allow with intervention noted
        return ToolCallResult(
            result_type=ToolCallResultType.ALLOW,
            original_args=tool_args,
            reason=f"Intervention noted: {intervention.reason}",
            confidence=intervention.confidence,
            latency_ms=latency_ms,
            intervention=intervention,
        )

    def _check_pending_intervention(self) -> Optional[InterventionSignal]:
        """Check for pending intervention for current trace."""
        if not self._current_trace_id:
            return None

        return self._pending_interventions.pop(self._current_trace_id, None)

    def add_pending_intervention(self, intervention: InterventionSignal):
        """Add an intervention signal to be applied on next tool call."""
        self._pending_interventions[intervention.trace_id] = intervention

    def on_intervention(self, callback: Callable[[InterventionSignal], Any]):
        """Register callback for intervention handling."""
        self._intervention_handlers.append(callback)

    async def handle_intervention(self, intervention: InterventionSignal):
        """Handle an intervention signal from the gateway."""
        # Store for next tool call
        self.add_pending_intervention(intervention)

        # Notify handlers
        for handler in self._intervention_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(intervention)
                else:
                    handler(intervention)
            except Exception as e:
                logger.error(f"Intervention handler error: {e}")

    # =========================================================================
    # InterceptorChain Integration
    # =========================================================================

    @property
    def name(self) -> str:
        """Hook name for InterceptorChain."""
        return "gateway_middleware"

    @property
    def priority(self) -> int:
        """Hook priority (lower = earlier). Run early to catch issues."""
        return 15  # High priority, before most other hooks

    async def __call__(self, ctx: "InterceptionContext") -> "PreCallResult":
        """
        Pre-call hook implementation for InterceptorChain.

        This allows the middleware to be used as a hook:
            interceptor_chain.add_pre_hook(middleware)

        Args:
            ctx: Interception context

        Returns:
            PreCallResult
        """
        from ..interceptor.protocols import PreCallResult, InterceptionDecision

        # Update context from InterceptionContext
        self.set_trace_context(
            trace_id=ctx.trace_id or "unknown",
            span_id=ctx.span_id
        )

        # For LLM calls (not tool calls), just allow
        # Tool calls are validated separately
        return PreCallResult.allow(
            hook_name=self.name,
            latency_ms=0.0
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get middleware statistics."""
        return {
            **self._stats,
            "avg_latency_ms": (
                self._stats["total_latency_ms"] / max(self._stats["tool_calls_validated"], 1)
            ),
            "pending_interventions": len(self._pending_interventions),
            "gateway_connected": self._gateway.is_connected,
            "gateway_stats": self._gateway.get_stats(),
        }


# =========================================================================
# Convenience Functions for Integration
# =========================================================================

def wrap_tool_with_gateway(
    tool_func: Callable,
    middleware: ToolCallMiddleware,
    tool_name: str,
    tool_type: str = "function"
) -> Callable:
    """
    Wrap a tool function with gateway validation.

    Usage:
        original_tool = my_tool_function
        wrapped_tool = wrap_tool_with_gateway(original_tool, middleware, "my_tool")

    Args:
        tool_func: Original tool function
        middleware: ToolCallMiddleware instance
        tool_name: Name of the tool
        tool_type: Type of tool

    Returns:
        Wrapped function with validation
    """
    import functools

    @functools.wraps(tool_func)
    async def async_wrapper(*args, **kwargs):
        # Validate
        result = await middleware.validate_tool_call(
            tool_name=tool_name,
            tool_args=kwargs,
            tool_type=tool_type
        )

        if not result.should_proceed:
            raise RuntimeError(f"Tool call blocked: {result.reason}")

        # Use potentially modified args
        return await tool_func(*args, **result.args)

    @functools.wraps(tool_func)
    def sync_wrapper(*args, **kwargs):
        # Run validation in event loop
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            middleware.validate_tool_call(
                tool_name=tool_name,
                tool_args=kwargs,
                tool_type=tool_type
            )
        )

        if not result.should_proceed:
            raise RuntimeError(f"Tool call blocked: {result.reason}")

        return tool_func(*args, **result.args)

    # Return appropriate wrapper based on original function
    if asyncio.iscoroutinefunction(tool_func):
        return async_wrapper
    return sync_wrapper
