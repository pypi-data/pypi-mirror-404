"""
Strands Agents hook handler for Aigie SDK.

Implements HookProvider to automatically trace Strands agent invocations,
tool calls, LLM calls, and multi-agent orchestrations.

Includes comprehensive error detection and drift monitoring.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ...buffer import EventType
from .config import StrandsConfig
from .cost_tracking import calculate_strands_cost
from .error_detection import ErrorDetector, DetectedError
from .drift_detection import DriftDetector

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Get current time in UTC with timezone info."""
    return datetime.now(timezone.utc)


def _utc_isoformat() -> str:
    """Get current UTC time as ISO format string."""
    return datetime.now(timezone.utc).isoformat()

if TYPE_CHECKING:
    try:
        from strands.hooks import (
            HookProvider,
            HookRegistry,
            BeforeInvocationEvent,
            AfterInvocationEvent,
            BeforeToolCallEvent,
            AfterToolCallEvent,
            BeforeModelCallEvent,
            AfterModelCallEvent,
            MessageAddedEvent,
            BeforeMultiAgentInvocationEvent,
            AfterMultiAgentInvocationEvent,
            BeforeNodeCallEvent,
            AfterNodeCallEvent,
        )
        from strands.agent.agent_result import AgentResult
        from strands.types.tools import ToolUse, ToolResult
    except ImportError:
        pass


class StrandsHandler:
    """
    Strands Agents handler for Aigie tracing.

    Implements HookProvider to automatically trace:
    - Agent invocations (BeforeInvocationEvent → AfterInvocationEvent)
    - Tool calls (BeforeToolCallEvent → AfterToolCallEvent)
    - LLM calls (BeforeModelCallEvent → AfterModelCallEvent)
    - Multi-agent orchestrations (BeforeMultiAgentInvocationEvent → AfterMultiAgentInvocationEvent)
    - Node executions (BeforeNodeCallEvent → AfterNodeCallEvent)

    Example:
        >>> from strands import Agent
        >>> from aigie.integrations.strands import StrandsHandler
        >>>
        >>> handler = StrandsHandler()
        >>> agent = Agent(tools=[...], hooks=[handler])
        >>> result = agent("What is the capital of France?")
    """

    def __init__(
        self,
        config: Optional[StrandsConfig] = None,
        trace_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize Strands handler.

        Args:
            config: Configuration for tracing behavior
            trace_name: Name for the trace (default: agent name)
            metadata: Additional metadata to attach
            tags: Tags to apply to trace and spans
            user_id: User ID for the trace
            session_id: Session ID for the trace
        """
        self.config = config or StrandsConfig.from_env()
        self.trace_name = trace_name
        self.metadata = metadata or {}
        self.tags = tags or []
        self.user_id = user_id
        self.session_id = session_id

        # State tracking
        self.trace_id: Optional[str] = None
        self.agent_span_id: Optional[str] = None
        self.tool_map: Dict[str, Dict[str, Any]] = {}  # tool_use_id -> {spanId, startTime}
        self.model_call_map: Dict[str, Dict[str, Any]] = {}  # model_span_id -> {startTime, ...}
        self.model_span_id: Optional[str] = None  # Keep for backward compat, points to latest
        self.model_start_time: Optional[datetime] = None  # Keep for backward compat
        self.multi_agent_map: Dict[str, Dict[str, Any]] = {}  # orchestrator_id -> {spanId, startTime}
        self.node_map: Dict[str, Dict[str, Any]] = {}  # node_id -> {spanId, startTime}

        # Current context for parent relationships
        self._current_parent_span_id: Optional[str] = None
        self._parent_span_stack: List[str] = []  # Stack for nested multi-agent/nodes
        self._aigie = None

        # Statistics
        self._total_tool_calls = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost = 0.0

        # Per-call token tracking - stores accumulated usage at start of each model call
        # This allows us to calculate delta (per-call) tokens
        self._model_call_start_tokens: Optional[Dict[str, int]] = None

        # Error tracking
        self._has_errors = False
        self._error_messages: List[str] = []

        # Error detection and monitoring
        self._error_detector = ErrorDetector()
        self._drift_detector = DriftDetector()
        self._detected_errors: List[DetectedError] = []
        self._invocation_start_time: Optional[datetime] = None

        # Depth tracking for flow view - maps span_id to depth
        self._span_depth_map: Dict[str, int] = {}

    def _get_depth_for_parent(self, parent_id: Optional[str]) -> int:
        """Calculate depth based on parent span's depth."""
        if not parent_id:
            return 0  # Root level
        parent_depth = self._span_depth_map.get(parent_id, 0)
        return parent_depth + 1

    def _register_span_depth(self, span_id: str, parent_id: Optional[str]) -> int:
        """Register a span's depth and return it."""
        depth = self._get_depth_for_parent(parent_id)
        self._span_depth_map[span_id] = depth
        return depth

    def _get_aigie(self):
        """Lazy load Aigie client."""
        if self._aigie is None:
            from ...client import get_aigie
            self._aigie = get_aigie()
        return self._aigie

    def register_hooks(self, registry: "HookRegistry") -> None:
        """
        Register hook callbacks with the Strands hook registry.

        This method is called by Strands when the handler is added to an agent.

        Args:
            registry: The hook registry to register callbacks with
        """
        if not self.config.enabled:
            return

        try:
            from strands.hooks import (
                BeforeInvocationEvent,
                AfterInvocationEvent,
                BeforeToolCallEvent,
                AfterToolCallEvent,
                BeforeModelCallEvent,
                AfterModelCallEvent,
                MessageAddedEvent,
                BeforeMultiAgentInvocationEvent,
                AfterMultiAgentInvocationEvent,
                BeforeNodeCallEvent,
                AfterNodeCallEvent,
            )
        except ImportError:
            logger.warning("[AIGIE] Strands hooks not available - cannot register callbacks")
            return

        # Core agent lifecycle
        if self.config.trace_agents:
            registry.add_callback(BeforeInvocationEvent, self._on_before_invocation)
            registry.add_callback(AfterInvocationEvent, self._on_after_invocation)
            registry.add_callback(MessageAddedEvent, self._on_message_added)

        # Tool execution
        if self.config.trace_tools:
            registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)
            registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)

        # Model invocation
        if self.config.trace_llm_calls:
            registry.add_callback(BeforeModelCallEvent, self._on_before_model_call)
            registry.add_callback(AfterModelCallEvent, self._on_after_model_call)

        # Multi-agent
        if self.config.trace_multi_agent:
            registry.add_callback(BeforeMultiAgentInvocationEvent, self._on_before_multi_agent)
            registry.add_callback(AfterMultiAgentInvocationEvent, self._on_after_multi_agent)
            registry.add_callback(BeforeNodeCallEvent, self._on_before_node_call)
            registry.add_callback(AfterNodeCallEvent, self._on_after_node_call)

        # BidiAgent streaming support (optional)
        if self.config.trace_streaming:
            self._register_streaming_hooks(registry)

    # Core agent lifecycle hooks

    async def _on_before_invocation(self, event: "BeforeInvocationEvent") -> None:
        """Handle BeforeInvocationEvent - create trace and agent span."""
        if not self.config.enabled or not self.config.trace_agents:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            # Check if we're already in a trace (from context or previous invocation)
            # This allows multiple agent invocations to share the same trace
            existing_trace_id = None
            
            # Check Aigie context for existing trace
            try:
                from ...auto_instrument.trace import get_current_trace
                current_trace = get_current_trace()
                if current_trace and hasattr(current_trace, 'id'):
                    existing_trace_id = current_trace.id
            except Exception:
                pass  # Context not available, continue
            
            # If we already have a trace_id (from previous invocation or context), reuse it
            if existing_trace_id:
                self.trace_id = existing_trace_id
                trace_already_exists = True
            elif self.trace_id:
                # Reuse existing trace_id from handler (for nested invocations)
                trace_already_exists = True
            else:
                # Generate new trace ID only if we don't have one
                self.trace_id = str(uuid.uuid4())
                trace_already_exists = False
            
            # Reset invocation-specific state (but keep trace_id)
            self._has_errors = False
            self._error_messages = []
            self._total_tool_calls = 0
            self._total_input_tokens = 0
            self._total_output_tokens = 0
            self._total_cost = 0.0
            self.agent_span_id = None
            self.model_span_id = None
            self.model_start_time = None
            self._model_call_start_tokens = None  # Reset per-call token tracking
            self.tool_map.clear()
            self.model_call_map.clear()  # Clear model call tracking map
            self.multi_agent_map.clear()
            self.node_map.clear()
            self._current_parent_span_id = None
            self._parent_span_stack.clear()

            # Determine trace name
            agent_name = getattr(event.agent, 'name', 'Strands Agent')
            trace_name = self.trace_name or agent_name

            # Only create trace if it doesn't already exist
            if not trace_already_exists:
                # Create trace
                trace_data = {
                    "id": self.trace_id,
                    "name": trace_name,
                    "metadata": {
                        "framework": "strands",
                        "agent_id": getattr(event.agent, 'agent_id', None),
                        "agent_name": agent_name,
                        **self.metadata,
                    },
                    "tags": self.tags,
                    "start_time": _utc_now().isoformat(),
                }

                if self.user_id:
                    trace_data["user_id"] = self.user_id
                if self.session_id:
                    trace_data["session_id"] = self.session_id

                # Create trace first
                await aigie._buffer.add(EventType.TRACE_CREATE, trace_data)
                
                # Set trace in context so other handlers can reuse it
                try:
                    from ...auto_instrument.trace import set_current_trace
                    # Create a simple trace context object with the trace_id
                    # This allows subsequent agent invocations to find and reuse the trace
                    class SimpleTraceContext:
                        def __init__(self, trace_id: str, trace_name: str):
                            self.id = trace_id
                            self.name = trace_name
                    set_current_trace(SimpleTraceContext(self.trace_id, trace_name))
                except Exception as e:
                    logger.debug(f"[AIGIE] Could not set trace in context: {e}")
                
                # Flush immediately to ensure trace is created before spans
                # This prevents orphan spans
                await aigie._buffer.flush()
            else:
                logger.debug(f"[AIGIE] Reusing existing trace: {self.trace_id}")

            # Create agent span (root span for this invocation - no parent)
            self.agent_span_id = str(uuid.uuid4())
            self._invocation_start_time = _utc_now()

            # Reset error/drift detection for this invocation
            self._error_detector = ErrorDetector()
            self._drift_detector = DriftDetector()
            self._detected_errors = []

            # Register agent span depth (root level = 0)
            agent_depth = self._register_span_depth(self.agent_span_id, None)

            # Capture system prompt for drift detection if available
            system_prompt = getattr(event.agent, 'system_prompt', None)
            if system_prompt:
                self._drift_detector.capture_system_prompt(str(system_prompt))

            agent_span_data = {
                "id": self.agent_span_id,
                "trace_id": self.trace_id,
                "parent_id": None,  # Root span under trace - use parent_id not parent_span_id
                "name": f"Agent: {agent_name}",
                "type": "agent",
                "start_time": self._invocation_start_time.isoformat(),
                "metadata": {
                    "agent_id": getattr(event.agent, 'agent_id', None),
                    "agent_name": agent_name,
                    "depth": agent_depth,
                },
                "tags": self.tags,
                "status": "running",
                "depth": agent_depth,  # For flow view ordering
            }

            if self.user_id:
                agent_span_data["user_id"] = self.user_id
            if self.session_id:
                agent_span_data["session_id"] = self.session_id

            # Capture input if enabled
            if self.config.capture_inputs and event.messages:
                # Truncate messages if needed
                messages_repr = str(event.messages)
                if len(messages_repr) > self.config.max_content_length:
                    messages_repr = messages_repr[:self.config.max_content_length] + "..."
                agent_span_data["input"] = messages_repr
                agent_span_data["metadata"]["input_messages"] = messages_repr

            await aigie._buffer.add(EventType.SPAN_CREATE, agent_span_data)
            self._current_parent_span_id = self.agent_span_id

            logger.debug(f"[AIGIE] Trace started: {trace_name} (id={self.trace_id})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_before_invocation: {e}")

    async def _on_after_invocation(self, event: "AfterInvocationEvent") -> None:
        """Handle AfterInvocationEvent - complete agent span and trace."""
        if not self.config.enabled or not self.config.trace_agents:
            return

        if not self.agent_span_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            # Determine if invocation succeeded or failed
            result: Optional["AgentResult"] = event.result
            has_error = result is None or self._has_errors or len(self._error_messages) > 0
            
            # Extract metrics from result
            if result and hasattr(result, 'metrics'):
                metrics = result.metrics
                if hasattr(metrics, 'accumulated_usage'):
                    usage = metrics.accumulated_usage
                    if usage:
                        # Usage is a TypedDict with keys: inputTokens, outputTokens, totalTokens
                        self._total_input_tokens = usage.get("inputTokens", 0) or 0
                        self._total_output_tokens = usage.get("outputTokens", 0) or 0

                        # Calculate cost - extract model_id
                        model_id = None
                        if hasattr(event.agent, 'model'):
                            model_id = self._extract_model_id(event.agent.model)

                        self._total_cost = calculate_strands_cost(
                            model_id=model_id,
                            input_tokens=self._total_input_tokens,
                            output_tokens=self._total_output_tokens,
                        )

            # Determine status
            status = "error" if has_error else "success"
            is_error = has_error
            error_message = None
            if self._error_messages:
                error_message = "; ".join(self._error_messages[:3])  # Limit to first 3 errors
            elif result is None:
                error_message = "Agent invocation returned no result"

            # Calculate duration
            agent_end_time = _utc_now()
            agent_duration_ms = 0
            if self._invocation_start_time:
                agent_duration_ms = (agent_end_time - self._invocation_start_time).total_seconds() * 1000

            # Update agent span
            update_data = {
                "id": self.agent_span_id,
                "trace_id": self.trace_id,
                "end_time": agent_end_time.isoformat(),
                "duration_ns": int(agent_duration_ms * 1_000_000),  # Consistent with LLM/tool spans
                "status": status,
                "is_error": is_error,
                "metadata": {
                    "total_tool_calls": self._total_tool_calls,
                    "total_input_tokens": self._total_input_tokens,
                    "total_output_tokens": self._total_output_tokens,
                    "total_tokens": self._total_input_tokens + self._total_output_tokens,
                    "total_cost": self._total_cost,
                    "duration_ms": agent_duration_ms,
                    "status": status,
                },
            }

            if error_message:
                update_data["error"] = error_message
                update_data["error_message"] = error_message
                update_data["metadata"]["error"] = error_message

            # Capture output if enabled
            if self.config.capture_outputs and result:
                output_repr = str(result)
                if len(output_repr) > self.config.max_content_length:
                    output_repr = output_repr[:self.config.max_content_length] + "..."
                update_data["output"] = output_repr
                update_data["metadata"]["result"] = output_repr

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            # Update trace with aggregated metrics
            # Note: We update the trace but don't set end_time if this is part of a larger workflow
            # The trace will be finalized when the entire workflow completes
            trace_output = {}
            if self.config.capture_outputs and result:
                output_repr = str(result)
                if len(output_repr) > self.config.max_content_length:
                    output_repr = output_repr[:self.config.max_content_length] + "..."
                trace_output["response"] = output_repr

            # Finalize drift detection and get all detected drifts
            end_time = _utc_now()
            duration_ms = 0
            if self._invocation_start_time:
                duration_ms = (end_time - self._invocation_start_time).total_seconds() * 1000
            total_tokens = self._total_input_tokens + self._total_output_tokens

            # Extract final output for drift detection
            final_output = None
            if self.config.capture_outputs and result:
                final_output = str(result)[:500]

            detected_drifts = self._drift_detector.finalize(
                total_duration_ms=duration_ms,
                total_tokens=total_tokens,
                total_cost=self._total_cost,
                final_output=final_output,
            )

            # Build monitoring data
            monitoring_data = {
                'drift_detection': {
                    'plan': self._drift_detector.plan.to_dict() if self._drift_detector.plan else None,
                    'execution': self._drift_detector.execution.to_dict() if self._drift_detector.execution else None,
                    'detected_drifts': [d.to_dict() for d in detected_drifts],
                    'drift_count': len(detected_drifts),
                },
                'error_detection': {
                    'stats': self._error_detector.stats.to_dict(),
                    'detected_errors': [e.to_dict() for e in self._detected_errors],
                    'error_count': len(self._detected_errors),
                },
            }

            # Log monitoring summary
            if detected_drifts:
                logger.info(f"[AIGIE] Drift detection summary: {len(detected_drifts)} drifts detected")
            if self._detected_errors:
                logger.info(f"[AIGIE] Error detection summary: {len(self._detected_errors)} errors detected")

            # Update trace with metrics from this invocation
            # Note: If multiple invocations share the same trace, each will update it
            # The backend should aggregate or the last update will be the final state
            trace_output["monitoring"] = {
                'drift_count': len(detected_drifts),
                'error_count': len(self._detected_errors),
                'plan_captured': self._drift_detector._plan_captured,
            }

            trace_update = {
                "id": self.trace_id,
                "status": status,  # Status from this invocation
                "end_time": end_time.isoformat(),  # Update end_time on each invocation
                "output": trace_output,
                # Token/cost fields for backend aggregation display
                "total_tokens": self._total_input_tokens + self._total_output_tokens,
                "prompt_tokens": self._total_input_tokens,
                "completion_tokens": self._total_output_tokens,
                "total_cost": self._total_cost,
                "metadata": {
                    "total_tool_calls": self._total_tool_calls,
                    "total_input_tokens": self._total_input_tokens,
                    "total_output_tokens": self._total_output_tokens,
                    "total_tokens": self._total_input_tokens + self._total_output_tokens,
                    "total_cost": self._total_cost,
                    "last_agent": getattr(event.agent, 'name', 'Strands Agent'),
                    "monitoring": monitoring_data,
                },
            }

            if error_message:
                trace_update["error"] = error_message
                trace_update["error_message"] = error_message

            await aigie._buffer.add(EventType.TRACE_UPDATE, trace_update)

            # Clean up any pending spans (tools, models, nodes, multi-agent)
            await self._complete_pending_spans()

            logger.debug(f"[AIGIE] Trace completed: {self.trace_id} (status={status})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_after_invocation: {e}")
            # Still try to complete trace with error status
            try:
                if self.agent_span_id and self.trace_id:
                    error_update = {
                        "id": self.agent_span_id,
                        "trace_id": self.trace_id,
                        "end_time": _utc_now().isoformat(),
                        "status": "error",
                        "error": str(e),
                        "error_message": str(e),
                    }
                    await aigie._buffer.add(EventType.SPAN_UPDATE, error_update)
                    
                    trace_error = {
                        "id": self.trace_id,
                        "status": "error",
                        "end_time": _utc_now().isoformat(),
                        "error": str(e),
                        "error_message": str(e),
                    }
                    await aigie._buffer.add(EventType.TRACE_UPDATE, trace_error)
            except Exception:
                pass  # Best effort

    async def _on_message_added(self, event: "MessageAddedEvent") -> None:
        """Handle MessageAddedEvent - track message additions."""
        if not self.config.enabled or not self.config.capture_messages:
            return

        # Messages are tracked as part of the agent span
        # This hook can be used for fine-grained message tracking if needed
        pass

    # Tool execution hooks

    async def _on_before_tool_call(self, event: "BeforeToolCallEvent") -> None:
        """Handle BeforeToolCallEvent - create tool span."""
        if not self.config.enabled or not self.config.trace_tools:
            return

        if not self._current_parent_span_id or not self.trace_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            tool_use: "ToolUse" = event.tool_use
            tool_use_id = tool_use.get('toolUseId', str(uuid.uuid4()))
            tool_name = tool_use.get('name', 'unknown_tool')

            span_id = str(uuid.uuid4())
            start_time = _utc_now()

            # Calculate depth for flow view ordering
            tool_depth = self._register_span_depth(span_id, self._current_parent_span_id)

            self.tool_map[tool_use_id] = {
                'spanId': span_id,
                'startTime': start_time,
                'toolName': tool_name,
                'depth': tool_depth,
                'tool_input': tool_use.get('input', {}),
            }

            span_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "parent_id": self._current_parent_span_id,  # Use parent_id not parent_span_id
                "name": f"Tool: {tool_name}",
                "type": "tool",
                "start_time": start_time.isoformat(),
                "metadata": {
                    "tool_name": tool_name,
                    "tool_use_id": tool_use_id,
                    "depth": tool_depth,
                },
                "tags": self.tags,
                "status": "running",
                "depth": tool_depth,  # For flow view ordering
            }

            if self.user_id:
                span_data["user_id"] = self.user_id
            if self.session_id:
                span_data["session_id"] = self.session_id

            # Capture tool input if enabled
            if self.config.capture_inputs:
                tool_input = tool_use.get('input', {})
                input_repr = str(tool_input)
                if len(input_repr) > self.config.max_content_length:
                    input_repr = input_repr[:self.config.max_content_length] + "..."
                span_data["input"] = input_repr
                span_data["metadata"]["tool_input"] = input_repr

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)
            self._total_tool_calls += 1

            logger.debug(f"[AIGIE] Tool span created: {tool_name} (id={span_id})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_before_tool_call: {e}")

    async def _on_after_tool_call(self, event: "AfterToolCallEvent") -> None:
        """Handle AfterToolCallEvent - complete tool span."""
        if not self.config.enabled or not self.config.trace_tools:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        # Extract tool_use_id before try block so it's accessible in finally
        tool_use: "ToolUse" = event.tool_use
        tool_use_id = tool_use.get('toolUseId')

        # If no toolUseId, try to find matching tool by name from recent entries
        if not tool_use_id:
            tool_name = tool_use.get('name', 'unknown_tool')
            # Look for most recent tool with matching name
            for tid, tdata in reversed(list(self.tool_map.items())):
                if tdata.get('toolName') == tool_name:
                    tool_use_id = tid
                    break
            if not tool_use_id:
                logger.warning(f"[AIGIE] No toolUseId found for tool {tool_name}, skipping duration tracking")
                return

        try:
            tool_data = self.tool_map.get(tool_use_id)
            if not tool_data:
                return

            span_id = tool_data['spanId']
            tool_name = tool_data['toolName']

            # Determine status
            status = "success"
            is_error = False
            if event.exception:
                status = "error"
                is_error = True
                self._has_errors = True
                error_msg = str(event.exception)
                if error_msg and error_msg not in self._error_messages:
                    self._error_messages.append(error_msg)
            elif event.cancel_message:
                status = "cancelled"

            # Calculate duration
            start_time = tool_data['startTime']
            end_time = _utc_now()
            duration = (end_time - start_time).total_seconds()
            duration_ms = duration * 1000

            # Error detection - check tool result for errors
            result_str = str(event.result) if event.result else ""
            detected_error = self._error_detector.detect_from_tool_result(
                tool_name=tool_name,
                tool_use_id=tool_use_id,
                result=result_str,
                is_error_flag=is_error,
                duration_ms=duration_ms,
            )
            if detected_error:
                self._detected_errors.append(detected_error)
                logger.debug(f"[AIGIE] Error detected in tool {tool_name}: {detected_error.error_type.value}")

            # Record for drift detection
            self._drift_detector.record_tool_use(
                tool_name=tool_name,
                tool_input=tool_data.get('tool_input', {}),
                duration_ms=duration_ms,
                is_error=is_error,
            )

            update_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": status,
                "is_error": is_error,
                "metadata": {
                    "tool_name": tool_name,
                    "duration_ms": duration_ms,
                    "status": status,
                },
            }

            # Capture tool output if enabled
            if self.config.capture_outputs:
                if event.result:
                    result_repr = str(event.result)
                    if len(result_repr) > self.config.max_tool_result_length:
                        result_repr = result_repr[:self.config.max_tool_result_length] + "..."
                    update_data["output"] = result_repr
                    update_data["metadata"]["tool_result"] = result_repr

                if event.exception:
                    error_str = str(event.exception)
                    update_data["error"] = error_str
                    update_data["error_message"] = error_str
                    update_data["metadata"]["error"] = error_str

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            logger.debug(f"[AIGIE] Tool span completed: {tool_name} (id={span_id}, status={status}, duration_ms={duration_ms:.2f})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_after_tool_call: {e}")
        finally:
            # Always cleanup map entry to prevent memory leaks
            if tool_use_id in self.tool_map:
                del self.tool_map[tool_use_id]

    # Model invocation hooks

    async def _on_before_model_call(self, event: "BeforeModelCallEvent") -> None:
        """Handle BeforeModelCallEvent - create LLM span."""
        if not self.config.enabled or not self.config.trace_llm_calls:
            return

        if not self._current_parent_span_id or not self.trace_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            span_id = str(uuid.uuid4())
            start_time = _utc_now()

            # Capture accumulated usage at the start of this model call
            # This allows us to calculate per-call (delta) tokens later
            start_tokens = self._get_current_accumulated_usage(event.agent)

            # Get model info - handle different model types
            model_id = None
            if hasattr(event.agent, 'model'):
                model_id = self._extract_model_id(event.agent.model)

            # Calculate depth for flow view ordering
            llm_depth = self._register_span_depth(span_id, self._current_parent_span_id)

            # Store in map for concurrent call support
            self.model_call_map[span_id] = {
                'startTime': start_time,
                'startTokens': start_tokens,
                'modelId': model_id,
                'depth': llm_depth,
            }

            # Keep backward compat references (points to latest)
            self.model_span_id = span_id
            self.model_start_time = start_time
            self._model_call_start_tokens = start_tokens

            span_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "parent_id": self._current_parent_span_id,  # Use parent_id not parent_span_id
                "name": f"LLM: {model_id or 'unknown'}",
                "type": "llm",
                "start_time": start_time.isoformat(),
                "metadata": {
                    "model_id": model_id,
                    "depth": llm_depth,
                },
                "tags": self.tags,
                "status": "running",
                "depth": llm_depth,  # For flow view ordering
            }

            if self.user_id:
                span_data["user_id"] = self.user_id
            if self.session_id:
                span_data["session_id"] = self.session_id

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

            logger.debug(f"[AIGIE] LLM span created: {model_id} (id={span_id})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_before_model_call: {e}")

    async def _on_after_model_call(self, event: "AfterModelCallEvent") -> None:
        """Handle AfterModelCallEvent - complete LLM span."""
        if not self.config.enabled or not self.config.trace_llm_calls:
            return

        if not self.model_span_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        # Get the span_id to complete - use the current model_span_id
        span_id = self.model_span_id

        try:
            # Try to get data from map first (more reliable for concurrent calls)
            model_data = self.model_call_map.get(span_id, {})
            start_time = model_data.get('startTime') or self.model_start_time
            start_tokens = model_data.get('startTokens') or self._model_call_start_tokens

            # Determine status
            status = "success"
            is_error = False
            if event.exception:
                status = "error"
                is_error = True
                self._has_errors = True
                error_msg = str(event.exception)
                if error_msg and error_msg not in self._error_messages:
                    self._error_messages.append(error_msg)

            # Extract model info for cost calculation
            model_id = model_data.get('modelId')
            if not model_id and hasattr(event.agent, 'model'):
                model_id = self._extract_model_id(event.agent.model)

            # Calculate per-call (delta) tokens for this specific model call
            # This is more accurate than accumulated totals when there are multiple LLM calls
            per_call_usage = self._calculate_per_call_tokens(
                agent=event.agent,
                start_tokens=start_tokens,
            )
            model_input_tokens = per_call_usage.get("inputTokens", 0)
            model_output_tokens = per_call_usage.get("outputTokens", 0)

            logger.debug(
                f"[AIGIE] Per-call tokens: input={model_input_tokens}, output={model_output_tokens} "
                f"(start_tokens={start_tokens})"
            )

            # Also get accumulated totals for trace-level aggregation
            accumulated_usage = self._get_current_accumulated_usage(event.agent)
            accumulated_input = accumulated_usage.get("inputTokens", 0)
            accumulated_output = accumulated_usage.get("outputTokens", 0)

            # Calculate cost for this model call (per-call tokens)
            model_cost = calculate_strands_cost(
                model_id=model_id,
                input_tokens=model_input_tokens,
                output_tokens=model_output_tokens,
            )

            # Calculate duration
            end_time = _utc_now()
            duration = 0.0
            if start_time:
                duration = (end_time - start_time).total_seconds()
            else:
                logger.warning(f"[AIGIE] No start_time found for model span {span_id}, duration will be 0")

            # Calculate duration in ms
            duration_ms = duration * 1000

            update_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": status,
                "is_error": is_error,
                "metadata": {
                    "model_id": model_id,
                    # Per-call (delta) tokens for this specific model invocation
                    "input_tokens": model_input_tokens,
                    "output_tokens": model_output_tokens,
                    "total_tokens": model_input_tokens + model_output_tokens,
                    "cost": model_cost,
                    # Accumulated tokens (running total across all model calls)
                    "accumulated_input_tokens": accumulated_input,
                    "accumulated_output_tokens": accumulated_output,
                    "accumulated_total_tokens": accumulated_input + accumulated_output,
                    "duration_ms": duration_ms,
                    "status": status,
                },
                # Token fields for backend aggregation (per-call values)
                "prompt_tokens": model_input_tokens,
                "completion_tokens": model_output_tokens,
                "total_tokens": model_input_tokens + model_output_tokens,
            }

            if event.stop_response:
                if self.config.capture_outputs:
                    message_repr = str(event.stop_response.message)
                    if len(message_repr) > self.config.max_content_length:
                        message_repr = message_repr[:self.config.max_content_length] + "..."
                    update_data["output"] = message_repr
                    update_data["metadata"]["stop_reason"] = str(event.stop_response.stop_reason)

            if event.exception:
                error_str = str(event.exception)
                update_data["error"] = error_str
                update_data["error_message"] = error_str
                update_data["metadata"]["error"] = error_str

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            logger.debug(f"[AIGIE] LLM span completed: {span_id} (status={status}, duration_ms={duration_ms:.2f})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_after_model_call: {e}")
        finally:
            # Always clean up model span state
            if span_id in self.model_call_map:
                del self.model_call_map[span_id]
            self.model_span_id = None
            self.model_start_time = None
            self._model_call_start_tokens = None

    # Multi-agent hooks

    async def _on_before_multi_agent(self, event: "BeforeMultiAgentInvocationEvent") -> None:
        """Handle BeforeMultiAgentInvocationEvent - create orchestrator span."""
        if not self.config.enabled or not self.config.trace_multi_agent:
            return

        if not self.trace_id:
            # If no trace_id, create one (for nested multi-agent scenarios)
            self.trace_id = str(uuid.uuid4())

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            orchestrator = event.source
            orchestrator_id = id(orchestrator)
            orchestrator_type = type(orchestrator).__name__

            span_id = str(uuid.uuid4())
            start_time = _utc_now()

            # Calculate depth for flow view ordering
            multi_agent_depth = self._register_span_depth(span_id, self._current_parent_span_id)

            self.multi_agent_map[orchestrator_id] = {
                'spanId': span_id,
                'startTime': start_time,
                'type': orchestrator_type,
                'depth': multi_agent_depth,
            }

            span_data = {
                "id": span_id,
                "trace_id": self.trace_id or str(uuid.uuid4()),
                "parent_id": self._current_parent_span_id,  # Use parent_id not parent_span_id
                "name": f"Multi-Agent: {orchestrator_type}",
                "type": "multi_agent",
                "start_time": start_time.isoformat(),
                "metadata": {
                    "orchestrator_type": orchestrator_type,
                    "orchestrator_id": str(orchestrator_id),
                    "depth": multi_agent_depth,
                },
                "depth": multi_agent_depth,  # For flow view ordering
                "tags": self.tags,
                "status": "running",
            }

            if self.user_id:
                span_data["user_id"] = self.user_id
            if self.session_id:
                span_data["session_id"] = self.session_id

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)
            
            # Store previous parent and push to stack
            if self._current_parent_span_id:
                self._parent_span_stack.append(self._current_parent_span_id)
            self._current_parent_span_id = span_id

            logger.debug(f"[AIGIE] Multi-agent orchestrator span created: {orchestrator_type} (id={span_id})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_before_multi_agent: {e}")

    async def _on_after_multi_agent(self, event: "AfterMultiAgentInvocationEvent") -> None:
        """Handle AfterMultiAgentInvocationEvent - complete orchestrator span."""
        if not self.config.enabled or not self.config.trace_multi_agent:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        # Extract orchestrator_id before try block so it's accessible in finally
        orchestrator = event.source
        orchestrator_id = id(orchestrator)

        try:
            orchestrator_data = self.multi_agent_map.get(orchestrator_id)
            if not orchestrator_data:
                return

            span_id = orchestrator_data['spanId']
            orchestrator_type = orchestrator_data['type']
            start_time = orchestrator_data['startTime']
            end_time = _utc_now()
            duration = (end_time - start_time).total_seconds()

            # Check for errors - AfterMultiAgentInvocationEvent might have error info
            status = "success"
            is_error = False
            error_message = None
            # Note: AfterMultiAgentInvocationEvent doesn't have exception field in Strands
            # but we track errors from child nodes/agents
            if self._has_errors:
                status = "error"
                is_error = True
                if self._error_messages:
                    error_message = "; ".join(self._error_messages[:2])

            # Calculate duration in ms
            duration_ms = duration * 1000

            update_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": status,
                "is_error": is_error,
                "metadata": {
                    "orchestrator_type": orchestrator_type,
                    "duration_ms": duration_ms,
                    "status": status,
                },
            }

            if error_message:
                update_data["error"] = error_message
                update_data["error_message"] = error_message
                update_data["metadata"]["error"] = error_message

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            # Restore previous parent from stack
            if self._parent_span_stack:
                self._current_parent_span_id = self._parent_span_stack.pop()
            else:
                # Fallback to agent span
                self._current_parent_span_id = self.agent_span_id

            logger.debug(f"[AIGIE] Multi-agent orchestrator span completed: {orchestrator_type} (id={span_id}, status={status})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_after_multi_agent: {e}")
        finally:
            # Always cleanup map entry to prevent memory leaks
            if orchestrator_id in self.multi_agent_map:
                del self.multi_agent_map[orchestrator_id]

    async def _on_before_node_call(self, event: "BeforeNodeCallEvent") -> None:
        """Handle BeforeNodeCallEvent - create node span."""
        if not self.config.enabled or not self.config.trace_multi_agent:
            return

        if not self._current_parent_span_id or not self.trace_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            node_id = event.node_id
            orchestrator = event.source
            orchestrator_type = type(orchestrator).__name__

            span_id = str(uuid.uuid4())
            start_time = _utc_now()

            # Calculate depth for flow view ordering
            node_depth = self._register_span_depth(span_id, self._current_parent_span_id)

            self.node_map[node_id] = {
                'spanId': span_id,
                'startTime': start_time,
                'nodeId': node_id,
                'depth': node_depth,
            }

            span_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "parent_id": self._current_parent_span_id,  # Use parent_id not parent_span_id
                "name": f"Node: {node_id}",
                "type": "node",
                "start_time": start_time.isoformat(),
                "metadata": {
                    "node_id": node_id,
                    "orchestrator_type": orchestrator_type,
                    "depth": node_depth,
                },
                "tags": self.tags,
                "status": "running",
                "depth": node_depth,  # For flow view ordering
            }

            if self.user_id:
                span_data["user_id"] = self.user_id
            if self.session_id:
                span_data["session_id"] = self.session_id

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

            logger.debug(f"[AIGIE] Node span created: {node_id} (id={span_id})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_before_node_call: {e}")

    async def _on_after_node_call(self, event: "AfterNodeCallEvent") -> None:
        """Handle AfterNodeCallEvent - complete node span."""
        if not self.config.enabled or not self.config.trace_multi_agent:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        # Extract node_id before try block so it's accessible in finally
        node_id = event.node_id

        try:
            node_data = self.node_map.get(node_id)
            if not node_data:
                return

            span_id = node_data['spanId']
            start_time = node_data['startTime']
            end_time = _utc_now()
            duration = (end_time - start_time).total_seconds()

            # Check for errors - AfterNodeCallEvent might have error info
            status = "success"
            is_error = False
            error_message = None
            # Note: AfterNodeCallEvent doesn't have exception field in Strands
            # but we track errors from child agents
            if self._has_errors:
                status = "error"
                is_error = True
                if self._error_messages:
                    error_message = "; ".join(self._error_messages[:2])

            # Calculate duration in ms
            duration_ms = duration * 1000

            update_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": status,
                "is_error": is_error,
                "metadata": {
                    "node_id": node_id,
                    "duration_ms": duration_ms,
                    "status": status,
                },
            }

            if error_message:
                update_data["error"] = error_message
                update_data["error_message"] = error_message
                update_data["metadata"]["error"] = error_message

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            logger.debug(f"[AIGIE] Node span completed: {node_id} (id={span_id}, status={status})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_after_node_call: {e}")
        finally:
            # Always cleanup map entry to prevent memory leaks
            if node_id in self.node_map:
                del self.node_map[node_id]

    # Helper methods

    def _get_current_accumulated_usage(self, agent: Any) -> Dict[str, int]:
        """
        Get the current accumulated token usage from the agent's event loop metrics.

        This is used to capture the "before" state so we can calculate per-call
        tokens by computing the delta after the model call completes.

        Args:
            agent: The Strands agent instance

        Returns:
            Dictionary with inputTokens and outputTokens (defaults to 0 if not available)
        """
        result = {"inputTokens": 0, "outputTokens": 0}
        try:
            if hasattr(agent, 'event_loop_metrics'):
                metrics = agent.event_loop_metrics
                if hasattr(metrics, 'accumulated_usage') and metrics.accumulated_usage:
                    usage = metrics.accumulated_usage
                    result["inputTokens"] = usage.get("inputTokens", 0) or 0
                    result["outputTokens"] = usage.get("outputTokens", 0) or 0
        except Exception:
            pass  # Return defaults if any error
        return result

    def _get_latest_cycle_usage(self, agent: Any) -> Optional[Dict[str, int]]:
        """
        Try to extract usage from the most recent event loop cycle.

        Strands tracks usage at the cycle level in:
        agent.event_loop_metrics.agent_invocations[-1].cycles[-1].usage

        This provides per-cycle (approximately per-model-call) token usage.

        Args:
            agent: The Strands agent instance

        Returns:
            Dictionary with per-cycle tokens, or None if not available
        """
        try:
            if not hasattr(agent, 'event_loop_metrics'):
                return None

            metrics = agent.event_loop_metrics
            if not hasattr(metrics, 'agent_invocations') or not metrics.agent_invocations:
                return None

            current_invocation = metrics.agent_invocations[-1]
            if not hasattr(current_invocation, 'cycles') or not current_invocation.cycles:
                return None

            current_cycle = current_invocation.cycles[-1]
            if not hasattr(current_cycle, 'usage') or not current_cycle.usage:
                return None

            usage = current_cycle.usage
            return {
                "inputTokens": usage.get("inputTokens", 0) or 0,
                "outputTokens": usage.get("outputTokens", 0) or 0,
                "totalTokens": usage.get("totalTokens", 0) or 0,
            }
        except Exception:
            return None

    def _calculate_per_call_tokens(
        self,
        agent: Any,
        start_tokens: Optional[Dict[str, int]]
    ) -> Dict[str, int]:
        """
        Calculate per-call (delta) tokens by comparing current accumulated usage
        with the usage captured at the start of the model call.

        This approach handles the case where AfterModelCallEvent doesn't include
        per-call usage directly - we compute it from the accumulated totals.

        Falls back to cycle-level usage if delta calculation isn't possible.

        Args:
            agent: The Strands agent instance
            start_tokens: The accumulated usage captured at the start of the model call

        Returns:
            Dictionary with per-call inputTokens and outputTokens
        """
        current_usage = self._get_current_accumulated_usage(agent)

        # First, try the delta approach (most accurate for per-call)
        if start_tokens:
            # Calculate delta (per-call tokens)
            per_call_input = max(0, current_usage["inputTokens"] - start_tokens["inputTokens"])
            per_call_output = max(0, current_usage["outputTokens"] - start_tokens["outputTokens"])

            # If we got valid delta tokens, return them
            if per_call_input > 0 or per_call_output > 0:
                return {
                    "inputTokens": per_call_input,
                    "outputTokens": per_call_output,
                    "totalTokens": per_call_input + per_call_output,
                }

        # Fallback: Try to get cycle-level usage
        cycle_usage = self._get_latest_cycle_usage(agent)
        if cycle_usage:
            return cycle_usage

        # Last resort: Use current accumulated (may be inaccurate for per-call)
        return {
            "inputTokens": current_usage["inputTokens"],
            "outputTokens": current_usage["outputTokens"],
            "totalTokens": current_usage["inputTokens"] + current_usage["outputTokens"],
        }

    def _extract_model_id(self, model: Any) -> Optional[str]:
        """Extract model ID from various model types."""
        if not model:
            return None
        
        # Try different ways to get model_id
        if hasattr(model, 'model_id'):
            return model.model_id
        elif hasattr(model, '_model_id'):
            return model._model_id
        elif hasattr(model, 'config'):
            if isinstance(model.config, dict):
                return model.config.get('model_id')
            elif hasattr(model.config, 'model_id'):
                return model.config.model_id
        # For GeminiModel and similar, check client_args
        elif hasattr(model, 'client_args') and isinstance(model.client_args, dict):
            # Fallback to model type name
            return type(model).__name__.replace('Model', '').lower()
        
        return None

    async def _complete_pending_spans(self) -> None:
        """Complete any pending spans that weren't explicitly closed."""
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return

        end_time = _utc_now()

        # Complete pending tool spans
        pending_tool_ids = list(self.tool_map.keys())
        for tool_use_id in pending_tool_ids:
            tool_data = self.tool_map.get(tool_use_id)
            if not tool_data:
                continue

            duration = (end_time - tool_data['startTime']).total_seconds()
            update_data = {
                "id": tool_data['spanId'],
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": "success",  # Assume success if not explicitly failed
                "metadata": {
                    "tool_name": tool_data['toolName'],
                    "pending_cleanup": True,  # Mark as cleanup
                },
            }
            try:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            except Exception:
                pass  # Best effort
            del self.tool_map[tool_use_id]

        # Complete pending model spans from map
        pending_model_span_ids = list(self.model_call_map.keys())
        for span_id in pending_model_span_ids:
            model_data = self.model_call_map.get(span_id)
            if not model_data:
                continue

            start_time = model_data.get('startTime')
            if start_time:
                duration = (end_time - start_time).total_seconds()
            else:
                duration = 0.0

            update_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": "success",  # Assume success if not explicitly failed
                "metadata": {
                    "model_id": model_data.get('modelId'),
                    "pending_cleanup": True,  # Mark as cleanup
                },
            }
            try:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            except Exception:
                pass  # Best effort
            del self.model_call_map[span_id]

        # Clear backward compat model state
        self.model_span_id = None
        self.model_start_time = None

        # Complete pending multi-agent spans
        pending_orchestrator_ids = list(self.multi_agent_map.keys())
        for orchestrator_id in pending_orchestrator_ids:
            orchestrator_data = self.multi_agent_map.get(orchestrator_id)
            if not orchestrator_data:
                continue

            duration = (end_time - orchestrator_data['startTime']).total_seconds()
            update_data = {
                "id": orchestrator_data['spanId'],
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": "success",  # Assume success if not explicitly failed
                "metadata": {
                    "orchestrator_type": orchestrator_data['type'],
                    "pending_cleanup": True,  # Mark as cleanup
                },
            }
            try:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            except Exception:
                pass  # Best effort
            del self.multi_agent_map[orchestrator_id]

        # Complete pending node spans
        pending_node_ids = list(self.node_map.keys())
        for node_id in pending_node_ids:
            node_data = self.node_map.get(node_id)
            if not node_data:
                continue

            duration = (end_time - node_data['startTime']).total_seconds()
            update_data = {
                "id": node_data['spanId'],
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": "success",  # Assume success if not explicitly failed
                "metadata": {
                    "node_id": node_id,
                    "pending_cleanup": True,  # Mark as cleanup
                },
            }
            try:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            except Exception:
                pass  # Best effort
            del self.node_map[node_id]

    # ========================================================================
    # BidiAgent Streaming Hooks
    # ========================================================================

    def _register_streaming_hooks(self, registry: "HookRegistry") -> None:
        """
        Register BidiAgent streaming hooks with the registry.

        BidiAgent hooks enable real-time tracing of bidirectional streaming
        conversations, including partial results and interruptions.

        Args:
            registry: The hook registry to register callbacks with
        """
        try:
            # Try to import BidiAgent-specific events if available
            # These events may not be available in all Strands versions
            from strands.hooks import (
                BidiBeforeInvocationEvent,
                BidiAfterInvocationEvent,
                BidiBeforeToolCallEvent,
                BidiAfterToolCallEvent,
                BidiInterruptionEvent,
            )

            registry.add_callback(BidiBeforeInvocationEvent, self._on_bidi_before_invocation)
            registry.add_callback(BidiAfterInvocationEvent, self._on_bidi_after_invocation)
            registry.add_callback(BidiBeforeToolCallEvent, self._on_bidi_before_tool_call)
            registry.add_callback(BidiAfterToolCallEvent, self._on_bidi_after_tool_call)
            registry.add_callback(BidiInterruptionEvent, self._on_bidi_interruption)

            logger.debug("[AIGIE] BidiAgent streaming hooks registered")

        except ImportError:
            logger.debug("[AIGIE] BidiAgent events not available - streaming hooks disabled")
        except Exception as e:
            logger.warning(f"[AIGIE] Failed to register BidiAgent hooks: {e}")

    async def _on_bidi_before_invocation(self, event: Any) -> None:
        """Handle BidiBeforeInvocationEvent - start streaming invocation span."""
        if not self.config.enabled or not self.config.trace_streaming:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            # Create streaming invocation span
            span_id = str(uuid.uuid4())
            start_time = _utc_now()

            # Use agent span as parent if available
            parent_id = self.agent_span_id or self._current_parent_span_id

            span_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "parent_id": parent_id,
                "name": "BidiAgent Streaming",
                "type": "llm",
                "start_time": start_time.isoformat(),
                "metadata": {
                    "streaming": True,
                    "bidi_agent": True,
                },
                "status": "running",
            }

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

            # Store for later completion
            if not hasattr(self, '_bidi_span_id'):
                self._bidi_span_id = None
            if not hasattr(self, '_bidi_start_time'):
                self._bidi_start_time = None

            self._bidi_span_id = span_id
            self._bidi_start_time = start_time

            logger.debug(f"[AIGIE] BidiAgent streaming started (span_id={span_id[:8]})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_bidi_before_invocation: {e}")

    async def _on_bidi_after_invocation(self, event: Any) -> None:
        """Handle BidiAfterInvocationEvent - complete streaming invocation span."""
        if not self.config.enabled or not self.config.trace_streaming:
            return

        if not hasattr(self, '_bidi_span_id') or not self._bidi_span_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            end_time = _utc_now()
            duration = 0.0
            if hasattr(self, '_bidi_start_time') and self._bidi_start_time:
                duration = (end_time - self._bidi_start_time).total_seconds()

            # Extract streaming result info
            output = None
            status = "success"
            if hasattr(event, 'result'):
                if hasattr(event.result, 'text'):
                    output = str(event.result.text)[:self.config.max_content_length]
                elif event.result is None:
                    status = "cancelled"

            update_data = {
                "id": self._bidi_span_id,
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": status,
                "output": output,
            }

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            logger.debug(f"[AIGIE] BidiAgent streaming completed (span_id={self._bidi_span_id[:8]})")

            self._bidi_span_id = None
            self._bidi_start_time = None

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_bidi_after_invocation: {e}")

    async def _on_bidi_before_tool_call(self, event: Any) -> None:
        """Handle BidiBeforeToolCallEvent - track streaming tool call."""
        if not self.config.enabled or not self.config.trace_streaming:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            # Extract tool info from event
            tool_name = getattr(event, 'tool_name', 'unknown_tool')
            tool_use_id = getattr(event, 'tool_use_id', str(uuid.uuid4()))

            span_id = str(uuid.uuid4())
            start_time = _utc_now()

            # Use bidi span as parent if available
            parent_id = getattr(self, '_bidi_span_id', None) or self.agent_span_id

            span_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "parent_id": parent_id,
                "name": f"Tool: {tool_name}",
                "type": "tool",
                "start_time": start_time.isoformat(),
                "metadata": {
                    "tool_name": tool_name,
                    "tool_use_id": tool_use_id,
                    "streaming": True,
                },
                "status": "running",
            }

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

            # Store in tool_map for completion
            self.tool_map[tool_use_id] = {
                'spanId': span_id,
                'startTime': start_time,
                'toolName': tool_name,
                'streaming': True,
            }

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_bidi_before_tool_call: {e}")

    async def _on_bidi_after_tool_call(self, event: Any) -> None:
        """Handle BidiAfterToolCallEvent - complete streaming tool call span."""
        if not self.config.enabled or not self.config.trace_streaming:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            tool_use_id = getattr(event, 'tool_use_id', None)
            if not tool_use_id or tool_use_id not in self.tool_map:
                return

            tool_data = self.tool_map[tool_use_id]
            end_time = _utc_now()
            duration = (end_time - tool_data['startTime']).total_seconds()

            # Extract result
            output = None
            status = "success"
            if hasattr(event, 'result'):
                output = str(event.result)[:self.config.max_tool_result_length]
            if hasattr(event, 'error') and event.error:
                status = "error"
                output = str(event.error)

            update_data = {
                "id": tool_data['spanId'],
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": status,
                "output": output,
            }

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            del self.tool_map[tool_use_id]

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_bidi_after_tool_call: {e}")

    async def _on_bidi_interruption(self, event: Any) -> None:
        """Handle BidiInterruptionEvent - track streaming interruptions."""
        if not self.config.enabled or not self.config.trace_streaming:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            # Create interruption span
            span_id = str(uuid.uuid4())
            timestamp = _utc_now()

            parent_id = getattr(self, '_bidi_span_id', None) or self.agent_span_id

            # Extract interruption reason
            reason = getattr(event, 'reason', 'unknown')
            source = getattr(event, 'source', 'user')

            span_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "parent_id": parent_id,
                "name": f"Interruption: {reason}",
                "type": "event",
                "start_time": timestamp.isoformat(),
                "end_time": timestamp.isoformat(),
                "duration_ns": 0,
                "metadata": {
                    "interruption": True,
                    "reason": reason,
                    "source": source,
                },
                "status": "cancelled",
            }

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

            logger.debug(f"[AIGIE] BidiAgent interruption recorded (reason={reason})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_bidi_interruption: {e}")
