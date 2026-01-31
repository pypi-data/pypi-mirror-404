"""
Intervention Handlers - Pluggable Handlers for Gateway Interventions

This module provides handlers that execute actual interventions when the gateway
detects issues. These handlers bridge the gap between detection and action.

Handler Types:
- BlockHandler: Stops execution by raising exceptions
- ModifyHandler: Transforms tool arguments before execution
- DelayHandler: Adds exponential backoff between calls
- EscalateHandler: Notifies external systems (webhooks, logging)

Architecture:
The gateway detects issues and sends intervention signals. These handlers
receive those signals and take actual action to stop/modify agent behavior.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, Awaitable

from .validation import InterventionSignal, GatewayDecision

logger = logging.getLogger("aigie.gateway.handlers")


class InterventionHandlerError(Exception):
    """Base exception for intervention handler errors."""

    def __init__(
        self,
        message: str,
        intervention: Optional[InterventionSignal] = None,
        handler_name: Optional[str] = None
    ):
        super().__init__(message)
        self.intervention = intervention
        self.handler_name = handler_name


class ExecutionBlockedError(InterventionHandlerError):
    """Raised when execution is blocked by an intervention."""
    pass


class InterventionType(str, Enum):
    """Types of interventions that can be applied."""
    BREAK_LOOP = "break_loop"
    RETRY_CURRENT_STEP = "retry_current_step"
    INJECT_CORRECTION = "inject_correction"
    REDIRECT = "redirect"
    ESCALATE = "escalate"
    DELAY = "delay"
    ROLLBACK = "rollback"


@dataclass
class HandlerResult:
    """Result of an intervention handler execution."""
    handled: bool
    action_taken: str
    modified_args: Optional[Dict[str, Any]] = None
    delay_ms: Optional[int] = None
    should_proceed: bool = True
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def blocked(cls, reason: str, intervention: Optional[InterventionSignal] = None) -> "HandlerResult":
        """Factory for blocked result."""
        return cls(
            handled=True,
            action_taken=f"Blocked: {reason}",
            should_proceed=False,
            metadata={"intervention_id": intervention.id if intervention else None}
        )

    @classmethod
    def modified(cls, reason: str, modified_args: Dict[str, Any]) -> "HandlerResult":
        """Factory for modified result."""
        return cls(
            handled=True,
            action_taken=f"Modified: {reason}",
            modified_args=modified_args,
            should_proceed=True,
        )

    @classmethod
    def delayed(cls, delay_ms: int, reason: str) -> "HandlerResult":
        """Factory for delayed result."""
        return cls(
            handled=True,
            action_taken=f"Delayed {delay_ms}ms: {reason}",
            delay_ms=delay_ms,
            should_proceed=True,
        )

    @classmethod
    def passed(cls) -> "HandlerResult":
        """Factory for no-op (pass-through) result."""
        return cls(
            handled=False,
            action_taken="Passed",
            should_proceed=True,
        )


class InterventionHandler(ABC):
    """
    Base class for intervention handlers.

    Handlers are called in priority order when interventions are triggered.
    Each handler can:
    - Block execution entirely
    - Modify arguments
    - Add delays
    - Escalate to external systems
    - Pass through to next handler
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Handler name for logging and identification."""
        pass

    @property
    def priority(self) -> int:
        """Handler priority (lower = earlier). Default: 50."""
        return 50

    @property
    def intervention_types(self) -> List[InterventionType]:
        """Intervention types this handler can process. Empty = all types."""
        return []

    @abstractmethod
    async def handle(
        self,
        intervention: InterventionSignal,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> HandlerResult:
        """
        Handle an intervention signal.

        Args:
            intervention: The intervention signal from gateway
            tool_name: Name of the tool being called
            tool_args: Current tool arguments

        Returns:
            HandlerResult indicating what action was taken
        """
        pass

    def can_handle(self, intervention: InterventionSignal) -> bool:
        """Check if this handler can process the intervention type."""
        if not self.intervention_types:
            return True
        try:
            intervention_type = InterventionType(intervention.intervention_type)
            return intervention_type in self.intervention_types
        except ValueError:
            return False


class BlockHandler(InterventionHandler):
    """
    Handler that blocks execution by raising an exception.

    This is the most aggressive intervention - it completely stops
    the agent from proceeding with the current action.

    Use Cases:
    - Breaking infinite loops
    - Preventing dangerous operations
    - Enforcing rate limits
    """

    def __init__(
        self,
        raise_exception: bool = True,
        exception_class: type = ExecutionBlockedError,
        log_blocks: bool = True,
        on_block: Optional[Callable[[InterventionSignal], Awaitable[None]]] = None,
    ):
        """
        Initialize BlockHandler.

        Args:
            raise_exception: Whether to raise exception on block
            exception_class: Exception class to raise
            log_blocks: Whether to log blocked calls
            on_block: Optional async callback when block occurs
        """
        self._raise_exception = raise_exception
        self._exception_class = exception_class
        self._log_blocks = log_blocks
        self._on_block = on_block
        self._block_count = 0

    @property
    def name(self) -> str:
        return "block_handler"

    @property
    def priority(self) -> int:
        return 10  # High priority - run early

    @property
    def intervention_types(self) -> List[InterventionType]:
        return [InterventionType.BREAK_LOOP]

    async def handle(
        self,
        intervention: InterventionSignal,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> HandlerResult:
        """Block the tool call."""
        self._block_count += 1

        if self._log_blocks:
            logger.warning(
                f"Blocking tool call '{tool_name}': {intervention.reason} "
                f"(intervention_id={intervention.id})"
            )

        # Call notification callback
        if self._on_block:
            try:
                await self._on_block(intervention)
            except Exception as e:
                logger.error(f"Block callback error: {e}")

        if self._raise_exception:
            raise self._exception_class(
                message=f"Tool call '{tool_name}' blocked: {intervention.reason}",
                intervention=intervention,
                handler_name=self.name
            )

        return HandlerResult.blocked(intervention.reason, intervention)

    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "name": self.name,
            "block_count": self._block_count,
        }


class ModifyHandler(InterventionHandler):
    """
    Handler that modifies tool arguments before execution.

    This allows corrections to be applied without blocking the agent,
    steering it toward better behavior.

    Use Cases:
    - Fixing incorrect parameters
    - Adding missing context
    - Sanitizing inputs
    """

    def __init__(
        self,
        allow_partial_modifications: bool = True,
        validate_modifications: bool = True,
        on_modify: Optional[Callable[[str, Dict, Dict], Awaitable[None]]] = None,
    ):
        """
        Initialize ModifyHandler.

        Args:
            allow_partial_modifications: Allow modifying subset of args
            validate_modifications: Validate modification types match original
            on_modify: Callback(tool_name, original_args, modified_args)
        """
        self._allow_partial = allow_partial_modifications
        self._validate = validate_modifications
        self._on_modify = on_modify
        self._modification_count = 0

    @property
    def name(self) -> str:
        return "modify_handler"

    @property
    def priority(self) -> int:
        return 20  # After block handler

    @property
    def intervention_types(self) -> List[InterventionType]:
        return [
            InterventionType.INJECT_CORRECTION,
            InterventionType.RETRY_CURRENT_STEP,
        ]

    async def handle(
        self,
        intervention: InterventionSignal,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> HandlerResult:
        """Apply modifications to tool arguments."""
        # Get modifications from intervention payload
        modifications = intervention.payload.get("corrections", {})
        if not modifications:
            modifications = intervention.payload.get("modified_args", {})

        if not modifications:
            logger.debug(f"No modifications in intervention for '{tool_name}'")
            return HandlerResult.passed()

        # Apply modifications
        modified_args = {**tool_args}

        for key, value in modifications.items():
            if key in modified_args or self._allow_partial:
                # Validate type if enabled
                if self._validate and key in tool_args:
                    original_type = type(tool_args[key])
                    if not isinstance(value, original_type) and value is not None:
                        logger.warning(
                            f"Type mismatch for '{key}': expected {original_type}, got {type(value)}"
                        )
                        continue

                modified_args[key] = value

        self._modification_count += 1

        logger.info(
            f"Modified tool call '{tool_name}': {list(modifications.keys())} "
            f"(intervention_id={intervention.id})"
        )

        # Call notification callback
        if self._on_modify:
            try:
                await self._on_modify(tool_name, tool_args, modified_args)
            except Exception as e:
                logger.error(f"Modify callback error: {e}")

        return HandlerResult.modified(
            reason=intervention.reason,
            modified_args=modified_args
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "name": self.name,
            "modification_count": self._modification_count,
        }


class DelayHandler(InterventionHandler):
    """
    Handler that adds delays between tool calls.

    Uses exponential backoff to slow down rapid/looping calls
    without completely blocking execution.

    Use Cases:
    - Rate limiting
    - Breaking fast loops
    - Allowing time for external systems
    """

    def __init__(
        self,
        base_delay_ms: int = 100,
        max_delay_ms: int = 10000,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        on_delay: Optional[Callable[[int], Awaitable[None]]] = None,
    ):
        """
        Initialize DelayHandler.

        Args:
            base_delay_ms: Starting delay in milliseconds
            max_delay_ms: Maximum delay cap
            backoff_factor: Multiplier for exponential backoff
            jitter: Add randomness to prevent thundering herd
            on_delay: Callback when delay is applied
        """
        self._base_delay = base_delay_ms
        self._max_delay = max_delay_ms
        self._backoff_factor = backoff_factor
        self._jitter = jitter
        self._on_delay = on_delay

        # Track delays per trace for backoff
        self._delay_counts: Dict[str, int] = {}
        self._total_delay_ms = 0

    @property
    def name(self) -> str:
        return "delay_handler"

    @property
    def priority(self) -> int:
        return 30

    @property
    def intervention_types(self) -> List[InterventionType]:
        return [InterventionType.DELAY]

    async def handle(
        self,
        intervention: InterventionSignal,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> HandlerResult:
        """Apply delay before allowing execution."""
        trace_id = intervention.trace_id

        # Calculate delay with exponential backoff
        delay_count = self._delay_counts.get(trace_id, 0)
        delay_ms = min(
            self._base_delay * (self._backoff_factor ** delay_count),
            self._max_delay
        )

        # Add jitter
        if self._jitter:
            import random
            jitter_factor = 0.5 + random.random()  # 0.5 to 1.5
            delay_ms = int(delay_ms * jitter_factor)

        delay_ms = int(delay_ms)

        logger.info(
            f"Delaying tool call '{tool_name}' by {delay_ms}ms "
            f"(attempt {delay_count + 1})"
        )

        # Apply delay
        await asyncio.sleep(delay_ms / 1000.0)

        # Update tracking
        self._delay_counts[trace_id] = delay_count + 1
        self._total_delay_ms += delay_ms

        # Cleanup old entries
        if len(self._delay_counts) > 1000:
            oldest = list(self._delay_counts.keys())[:500]
            for key in oldest:
                del self._delay_counts[key]

        # Call notification callback
        if self._on_delay:
            try:
                await self._on_delay(delay_ms)
            except Exception as e:
                logger.error(f"Delay callback error: {e}")

        return HandlerResult.delayed(delay_ms, intervention.reason)

    def reset_backoff(self, trace_id: str):
        """Reset backoff counter for a trace."""
        self._delay_counts.pop(trace_id, None)

    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "name": self.name,
            "total_delay_ms": self._total_delay_ms,
            "active_backoffs": len(self._delay_counts),
        }


class EscalateHandler(InterventionHandler):
    """
    Handler that escalates interventions to external systems.

    This doesn't block or modify execution, but notifies external
    systems (logging, webhooks, alerts) about the intervention.

    Use Cases:
    - Logging critical issues
    - Sending alerts to monitoring systems
    - Notifying human operators
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        log_level: int = logging.WARNING,
        include_tool_args: bool = False,
        on_escalate: Optional[Callable[[InterventionSignal, str], Awaitable[None]]] = None,
    ):
        """
        Initialize EscalateHandler.

        Args:
            webhook_url: Optional webhook URL for notifications
            log_level: Logging level for escalations
            include_tool_args: Include tool args in escalation (may contain sensitive data)
            on_escalate: Callback for custom escalation logic
        """
        self._webhook_url = webhook_url
        self._log_level = log_level
        self._include_tool_args = include_tool_args
        self._on_escalate = on_escalate
        self._escalation_count = 0

    @property
    def name(self) -> str:
        return "escalate_handler"

    @property
    def priority(self) -> int:
        return 100  # Run last, as side effect

    @property
    def intervention_types(self) -> List[InterventionType]:
        return [InterventionType.ESCALATE]

    async def handle(
        self,
        intervention: InterventionSignal,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> HandlerResult:
        """Escalate the intervention."""
        self._escalation_count += 1

        # Build escalation message
        message = {
            "intervention_id": intervention.id,
            "trace_id": intervention.trace_id,
            "span_id": intervention.span_id,
            "intervention_type": intervention.intervention_type,
            "reason": intervention.reason,
            "confidence": intervention.confidence,
            "tool_name": tool_name,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self._include_tool_args:
            message["tool_args"] = tool_args

        # Log
        logger.log(
            self._log_level,
            f"Escalation: {intervention.reason} (tool={tool_name}, trace={intervention.trace_id})"
        )

        # Send to webhook
        if self._webhook_url:
            await self._send_webhook(message)

        # Call custom escalation callback
        if self._on_escalate:
            try:
                await self._on_escalate(intervention, tool_name)
            except Exception as e:
                logger.error(f"Escalation callback error: {e}")

        # Always pass through - escalation is a side effect
        return HandlerResult.passed()

    async def _send_webhook(self, message: Dict[str, Any]):
        """Send message to webhook."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._webhook_url,
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status >= 400:
                        logger.warning(f"Webhook returned {response.status}")
        except ImportError:
            logger.debug("aiohttp not installed, skipping webhook")
        except Exception as e:
            logger.error(f"Webhook error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            "name": self.name,
            "escalation_count": self._escalation_count,
            "webhook_configured": self._webhook_url is not None,
        }


class HandlerChain:
    """
    Chain of intervention handlers executed in priority order.

    Handlers are executed from lowest to highest priority until
    one returns a result that stops propagation (handled=True and should_proceed=False).
    """

    def __init__(self, handlers: Optional[List[InterventionHandler]] = None):
        """
        Initialize handler chain.

        Args:
            handlers: Optional list of handlers (will be sorted by priority)
        """
        self._handlers: List[InterventionHandler] = []
        if handlers:
            for handler in handlers:
                self.add_handler(handler)

    def add_handler(self, handler: InterventionHandler):
        """Add a handler to the chain."""
        self._handlers.append(handler)
        self._handlers.sort(key=lambda h: h.priority)

    def remove_handler(self, name: str) -> bool:
        """Remove a handler by name."""
        original_count = len(self._handlers)
        self._handlers = [h for h in self._handlers if h.name != name]
        return len(self._handlers) < original_count

    async def handle(
        self,
        intervention: InterventionSignal,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> HandlerResult:
        """
        Process an intervention through the handler chain.

        Args:
            intervention: The intervention signal
            tool_name: Name of the tool being called
            tool_args: Current tool arguments

        Returns:
            Final HandlerResult from the chain
        """
        current_args = tool_args.copy()
        final_result = HandlerResult.passed()

        for handler in self._handlers:
            if not handler.can_handle(intervention):
                continue

            try:
                result = await handler.handle(intervention, tool_name, current_args)

                # If handler took action
                if result.handled:
                    final_result = result

                    # Update args if modified
                    if result.modified_args:
                        current_args = result.modified_args

                    # Stop if blocked
                    if not result.should_proceed:
                        break

            except InterventionHandlerError:
                # Re-raise intervention errors
                raise
            except Exception as e:
                logger.error(f"Handler '{handler.name}' error: {e}")
                # Continue to next handler on non-intervention errors

        # Update final result with accumulated modifications
        if current_args != tool_args and final_result.should_proceed:
            final_result.modified_args = current_args

        return final_result

    def get_stats(self) -> Dict[str, Any]:
        """Get chain statistics."""
        return {
            "handler_count": len(self._handlers),
            "handlers": [h.get_stats() for h in self._handlers],
        }

    @classmethod
    def default(cls) -> "HandlerChain":
        """Create a default handler chain with standard handlers."""
        return cls([
            BlockHandler(raise_exception=True),
            ModifyHandler(allow_partial_modifications=True),
            DelayHandler(base_delay_ms=100, max_delay_ms=5000),
            EscalateHandler(log_level=logging.WARNING),
        ])
