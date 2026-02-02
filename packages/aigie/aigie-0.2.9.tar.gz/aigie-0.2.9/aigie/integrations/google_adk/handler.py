"""
Google ADK handler for Aigie SDK.

Provides manual tracing support for Google ADK agents, capturing
agent invocations, LLM calls, tool executions, and events.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ...buffer import EventType
from .config import GoogleADKConfig
from .cost_tracking import calculate_google_adk_cost
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
    from .session import GoogleADKSessionContext


class GoogleADKHandler:
    """
    Google ADK handler for Aigie tracing.

    Provides manual tracing methods for Google ADK agent workflows:
    - Runner invocations (run lifecycle)
    - Agent executions
    - LLM/model calls with token tracking
    - Tool executions

    Example:
        >>> from google.adk import Runner, LlmAgent
        >>> from aigie.integrations.google_adk import GoogleADKHandler
        >>>
        >>> handler = GoogleADKHandler(trace_name="my-agent")
        >>>
        >>> # Manual usage in custom callbacks
        >>> await handler.handle_run_start(invocation_context)
        >>> await handler.handle_agent_start(agent, callback_context)
        >>> await handler.handle_llm_start(callback_context, llm_request)
        >>> # ... agent executes
        >>> await handler.handle_llm_end(callback_context, llm_response)
        >>> await handler.handle_agent_end(agent, callback_context)
        >>> await handler.handle_run_end(invocation_context)
    """

    def __init__(
        self,
        config: Optional[GoogleADKConfig] = None,
        trace_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        session_context: Optional["GoogleADKSessionContext"] = None,
    ):
        """
        Initialize Google ADK handler.

        Args:
            config: Configuration for tracing behavior
            trace_name: Name for the trace (default: agent name)
            metadata: Additional metadata to attach
            tags: Tags to apply to trace and spans
            user_id: User ID for the trace
            session_id: Session ID for the trace
            session_context: Optional session context for trace sharing
        """
        self.config = config or GoogleADKConfig.from_env()
        self.trace_name = trace_name
        self.metadata = metadata or {}
        self.tags = tags or []
        self.user_id = user_id
        self.session_id = session_id

        # Session context for trace sharing
        self._session_context = session_context

        # State tracking
        self.trace_id: Optional[str] = session_context.trace_id if session_context else None
        self.run_span_id: Optional[str] = None
        self.agent_span_id: Optional[str] = None
        self.llm_span_id: Optional[str] = None
        self.tool_map: Dict[str, Dict[str, Any]] = {}  # function_call_id -> {spanId, startTime}
        self.agent_map: Dict[str, Dict[str, Any]] = {}  # agent_name -> {spanId, startTime}

        # Current context for parent relationships
        self._current_parent_span_id: Optional[str] = None
        self._parent_span_stack: List[str] = []
        self._aigie = None

        # Depth tracking for flow view
        self._span_depth_map: Dict[str, int] = {}

        # Statistics
        self._total_model_calls = 0
        self._total_tool_calls = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost = 0.0

        # Error tracking
        self._has_errors = False
        self._error_messages: List[str] = []

        # Error detection and monitoring
        self._error_detector = ErrorDetector()
        self._detected_errors: List[DetectedError] = []
        self._run_start_time: Optional[datetime] = None

    def _get_aigie(self):
        """Lazy load Aigie client."""
        if self._aigie is None:
            from ...client import get_aigie
            self._aigie = get_aigie()
        return self._aigie

    def _get_depth_for_parent(self, parent_id: Optional[str]) -> int:
        """Calculate depth based on parent span's depth."""
        if not parent_id:
            return 0
        parent_depth = self._span_depth_map.get(parent_id, 0)
        return parent_depth + 1

    def _register_span_depth(self, span_id: str, parent_id: Optional[str]) -> int:
        """Register a span's depth and return it."""
        depth = self._get_depth_for_parent(parent_id)
        self._span_depth_map[span_id] = depth
        return depth

    def _get_current_parent(self) -> Optional[str]:
        """Get current parent span ID for nesting."""
        if self._session_context:
            ctx_parent = self._session_context.get_current_parent()
            if ctx_parent:
                return ctx_parent
        return self._current_parent_span_id or self.agent_span_id or self.run_span_id

    def _set_current_parent(self, span_id: Optional[str]) -> None:
        """Set current parent span ID."""
        self._current_parent_span_id = span_id
        if self._session_context:
            self._session_context.set_current_parent(span_id)

    # ========================================================================
    # Run Lifecycle Methods
    # ========================================================================

    async def handle_run_start(
        self,
        invocation_context: Any,
        user_message: Optional[str] = None,
    ) -> str:
        """
        Called when a Runner.run_async() starts.

        Args:
            invocation_context: The InvocationContext from ADK
            user_message: Optional user message content

        Returns:
            The trace ID
        """
        if not self.config.enabled:
            return ""

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return ""

        try:
            # Record start time
            self._run_start_time = _utc_now()

            # Reset state
            self._has_errors = False
            self._error_messages = []
            self._total_model_calls = 0
            self._total_tool_calls = 0
            self._total_input_tokens = 0
            self._total_output_tokens = 0
            self._total_cost = 0.0
            self.tool_map.clear()
            self.agent_map.clear()
            self._detected_errors = []
            self._error_detector = ErrorDetector()

            # Get or create trace ID
            if not self.trace_id:
                if self._session_context:
                    self.trace_id = self._session_context.trace_id
                else:
                    self.trace_id = str(uuid.uuid4())

            # Extract info from invocation context
            invocation_id = getattr(invocation_context, 'invocation_id', str(uuid.uuid4()))
            session = getattr(invocation_context, 'session', None)
            agent = getattr(invocation_context, 'agent', None)

            agent_name = getattr(agent, 'name', 'ADK Agent') if agent else 'ADK Agent'
            trace_name = self.trace_name or agent_name

            session_user_id = getattr(session, 'user_id', None) if session else None
            session_id = getattr(session, 'id', None) if session else None

            # Build metadata
            trace_metadata = {
                **self.metadata,
                'framework': 'google_adk',
                'invocation_id': invocation_id,
                'agent_name': agent_name,
            }

            # Only create trace if not already created
            should_create_trace = True
            if self._session_context and self._session_context.trace_created:
                should_create_trace = False

            if should_create_trace:
                trace_data = {
                    'id': self.trace_id,
                    'name': trace_name,
                    'type': 'agent',
                    'status': 'pending',
                    'tags': [*self.tags, 'google_adk'],
                    'metadata': trace_metadata,
                    'start_time': self._run_start_time.isoformat(),
                    'created_at': self._run_start_time.isoformat(),
                }

                if self.user_id or session_user_id:
                    trace_data['user_id'] = self.user_id or session_user_id
                if self.session_id or session_id:
                    trace_data['session_id'] = self.session_id or session_id

                if user_message and self.config.capture_inputs:
                    trace_data['input'] = {
                        'message': user_message[:self.config.max_content_length],
                    }

                await aigie._buffer.add(EventType.TRACE_CREATE, trace_data)

                if self._session_context:
                    self._session_context.mark_trace_created()

                # Flush to ensure trace is created before spans
                await aigie._buffer.flush()

            # Create run span
            self.run_span_id = str(uuid.uuid4())
            run_depth = self._register_span_depth(self.run_span_id, None)

            run_span_data = {
                'id': self.run_span_id,
                'trace_id': self.trace_id,
                'parent_id': None,
                'name': f'Run: {agent_name}',
                'type': 'agent',
                'start_time': self._run_start_time.isoformat(),
                'metadata': {
                    'invocation_id': invocation_id,
                    'agent_name': agent_name,
                    'depth': run_depth,
                },
                'tags': self.tags,
                'status': 'running',
                'depth': run_depth,
            }

            if user_message and self.config.capture_inputs:
                run_span_data['input'] = user_message[:self.config.max_content_length]

            await aigie._buffer.add(EventType.SPAN_CREATE, run_span_data)
            self._set_current_parent(self.run_span_id)

            logger.debug(f"[AIGIE] Run started: {trace_name} (trace_id={self.trace_id})")
            return self.trace_id

        except Exception as e:
            logger.warning(f"[AIGIE] Error in handle_run_start: {e}")
            return ""

    async def handle_run_end(
        self,
        invocation_context: Any,
        error: Optional[Exception] = None,
    ) -> None:
        """
        Called when a Runner.run_async() completes.

        Args:
            invocation_context: The InvocationContext from ADK
            error: Optional exception if the run failed
        """
        if not self.config.enabled or not self.run_span_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            end_time = _utc_now()
            has_error = error is not None or self._has_errors
            status = 'error' if has_error else 'success'

            # Calculate duration
            duration_ms = 0.0
            if self._run_start_time:
                duration_ms = (end_time - self._run_start_time).total_seconds() * 1000

            # Build error message
            error_message = None
            if error:
                error_message = str(error)[:500]
                # Detect error type
                detected_error = self._error_detector.detect_from_exception(
                    error, "run", {"invocation_id": getattr(invocation_context, 'invocation_id', None)}
                )
                if detected_error:
                    self._detected_errors.append(detected_error)
            elif self._error_messages:
                error_message = "; ".join(self._error_messages[:3])

            # Update run span
            run_update = {
                'id': self.run_span_id,
                'trace_id': self.trace_id,
                'end_time': end_time.isoformat(),
                'duration_ns': int(duration_ms * 1_000_000),
                'status': status,
                'is_error': has_error,
                'metadata': {
                    'total_model_calls': self._total_model_calls,
                    'total_tool_calls': self._total_tool_calls,
                    'total_input_tokens': self._total_input_tokens,
                    'total_output_tokens': self._total_output_tokens,
                    'total_tokens': self._total_input_tokens + self._total_output_tokens,
                    'total_cost': self._total_cost,
                    'duration_ms': duration_ms,
                    'status': status,
                },
                'prompt_tokens': self._total_input_tokens,
                'completion_tokens': self._total_output_tokens,
                'total_tokens': self._total_input_tokens + self._total_output_tokens,
                'total_cost': self._total_cost,
            }

            if error_message:
                run_update['error'] = error_message
                run_update['error_message'] = error_message

            await aigie._buffer.add(EventType.SPAN_UPDATE, run_update)

            # Update trace
            trace_update = {
                'id': self.trace_id,
                'status': status,
                'end_time': end_time.isoformat(),
                'total_tokens': self._total_input_tokens + self._total_output_tokens,
                'prompt_tokens': self._total_input_tokens,
                'completion_tokens': self._total_output_tokens,
                'total_cost': self._total_cost,
                'metadata': {
                    'total_model_calls': self._total_model_calls,
                    'total_tool_calls': self._total_tool_calls,
                    'error_count': len(self._detected_errors),
                },
            }

            if error_message:
                trace_update['error'] = error_message
                trace_update['error_message'] = error_message

            await aigie._buffer.add(EventType.TRACE_UPDATE, trace_update)

            # Complete any pending spans
            await self._complete_pending_spans(end_time)

            logger.debug(f"[AIGIE] Run completed: {self.trace_id} (status={status})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in handle_run_end: {e}")

    # ========================================================================
    # Agent Lifecycle Methods
    # ========================================================================

    async def handle_agent_start(
        self,
        agent: Any,
        callback_context: Any,
    ) -> str:
        """
        Called when an agent starts execution.

        Args:
            agent: The agent instance
            callback_context: The CallbackContext from ADK

        Returns:
            The agent span ID
        """
        if not self.config.enabled or not self.config.trace_agents:
            return ""

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return ""

        try:
            agent_name = getattr(agent, 'name', 'Agent')
            span_id = str(uuid.uuid4())
            start_time = _utc_now()

            parent_id = self._get_current_parent()
            agent_depth = self._register_span_depth(span_id, parent_id)

            # Store in agent map
            self.agent_map[agent_name] = {
                'spanId': span_id,
                'startTime': start_time,
                'agentName': agent_name,
                'depth': agent_depth,
            }

            span_data = {
                'id': span_id,
                'trace_id': self.trace_id,
                'parent_id': parent_id,
                'name': f'Agent: {agent_name}',
                'type': 'agent',
                'start_time': start_time.isoformat(),
                'metadata': {
                    'agent_name': agent_name,
                    'depth': agent_depth,
                },
                'tags': self.tags,
                'status': 'running',
                'depth': agent_depth,
            }

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

            self.agent_span_id = span_id
            self._set_current_parent(span_id)

            # Push to parent stack for nested agents
            self._parent_span_stack.append(parent_id or "")

            logger.debug(f"[AIGIE] Agent started: {agent_name} (span_id={span_id})")
            return span_id

        except Exception as e:
            logger.warning(f"[AIGIE] Error in handle_agent_start: {e}")
            return ""

    async def handle_agent_end(
        self,
        agent: Any,
        callback_context: Any,
        error: Optional[Exception] = None,
    ) -> None:
        """
        Called when an agent completes execution.

        Args:
            agent: The agent instance
            callback_context: The CallbackContext from ADK
            error: Optional exception if the agent failed
        """
        if not self.config.enabled or not self.config.trace_agents:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            agent_name = getattr(agent, 'name', 'Agent')
            agent_data = self.agent_map.get(agent_name)

            if not agent_data:
                return

            end_time = _utc_now()
            duration = (end_time - agent_data['startTime']).total_seconds()
            duration_ms = duration * 1000

            has_error = error is not None
            status = 'error' if has_error else 'success'

            update_data = {
                'id': agent_data['spanId'],
                'trace_id': self.trace_id,
                'end_time': end_time.isoformat(),
                'duration_ns': int(duration * 1_000_000_000),
                'status': status,
                'is_error': has_error,
                'metadata': {
                    'agent_name': agent_name,
                    'duration_ms': duration_ms,
                    'status': status,
                },
            }

            if error:
                error_str = str(error)[:500]
                update_data['error'] = error_str
                update_data['error_message'] = error_str
                self._has_errors = True
                if error_str not in self._error_messages:
                    self._error_messages.append(error_str)

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            # Restore parent from stack
            if self._parent_span_stack:
                prev_parent = self._parent_span_stack.pop()
                self._set_current_parent(prev_parent if prev_parent else self.run_span_id)
            else:
                self._set_current_parent(self.run_span_id)

            self.agent_span_id = None
            del self.agent_map[agent_name]

            logger.debug(f"[AIGIE] Agent completed: {agent_name} (status={status})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in handle_agent_end: {e}")

    # ========================================================================
    # LLM/Model Lifecycle Methods
    # ========================================================================

    async def handle_llm_start(
        self,
        callback_context: Any,
        llm_request: Any,
    ) -> str:
        """
        Called before an LLM call.

        Args:
            callback_context: The CallbackContext from ADK
            llm_request: The LlmRequest object

        Returns:
            The LLM span ID
        """
        if not self.config.enabled or not self.config.trace_llm_calls:
            return ""

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return ""

        try:
            span_id = str(uuid.uuid4())
            start_time = _utc_now()

            # Extract model info
            model = getattr(llm_request, 'model', None)
            if not model:
                config = getattr(llm_request, 'config', None)
                if config:
                    model = getattr(config, 'model', None)
            model = model or 'gemini'

            parent_id = self._get_current_parent()
            llm_depth = self._register_span_depth(span_id, parent_id)

            span_data = {
                'id': span_id,
                'trace_id': self.trace_id,
                'parent_id': parent_id,
                'name': f'LLM: {model}',
                'type': 'llm',
                'start_time': start_time.isoformat(),
                'metadata': {
                    'model': model,
                    'depth': llm_depth,
                },
                'tags': self.tags,
                'status': 'running',
                'depth': llm_depth,
                'model': model,
            }

            # Capture input if enabled
            if self.config.capture_inputs:
                messages = getattr(llm_request, 'messages', None)
                if messages:
                    messages_repr = str(messages)[:self.config.max_content_length]
                    span_data['input'] = messages_repr

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

            self.llm_span_id = span_id
            self._llm_start_time = start_time
            self._llm_model = model
            self._total_model_calls += 1

            logger.debug(f"[AIGIE] LLM call started: {model} (span_id={span_id})")
            return span_id

        except Exception as e:
            logger.warning(f"[AIGIE] Error in handle_llm_start: {e}")
            return ""

    async def handle_llm_end(
        self,
        callback_context: Any,
        llm_response: Any,
        error: Optional[Exception] = None,
    ) -> None:
        """
        Called after an LLM call completes.

        Args:
            callback_context: The CallbackContext from ADK
            llm_response: The LlmResponse object
            error: Optional exception if the call failed
        """
        if not self.config.enabled or not self.config.trace_llm_calls:
            return

        if not self.llm_span_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            end_time = _utc_now()
            duration = (end_time - self._llm_start_time).total_seconds() if hasattr(self, '_llm_start_time') else 0
            duration_ms = duration * 1000

            has_error = error is not None
            status = 'error' if has_error else 'success'

            # Extract token usage from response
            input_tokens = 0
            output_tokens = 0
            model = getattr(self, '_llm_model', 'gemini')

            if llm_response:
                usage = getattr(llm_response, 'usage', None)
                if usage:
                    input_tokens = getattr(usage, 'prompt_tokens', 0) or getattr(usage, 'input_tokens', 0) or 0
                    output_tokens = getattr(usage, 'completion_tokens', 0) or getattr(usage, 'output_tokens', 0) or 0

                # Also check for total_tokens
                if not input_tokens and not output_tokens:
                    total_tokens = getattr(usage, 'total_tokens', 0) if usage else 0
                    if total_tokens:
                        # Estimate split
                        input_tokens = int(total_tokens * 0.3)
                        output_tokens = total_tokens - input_tokens

                # Get model from response if available
                resp_model = getattr(llm_response, 'model', None)
                if resp_model:
                    model = resp_model

                # Check for errors in response
                detected_error = self._error_detector.detect_from_llm_response(llm_response, model)
                if detected_error:
                    self._detected_errors.append(detected_error)
                    has_error = True
                    status = 'error'

            # Calculate cost
            cost = calculate_google_adk_cost(model, input_tokens, output_tokens)

            # Update totals
            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens
            self._total_cost += cost

            update_data = {
                'id': self.llm_span_id,
                'trace_id': self.trace_id,
                'end_time': end_time.isoformat(),
                'duration_ns': int(duration * 1_000_000_000),
                'status': status,
                'is_error': has_error,
                'metadata': {
                    'model': model,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': input_tokens + output_tokens,
                    'cost': cost,
                    'duration_ms': duration_ms,
                    'status': status,
                },
                'prompt_tokens': input_tokens,
                'completion_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'total_cost': cost,
                'model': model,
            }

            # Capture output if enabled
            if self.config.capture_outputs and llm_response:
                content = getattr(llm_response, 'content', None)
                if content:
                    content_repr = str(content)[:self.config.max_content_length]
                    update_data['output'] = content_repr

            if error:
                error_str = str(error)[:500]
                update_data['error'] = error_str
                update_data['error_message'] = error_str
                self._has_errors = True
                if error_str not in self._error_messages:
                    self._error_messages.append(error_str)

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            logger.debug(f"[AIGIE] LLM call completed: {model} (tokens={input_tokens + output_tokens}, cost=${cost:.6f})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in handle_llm_end: {e}")
        finally:
            self.llm_span_id = None
            self._llm_start_time = None
            self._llm_model = None

    # ========================================================================
    # Tool Lifecycle Methods
    # ========================================================================

    async def handle_tool_start(
        self,
        tool: Any,
        tool_args: Dict[str, Any],
        tool_context: Any,
    ) -> str:
        """
        Called before a tool execution.

        Args:
            tool: The BaseTool instance
            tool_args: Arguments passed to the tool
            tool_context: The ToolContext from ADK

        Returns:
            The tool span ID
        """
        if not self.config.enabled or not self.config.trace_tools:
            return ""

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return ""

        try:
            tool_name = getattr(tool, 'name', 'unknown_tool')
            function_call_id = getattr(tool_context, 'function_call_id', str(uuid.uuid4()))

            span_id = str(uuid.uuid4())
            start_time = _utc_now()

            parent_id = self._get_current_parent()
            tool_depth = self._register_span_depth(span_id, parent_id)

            self.tool_map[function_call_id] = {
                'spanId': span_id,
                'startTime': start_time,
                'toolName': tool_name,
                'depth': tool_depth,
                'tool_args': tool_args,
            }

            span_data = {
                'id': span_id,
                'trace_id': self.trace_id,
                'parent_id': parent_id,
                'name': f'Tool: {tool_name}',
                'type': 'tool',
                'start_time': start_time.isoformat(),
                'metadata': {
                    'tool_name': tool_name,
                    'function_call_id': function_call_id,
                    'depth': tool_depth,
                },
                'tags': self.tags,
                'status': 'running',
                'depth': tool_depth,
            }

            # Capture input if enabled
            if self.config.capture_inputs and tool_args:
                input_repr = str(tool_args)[:self.config.max_tool_result_length]
                span_data['input'] = input_repr

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

            self._total_tool_calls += 1

            logger.debug(f"[AIGIE] Tool started: {tool_name} (span_id={span_id})")
            return span_id

        except Exception as e:
            logger.warning(f"[AIGIE] Error in handle_tool_start: {e}")
            return ""

    async def handle_tool_end(
        self,
        tool: Any,
        tool_args: Dict[str, Any],
        tool_context: Any,
        result: Any,
        error: Optional[Exception] = None,
    ) -> None:
        """
        Called after a tool execution completes.

        Args:
            tool: The BaseTool instance
            tool_args: Arguments passed to the tool
            tool_context: The ToolContext from ADK
            result: The tool execution result
            error: Optional exception if the tool failed
        """
        if not self.config.enabled or not self.config.trace_tools:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            function_call_id = getattr(tool_context, 'function_call_id', None)
            if not function_call_id:
                return

            tool_data = self.tool_map.get(function_call_id)
            if not tool_data:
                return

            end_time = _utc_now()
            duration = (end_time - tool_data['startTime']).total_seconds()
            duration_ms = duration * 1000

            tool_name = tool_data['toolName']
            has_error = error is not None
            status = 'error' if has_error else 'success'

            # Error detection from tool result
            detected_error = self._error_detector.detect_from_tool_result(
                tool_name=tool_name,
                tool_use_id=function_call_id,
                result=result,
                is_error_flag=has_error,
                duration_ms=duration_ms,
            )
            if detected_error:
                self._detected_errors.append(detected_error)
                has_error = True
                status = 'error'

            update_data = {
                'id': tool_data['spanId'],
                'trace_id': self.trace_id,
                'end_time': end_time.isoformat(),
                'duration_ns': int(duration * 1_000_000_000),
                'status': status,
                'is_error': has_error,
                'metadata': {
                    'tool_name': tool_name,
                    'function_call_id': function_call_id,
                    'duration_ms': duration_ms,
                    'status': status,
                },
            }

            # Capture output if enabled
            if self.config.capture_outputs:
                if result is not None:
                    result_repr = str(result)[:self.config.max_tool_result_length]
                    update_data['output'] = result_repr

            if error:
                error_str = str(error)[:500]
                update_data['error'] = error_str
                update_data['error_message'] = error_str
                self._has_errors = True
                if error_str not in self._error_messages:
                    self._error_messages.append(error_str)

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            del self.tool_map[function_call_id]

            logger.debug(f"[AIGIE] Tool completed: {tool_name} (status={status}, duration_ms={duration_ms:.2f})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in handle_tool_end: {e}")

    # ========================================================================
    # Event Handling
    # ========================================================================

    async def handle_event(
        self,
        invocation_context: Any,
        event: Any,
    ) -> None:
        """
        Called for each event in the Runner's event stream.

        Args:
            invocation_context: The InvocationContext from ADK
            event: The event object
        """
        if not self.config.enabled or not self.config.trace_events:
            return

        # Events are typically captured as metadata on existing spans
        # This hook can be used for fine-grained event tracking if needed
        pass

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _complete_pending_spans(self, end_time: datetime) -> None:
        """Complete any pending spans that weren't explicitly closed."""
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return

        # Complete pending tool spans
        for function_call_id, tool_data in list(self.tool_map.items()):
            duration = (end_time - tool_data['startTime']).total_seconds()
            update_data = {
                'id': tool_data['spanId'],
                'trace_id': self.trace_id,
                'end_time': end_time.isoformat(),
                'duration_ns': int(duration * 1_000_000_000),
                'status': 'success',
                'metadata': {
                    'tool_name': tool_data['toolName'],
                    'pending_cleanup': True,
                },
            }
            try:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            except Exception:
                pass
        self.tool_map.clear()

        # Complete pending agent spans
        for agent_name, agent_data in list(self.agent_map.items()):
            duration = (end_time - agent_data['startTime']).total_seconds()
            update_data = {
                'id': agent_data['spanId'],
                'trace_id': self.trace_id,
                'end_time': end_time.isoformat(),
                'duration_ns': int(duration * 1_000_000_000),
                'status': 'success',
                'metadata': {
                    'agent_name': agent_name,
                    'pending_cleanup': True,
                },
            }
            try:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            except Exception:
                pass
        self.agent_map.clear()

        # Complete pending LLM span
        if self.llm_span_id and hasattr(self, '_llm_start_time') and self._llm_start_time:
            duration = (end_time - self._llm_start_time).total_seconds()
            update_data = {
                'id': self.llm_span_id,
                'trace_id': self.trace_id,
                'end_time': end_time.isoformat(),
                'duration_ns': int(duration * 1_000_000_000),
                'status': 'success',
                'metadata': {
                    'pending_cleanup': True,
                },
            }
            try:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            except Exception:
                pass
            self.llm_span_id = None

    def __repr__(self) -> str:
        return (
            f"GoogleADKHandler("
            f"trace_id={self.trace_id}, "
            f"model_calls={self._total_model_calls}, "
            f"tool_calls={self._total_tool_calls}, "
            f"tokens={self._total_input_tokens + self._total_output_tokens}, "
            f"cost=${self._total_cost:.4f})"
        )
