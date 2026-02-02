"""
Claude Agent SDK callback handler for Aigie SDK.

Provides automatic tracing for Claude Agent SDK query execution,
tool usage, and conversation sessions.

Includes comprehensive error detection and drift monitoring.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING


def _utc_now() -> datetime:
    """Get current time in UTC with timezone info."""
    return datetime.now(timezone.utc)


def _utc_isoformat() -> str:
    """Get current UTC time as ISO format string."""
    return datetime.now(timezone.utc).isoformat()

from ...buffer import EventType
from .cost_tracking import calculate_claude_cost
from .error_detection import ErrorDetector, get_error_detector, DetectedError
from .drift_detection import DriftDetector

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .session_context import ClaudeSessionContext


def _shorten_model_name(model: str) -> str:
    """Convert full model name to short display name.

    Examples:
        claude-sonnet-4-20250514 -> Sonnet
        claude-haiku-3-5-20241022 -> Haiku
        claude-opus-4-5-20251101 -> Opus
    """
    if not model:
        return "Claude"
    model_lower = model.lower()
    if 'sonnet' in model_lower:
        return 'Sonnet'
    elif 'haiku' in model_lower:
        return 'Haiku'
    elif 'opus' in model_lower:
        return 'Opus'
    return 'Claude'


def _format_subagent_name(subagent_type: str) -> str:
    """Format subagent type as a proper display name.

    Examples:
        researcher -> Researcher
        data-analyst -> Data Analyst
        report-writer -> Report Writer
    """
    if not subagent_type:
        return "Subagent"
    return subagent_type.replace('-', ' ').replace('_', ' ').title()


class ClaudeAgentSDKHandler:
    """
    Claude Agent SDK handler for Aigie tracing.

    Automatically traces Claude Agent SDK executions including:
    - Query execution (stateless)
    - Client sessions (stateful)
    - Tool use with PreToolUse/PostToolUse hooks
    - Message streaming and costs
    - Token usage tracking

    Example:
        >>> from claude_agent_sdk import query
        >>> from aigie.integrations.claude_agent_sdk import ClaudeAgentSDKHandler
        >>>
        >>> handler = ClaudeAgentSDKHandler(
        ...     trace_name='research-agent',
        ...     metadata={'project': 'analysis'}
        ... )
        >>>
        >>> # Manual usage
        >>> await handler.handle_query_start("What is the capital of France?", {})
        >>> # ... execute query
        >>> await handler.handle_query_end(query_id, messages, result_message)
    """

    def __init__(
        self,
        trace_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        capture_tool_results: bool = True,
        capture_messages: bool = True,
        session_context: Optional["ClaudeSessionContext"] = None,
    ):
        """
        Initialize Claude Agent SDK handler.

        Args:
            trace_name: Name for the trace
            metadata: Additional metadata to attach
            tags: Tags to apply to trace and spans
            user_id: User ID for the trace
            session_id: Session ID for the trace
            capture_tool_results: Whether to capture tool results
            capture_messages: Whether to capture message content
            session_context: Optional session context for trace sharing
        """
        self.trace_name = trace_name
        self.metadata = metadata or {}
        self.tags = tags or []
        self.user_id = user_id
        self.session_id = session_id
        self.capture_tool_results = capture_tool_results
        self.capture_messages = capture_messages

        # Session context for trace sharing
        self._session_context = session_context

        # State tracking - inherit trace_id from session context if available
        self.trace_id: Optional[str] = session_context.trace_id if session_context else None
        self.query_span_id: Optional[str] = None
        self.session_span_id: Optional[str] = None
        self.tool_map: Dict[str, Dict[str, Any]] = {}  # tool_use_id -> {spanId, startTime}
        self.turn_map: Dict[str, Dict[str, Any]] = {}  # turn_id -> {spanId, startTime}
        # subagent_map now tracks tokens for aggregation
        self.subagent_map: Dict[str, Dict[str, Any]] = {}  # tool_use_id -> {spanId, startTime, type, description, tokens...}

        # Current context for parent relationships
        self._current_query_span_id: Optional[str] = None
        self._current_turn_span_id: Optional[str] = None
        self._current_parent_tool_use_id: Optional[str] = None  # For tracking subagent context
        self._aigie = None
        self._trace_context: Optional[Any] = None

        # Parent span stack for nested subagent hierarchy
        self._parent_span_stack: List[str] = []
        # Local current parent for when no session context
        self._local_current_parent: Optional[str] = None

        # Depth tracking for flow view - maps span_id to depth
        self._span_depth_map: Dict[str, int] = {}
        self._current_depth: int = 0

        # Statistics (delegate to session context if available)
        self._local_total_turns = 0
        self._local_total_tool_calls = 0
        self._local_total_input_tokens = 0
        self._local_total_output_tokens = 0
        self._local_total_cache_read_tokens = 0
        self._local_total_cache_creation_tokens = 0
        self._local_total_cost = 0.0

        # Error detection and monitoring
        self._error_detector = ErrorDetector()
        self._drift_detector = DriftDetector()
        self._detected_errors: List[DetectedError] = []
        self._query_start_time: Optional[datetime] = None

    @property
    def total_turns(self) -> int:
        if self._session_context:
            return self._session_context.total_turns
        return self._local_total_turns

    @total_turns.setter
    def total_turns(self, value: int) -> None:
        if self._session_context:
            self._session_context.total_turns = value
        else:
            self._local_total_turns = value

    @property
    def total_tool_calls(self) -> int:
        if self._session_context:
            return self._session_context.total_tool_calls
        return self._local_total_tool_calls

    @total_tool_calls.setter
    def total_tool_calls(self, value: int) -> None:
        if self._session_context:
            self._session_context.total_tool_calls = value
        else:
            self._local_total_tool_calls = value

    @property
    def total_input_tokens(self) -> int:
        if self._session_context:
            return self._session_context.total_input_tokens
        return self._local_total_input_tokens

    @total_input_tokens.setter
    def total_input_tokens(self, value: int) -> None:
        if self._session_context:
            self._session_context.total_input_tokens = value
        else:
            self._local_total_input_tokens = value

    @property
    def total_output_tokens(self) -> int:
        if self._session_context:
            return self._session_context.total_output_tokens
        return self._local_total_output_tokens

    @total_output_tokens.setter
    def total_output_tokens(self, value: int) -> None:
        if self._session_context:
            self._session_context.total_output_tokens = value
        else:
            self._local_total_output_tokens = value

    @property
    def total_cache_read_tokens(self) -> int:
        if self._session_context:
            return self._session_context.total_cache_read_tokens
        return self._local_total_cache_read_tokens

    @total_cache_read_tokens.setter
    def total_cache_read_tokens(self, value: int) -> None:
        if self._session_context:
            self._session_context.total_cache_read_tokens = value
        else:
            self._local_total_cache_read_tokens = value

    @property
    def total_cache_creation_tokens(self) -> int:
        if self._session_context:
            return self._session_context.total_cache_creation_tokens
        return self._local_total_cache_creation_tokens

    @total_cache_creation_tokens.setter
    def total_cache_creation_tokens(self, value: int) -> None:
        if self._session_context:
            self._session_context.total_cache_creation_tokens = value
        else:
            self._local_total_cache_creation_tokens = value

    @property
    def total_cost(self) -> float:
        if self._session_context:
            return self._session_context.total_cost
        return self._local_total_cost

    @total_cost.setter
    def total_cost(self, value: float) -> None:
        if self._session_context:
            self._session_context.total_cost = value
        else:
            self._local_total_cost = value

    def _get_aigie(self):
        """Lazy load Aigie client."""
        if self._aigie is None:
            from ...client import get_aigie
            self._aigie = get_aigie()
        return self._aigie

    def _get_current_parent(self) -> Optional[str]:
        """Get current parent span ID for nesting."""
        if self._session_context:
            ctx_parent = self._session_context.get_current_parent()
            if ctx_parent:
                return ctx_parent
        # Check local parent first (for subagent nesting), then fall back to turn/query
        if self._local_current_parent:
            return self._local_current_parent
        return self._current_turn_span_id or self._current_query_span_id

    def _set_current_parent(self, span_id: Optional[str]) -> None:
        """Set current parent span ID."""
        self._local_current_parent = span_id
        if self._session_context:
            self._session_context.set_current_parent(span_id)

    def _get_depth_for_parent(self, parent_id: Optional[str]) -> int:
        """Calculate depth based on parent span's depth."""
        if not parent_id:
            return 0  # Root level (trace)
        # Look up parent's depth and add 1
        parent_depth = self._span_depth_map.get(parent_id, 0)
        return parent_depth + 1

    def _register_span_depth(self, span_id: str, parent_id: Optional[str]) -> int:
        """Register a span's depth and return it."""
        depth = self._get_depth_for_parent(parent_id)
        self._span_depth_map[span_id] = depth
        return depth

    def _get_current_subagent(self) -> Optional[Dict[str, Any]]:
        """Get the current active subagent for token attribution."""
        # Find the most recently spawned subagent that hasn't ended
        # This is tracked via the parent span stack
        if self._parent_span_stack:
            # Find subagent by span ID
            for tool_use_id, subagent_data in self.subagent_map.items():
                if subagent_data.get('spanId') == self._parent_span_stack[-1]:
                    return subagent_data
        return None

    def set_trace_context(self, trace_context: Any) -> None:
        """Set an existing trace context to use."""
        self._trace_context = trace_context
        if hasattr(trace_context, 'id'):
            self.trace_id = str(trace_context.id)

    async def handle_query_start(
        self,
        prompt: str,
        options: Dict[str, Any],
        model: Optional[str] = None,
    ) -> str:
        """
        Called when a query() call starts.

        Args:
            prompt: The prompt being sent
            options: Query options (tools, system_prompt, etc.)
            model: The model being used

        Returns:
            The query ID for tracking
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return ""

        # Record query start time for duration tracking
        self._query_start_time = _utc_now()

        # Reset error tracking for this query
        self._detected_errors = []

        # Reset drift detector for this query (new plan per query)
        self._drift_detector = DriftDetector()

        # Capture initial plan for drift detection
        system_prompt = options.get('system_prompt', '')
        if system_prompt:
            self._drift_detector.capture_system_prompt(system_prompt)
        self._drift_detector.capture_initial_prompt(prompt)

        # Generate trace ID if not set - use session context if available
        if not self.trace_id:
            if self._session_context:
                self.trace_id = self._session_context.trace_id
            elif self._trace_context and hasattr(self._trace_context, 'id'):
                self.trace_id = str(self._trace_context.id)
            else:
                self.trace_id = str(uuid.uuid4())

        # Build trace name - use session context name if available
        trace_name = self.trace_name
        if not trace_name and self._session_context:
            trace_name = self._session_context.trace_name
        if not trace_name:
            # Generate descriptive name with model and prompt preview
            model_short = (model or "claude").split("-")[0].capitalize()
            if prompt:
                # Create prompt preview (30 chars, remove newlines)
                preview = prompt[:30].replace('\n', ' ').strip()
                if len(prompt) > 30:
                    preview += "..."
                trace_name = f"{model_short}: {preview}"
            else:
                trace_name = f"{model_short} Agent"

        # Extract tool names if present
        tools = options.get('tools', [])
        tool_names = []
        if tools:
            for t in tools[:10]:
                if hasattr(t, 'name'):
                    tool_names.append(t.name)
                elif isinstance(t, dict) and 'name' in t:
                    tool_names.append(t['name'])

        # Build metadata
        trace_metadata = {
            **self.metadata,
            'model': model or options.get('model', 'claude-sonnet-4-20250514'),
            'tool_count': len(tools),
            'tool_names': tool_names[:10],
            'framework': 'claude_agent_sdk',
            'max_tokens': options.get('max_tokens'),
            'max_turns': options.get('max_turns'),
        }

        # Only create trace if we don't have a trace context AND haven't created one yet
        should_create_trace = not self._trace_context
        if self._session_context and self._session_context.trace_created:
            should_create_trace = False

        if should_create_trace:
            trace_data = {
                'id': self.trace_id,
                'name': trace_name,
                'type': 'agent',
                'input': {
                    'prompt': prompt[:2000] if self.capture_messages else '[redacted]',
                    'model': trace_metadata['model'],
                    'tool_count': len(tools),
                },
                'status': 'pending',
                'tags': [*self.tags, 'claude_agent_sdk'],
                'metadata': trace_metadata,
                'start_time': _utc_isoformat(),
                'created_at': _utc_isoformat(),
            }

            if self.user_id:
                trace_data['user_id'] = self.user_id
            if self.session_id:
                trace_data['session_id'] = self.session_id

            # Send trace via buffer
            if aigie._buffer:
                logger.debug(f"[AIGIE] TRACE_CREATE: id={self.trace_id}, name={trace_name}")
                await aigie._buffer.add(EventType.TRACE_CREATE, trace_data)

            # Mark trace as created in session context
            if self._session_context:
                self._session_context.mark_trace_created()

        # Create query span with clean naming
        self.query_span_id = str(uuid.uuid4())
        model_short = _shorten_model_name(trace_metadata['model'])

        # Register query span depth (root level = 0)
        query_depth = self._register_span_depth(self.query_span_id, None)

        query_span_data = {
            'id': self.query_span_id,
            'trace_id': self.trace_id,
            'name': f'Query ({model_short})',
            'type': 'llm',
            'input': {
                'prompt': prompt[:2000] if self.capture_messages else '[redacted]',
                'model': trace_metadata['model'],
                'tools': tool_names,
                'system_prompt': options.get('system_prompt', '')[:500] if self.capture_messages else None,
            },
            'status': 'pending',
            'tags': self.tags or [],
            'metadata': {**trace_metadata, 'depth': query_depth},
            'model': trace_metadata['model'],
            'start_time': _utc_isoformat(),
            'created_at': _utc_isoformat(),
            'depth': query_depth,  # For flow view ordering
        }

        self._current_query_span_id = self.query_span_id

        # Set query span as current parent in session context for child span nesting
        if self._session_context:
            self._session_context.current_query_span_id = self.query_span_id
            self._session_context.set_current_parent(self.query_span_id)

        if aigie._buffer:
            logger.debug(f"[AIGIE] SPAN_CREATE: id={self.query_span_id}, name=Query ({model_short}), parent=None (trace root)")
            await aigie._buffer.add(EventType.SPAN_CREATE, query_span_data)

        return self.query_span_id

    async def handle_query_end(
        self,
        query_id: str,
        messages: List[Any],
        result_message: Any,
        error: Optional[str] = None,
    ) -> None:
        """
        Called when a query() call completes.

        Args:
            query_id: Query ID from handle_query_start
            messages: List of messages from the conversation
            result_message: The ResultMessage with final output and costs
            error: Error message if query failed
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return

        end_time = _utc_now()
        success = error is None

        # Extract usage and cost from ResultMessage
        usage = {}
        cost = 0.0
        model = None

        if result_message:
            if hasattr(result_message, 'usage'):
                usage_obj = result_message.usage
                # Handle both dict and object formats
                if isinstance(usage_obj, dict):
                    usage = {
                        'input_tokens': usage_obj.get('input_tokens', 0),
                        'output_tokens': usage_obj.get('output_tokens', 0),
                        'cache_read_input_tokens': usage_obj.get('cache_read_input_tokens', 0),
                        'cache_creation_input_tokens': usage_obj.get('cache_creation_input_tokens', 0),
                    }
                else:
                    usage = {
                        'input_tokens': getattr(usage_obj, 'input_tokens', 0),
                        'output_tokens': getattr(usage_obj, 'output_tokens', 0),
                        'cache_read_input_tokens': getattr(usage_obj, 'cache_read_input_tokens', 0),
                        'cache_creation_input_tokens': getattr(usage_obj, 'cache_creation_input_tokens', 0),
                    }
                # Update totals
                self.total_input_tokens += usage.get('input_tokens', 0)
                self.total_output_tokens += usage.get('output_tokens', 0)
                self.total_cache_read_tokens += usage.get('cache_read_input_tokens', 0)
                self.total_cache_creation_tokens += usage.get('cache_creation_input_tokens', 0)

            if hasattr(result_message, 'total_cost_usd'):
                cost = result_message.total_cost_usd or 0.0
            elif hasattr(result_message, 'model'):
                # Calculate cost from usage
                model = result_message.model
                cost = calculate_claude_cost(model, usage)

            self.total_cost += cost

            if hasattr(result_message, 'model'):
                model = result_message.model

        # Extract final output
        output = None
        if messages and self.capture_messages:
            last_message = messages[-1] if messages else None
            if last_message:
                if hasattr(last_message, 'content'):
                    content = last_message.content
                    if isinstance(content, str):
                        output = content[:2000]
                    elif isinstance(content, list):
                        # Extract text blocks
                        text_parts = []
                        for block in content:
                            if hasattr(block, 'text'):
                                text_parts.append(block.text)
                            elif isinstance(block, dict) and 'text' in block:
                                text_parts.append(block['text'])
                        output = '\n'.join(text_parts)[:2000]

        # Update query span
        if self.query_span_id:
            # Get model name for span name
            model_name = model or (self.metadata.get('model') if self.metadata else None) or 'claude-sonnet-4-20250514'
            model_short = _shorten_model_name(model_name)

            # Get token values - prefer local usage, fallback to accumulated totals
            span_input_tokens = usage.get('input_tokens') or self.total_input_tokens
            span_output_tokens = usage.get('output_tokens') or self.total_output_tokens
            span_total_tokens = span_input_tokens + span_output_tokens
            span_cost = cost if cost > 0 else self.total_cost

            query_update = {
                'id': self.query_span_id,
                'trace_id': self.trace_id,  # Required for backend merge
                'name': f'Query ({model_short})',  # Clean name without verbose model
                'type': 'llm',  # Include type to handle race conditions
                'status': 'success' if success else 'failed',
                'output': {
                    'response': output,
                    'message_count': len(messages),
                    'usage': {
                        'input_tokens': span_input_tokens,
                        'output_tokens': span_output_tokens,
                        'total_tokens': span_total_tokens,
                    },
                    'cost': span_cost,
                },
                'end_time': end_time.isoformat(),
                'model': model_name,
                'prompt_tokens': span_input_tokens,
                'completion_tokens': span_output_tokens,
                'total_tokens': span_total_tokens,
                'total_cost': span_cost,
            }

            if error:
                query_update['error'] = error
                query_update['error_message'] = error

            if aigie._buffer:
                logger.debug(f"[AIGIE] SPAN_UPDATE: id={query_update['id']}, tokens={query_update.get('total_tokens')}, status={query_update.get('status')}")
                await aigie._buffer.add(EventType.SPAN_UPDATE, query_update)

        # Update trace with top-level token fields for backend aggregation
        update_data = {
            'id': self.trace_id,
            'status': 'success' if success else 'failed',
            'output': {
                'response': output,
                'message_count': len(messages),
                'total_tokens': self.total_input_tokens + self.total_output_tokens,
                'total_cost': self.total_cost,
                'tool_calls': self.total_tool_calls,
            },
            'end_time': end_time.isoformat(),
            # Top-level token/cost fields for backend aggregation display
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'prompt_tokens': self.total_input_tokens,
            'completion_tokens': self.total_output_tokens,
            'total_cost': self.total_cost,
        }

        if error:
            update_data['error'] = error
            update_data['error_message'] = error

        # Finalize drift detection and get all detected drifts
        start_time = self._query_start_time or _utc_now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        total_tokens = self.total_input_tokens + self.total_output_tokens

        detected_drifts = self._drift_detector.finalize(
            total_duration_ms=duration_ms,
            total_tokens=total_tokens,
            total_cost=self.total_cost,
            final_output=output,
        )

        # Add monitoring data to trace output
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

        # Add monitoring to trace metadata
        if 'metadata' not in update_data:
            update_data['metadata'] = {}
        update_data['metadata']['monitoring'] = monitoring_data

        # Also add summary to output for visibility
        update_data['output']['monitoring'] = {
            'drift_count': len(detected_drifts),
            'error_count': len(self._detected_errors),
            'retries': self._drift_detector.execution.retry_count if self._drift_detector.execution else 0,
            'plan_captured': self._drift_detector._plan_captured,
        }

        # Log monitoring summary
        if detected_drifts:
            logger.info(f"[AIGIE] Drift detection summary: {len(detected_drifts)} drifts detected")
            for drift in detected_drifts[:3]:  # Log first 3
                logger.info(f"[AIGIE]   - {drift.drift_type.value}: {drift.description[:80]}")
        if self._detected_errors:
            logger.info(f"[AIGIE] Error detection summary: {len(self._detected_errors)} errors detected")
            for err in self._detected_errors[:3]:  # Log first 3
                logger.info(f"[AIGIE]   - {err.error_type.value}: {err.message[:80]}")

        if aigie._buffer:
            # Debug: Log trace update data
            logger.debug(f"[AIGIE] TRACE_UPDATE: id={self.trace_id}, total_tokens={update_data['total_tokens']}, cost={update_data['total_cost']}")
            await aigie._buffer.add(EventType.TRACE_UPDATE, update_data)

        # Complete any pending spans to ensure all have end_time
        await self.complete_pending_turn_spans()
        await self.complete_pending_tool_spans()
        await self.complete_pending_subagent_spans()

        # Clear query span from session context since query is done
        self._current_query_span_id = None
        if self._session_context:
            self._session_context.current_query_span_id = None
            self._session_context.set_current_parent(None)

    async def handle_tool_use_start(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_use_id: str,
        parent_tool_use_id: Optional[str] = None,
    ) -> str:
        """
        Called when a tool use starts (PreToolUse hook).

        Args:
            tool_name: Name of the tool being called
            tool_input: Input arguments to the tool
            tool_use_id: Unique ID for this tool use
            parent_tool_use_id: Optional parent tool use ID from message context
                              (used to explicitly parent tools under their subagent)

        Returns:
            The span ID for this tool call
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return ""

        self.total_tool_calls += 1
        span_id = str(uuid.uuid4())
        start_time = _utc_now()

        # Get parent span ID - prefer explicit parent_tool_use_id if it maps to a subagent
        if parent_tool_use_id and parent_tool_use_id in self.subagent_map:
            parent_id = self.subagent_map[parent_tool_use_id].get('spanId')
            logger.debug(f"[AIGIE] Tool {tool_name} using explicit parent from parent_tool_use_id: {parent_id}")
        else:
            parent_id = self._get_current_parent()

        # Increment tool count on current subagent if we're inside one
        current_subagent = self._get_current_subagent()
        parent_subagent_type = None
        if current_subagent:
            current_subagent['tool_count'] = current_subagent.get('tool_count', 0) + 1
            parent_subagent_type = current_subagent.get('subagentType')

        # Calculate depth for flow view ordering
        tool_depth = self._register_span_depth(span_id, parent_id)

        self.tool_map[tool_use_id] = {
            'spanId': span_id,
            'startTime': start_time,
            'toolName': tool_name,
            'parentSubagentType': parent_subagent_type,
            'tool_input': tool_input,  # Store for drift detection
            'depth': tool_depth,
        }

        # Serialize tool input
        input_data = {}
        if self.capture_tool_results:
            input_data = {k: str(v)[:500] for k, v in tool_input.items()} if tool_input else {}

        span_data = {
            'id': span_id,
            'trace_id': self.trace_id,
            'parent_id': parent_id,
            'name': tool_name,  # Clean name without prefix
            'type': 'tool',
            'input': input_data,
            'status': 'running',
            'tags': self.tags or [],
            'metadata': {
                'toolName': tool_name,
                'toolUseId': tool_use_id,
                'framework': 'claude_agent_sdk',
                'status': 'running',
                'parentSubagentType': parent_subagent_type,
                'depth': tool_depth,
            },
            'start_time': start_time.isoformat(),
            'created_at': start_time.isoformat(),
            'depth': tool_depth,  # For flow view ordering
        }

        if aigie._buffer:
            logger.debug(f"[AIGIE] SPAN_CREATE: id={span_id}, name={tool_name}, parent={parent_id}, status=running")
            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

        return span_id

    async def handle_tool_use_end(
        self,
        tool_use_id: str,
        result: Any,
        is_error: bool = False,
    ) -> None:
        """
        Called when a tool use completes (PostToolUse hook).

        Args:
            tool_use_id: Unique ID for this tool use
            result: Result from the tool execution
            is_error: Whether the tool execution failed
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        tool_data = self.tool_map.get(tool_use_id)
        if not tool_data:
            return

        end_time = _utc_now()
        duration = (end_time - tool_data['startTime']).total_seconds()
        duration_ms = duration * 1000

        # Error detection - check tool result for errors
        detected_error = self._error_detector.detect_from_tool_result(
            tool_name=tool_data['toolName'],
            tool_use_id=tool_use_id,
            result=result,
            is_error_flag=is_error,
            duration_ms=duration_ms,
        )

        # Update is_error if we detected an error in the result
        if detected_error and not is_error:
            is_error = True
            self._detected_errors.append(detected_error)
            logger.warning(f"[AIGIE] Error detected in tool {tool_data['toolName']}: {detected_error.message[:100]}")

        # Record for drift detection
        self._drift_detector.record_tool_use(
            tool_name=tool_data['toolName'],
            tool_input=tool_data.get('tool_input', {}),
            duration_ms=duration_ms,
            is_error=is_error,
        )

        # Determine status string
        status = 'error' if is_error else 'success'

        output_data = {}
        if self.capture_tool_results:
            if isinstance(result, str):
                output_data['result'] = result[:1000]
            elif hasattr(result, 'model_dump'):
                output_data['result'] = str(result.model_dump())[:1000]
            else:
                output_data['result'] = str(result)[:1000]
        output_data['is_error'] = is_error
        output_data['status'] = status

        # Add error details if detected
        error_metadata = {}
        if detected_error:
            error_metadata = {
                'error_type': detected_error.error_type.value,
                'error_severity': detected_error.severity.value,
                'error_is_transient': detected_error.is_transient,
            }

        update_data = {
            'id': tool_data['spanId'],
            'trace_id': self.trace_id,  # Required for backend merge
            'name': tool_data['toolName'],  # Clean name without prefix
            'type': 'tool',  # Include type for race conditions
            'output': output_data,
            'status': status,
            'is_error': is_error,  # Top-level for backend visibility
            'end_time': end_time.isoformat(),
            'duration_ns': int(duration * 1_000_000_000),
            'metadata': {
                'toolName': tool_data['toolName'],
                'toolUseId': tool_use_id,
                'framework': 'claude_agent_sdk',
                'status': status,
                'duration_ms': int(duration_ms),
                'parentSubagentType': tool_data.get('parentSubagentType'),
                **error_metadata,
            },
        }

        if is_error:
            update_data['error'] = str(result)[:500]
            update_data['error_message'] = str(result)[:500]
            if detected_error:
                update_data['error_type'] = detected_error.error_type.value

        if aigie._buffer:
            logger.debug(f"[AIGIE] SPAN_UPDATE: id={tool_data['spanId']}, name={tool_data['toolName']}, status={status}")
            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

        del self.tool_map[tool_use_id]

    async def complete_pending_tool_spans(self) -> None:
        """
        Complete any pending tool spans that weren't explicitly closed.

        This ensures all tool spans have end_time populated even if
        the corresponding ToolResultBlock was missed.
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        end_time = _utc_now()
        pending_ids = list(self.tool_map.keys())

        for tool_use_id in pending_ids:
            tool_data = self.tool_map.get(tool_use_id)
            if not tool_data:
                continue

            duration = (end_time - tool_data['startTime']).total_seconds()

            update_data = {
                'id': tool_data['spanId'],
                'trace_id': self.trace_id,  # Required for backend merge
                'name': tool_data['toolName'],  # Clean name without prefix
                'type': 'tool',  # Include type for race conditions
                'status': 'success',  # Assume success if not explicitly failed
                'end_time': end_time.isoformat(),
                'duration_ns': int(duration * 1_000_000_000),
            }

            if aigie._buffer:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            del self.tool_map[tool_use_id]

    async def complete_pending_subagent_spans(self) -> None:
        """
        Complete any pending subagent spans that weren't explicitly closed.

        This ensures all subagent spans have end_time populated even if
        the corresponding ToolResultBlock was missed.
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        end_time = _utc_now()
        pending_ids = list(self.subagent_map.keys())

        for tool_use_id in pending_ids:
            subagent_data = self.subagent_map.get(tool_use_id)
            if not subagent_data:
                continue

            duration = (end_time - subagent_data['startTime']).total_seconds()

            subagent_name = _format_subagent_name(subagent_data['subagentType'])
            update_data = {
                'id': subagent_data['spanId'],
                'trace_id': self.trace_id,
                'name': subagent_name,
                'type': 'agent',
                'status': 'success',  # Assume success if not explicitly failed
                'end_time': end_time.isoformat(),
                'duration_ns': int(duration * 1_000_000_000),
                # Include accumulated tokens if available
                'prompt_tokens': subagent_data.get('input_tokens', 0),
                'completion_tokens': subagent_data.get('output_tokens', 0),
                'total_tokens': subagent_data.get('input_tokens', 0) + subagent_data.get('output_tokens', 0),
                'total_cost': subagent_data.get('cost', 0.0),
                'metadata': {
                    'subagentType': subagent_data['subagentType'],
                    'tool_count': subagent_data.get('tool_count', 0),
                },
            }

            if aigie._buffer:
                logger.debug(f"[AIGIE] Completing pending subagent span: {subagent_name}")
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            # Restore previous parent from stack
            if self._parent_span_stack:
                self._parent_span_stack.pop()
                if self._parent_span_stack:
                    self._set_current_parent(self._parent_span_stack[-1])
                else:
                    self._set_current_parent(self._current_turn_span_id or self._current_query_span_id)

            del self.subagent_map[tool_use_id]

    async def complete_pending_turn_spans(self) -> None:
        """
        Complete any pending turn spans that weren't explicitly closed.

        This ensures all turn (chain) spans have end_time populated even if
        the turn wasn't properly ended via handle_turn_end.
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        end_time = _utc_now()
        pending_ids = list(self.turn_map.keys())

        for turn_id in pending_ids:
            turn_data = self.turn_map.get(turn_id)
            if not turn_data:
                continue

            duration = (end_time - turn_data['startTime']).total_seconds()

            update_data = {
                'id': turn_data['spanId'],
                'trace_id': self.trace_id,
                'name': f"Turn {turn_data['turnNumber']}",
                'type': 'chain',
                'status': 'success',  # Assume success if not explicitly failed
                'end_time': end_time.isoformat(),
                'duration_ns': int(duration * 1_000_000_000),
            }

            if aigie._buffer:
                logger.debug(f"[AIGIE] Completing pending turn span: Turn {turn_data['turnNumber']}")
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            del self.turn_map[turn_id]

        self._current_turn_span_id = None

    async def handle_session_start(
        self,
        client: Any,
        options: Dict[str, Any],
    ) -> str:
        """
        Called when a ClaudeSDKClient session starts.

        Args:
            client: The ClaudeSDKClient instance
            options: Session options

        Returns:
            The session ID for tracking
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return ""

        # Generate trace ID if not set
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())

        # Build descriptive trace name
        model = options.get('model', 'claude-sonnet-4-20250514')
        model_short = model.split("-")[0].capitalize() if model else "Claude"
        trace_name = self.trace_name or f"{model_short} Session"

        # Build metadata
        trace_metadata = {
            **self.metadata,
            'framework': 'claude_agent_sdk',
            'session_type': 'stateful',
            'model': options.get('model', 'claude-sonnet-4-20250514'),
        }

        # Create trace
        trace_data = {
            'id': self.trace_id,
            'name': trace_name,
            'type': 'agent',
            'input': {
                'session_type': 'stateful',
                'model': trace_metadata['model'],
            },
            'status': 'pending',
            'tags': [*self.tags, 'claude_agent_sdk', 'session'],
            'metadata': trace_metadata,
            'start_time': _utc_isoformat(),
            'created_at': _utc_isoformat(),
        }

        if self.user_id:
            trace_data['user_id'] = self.user_id
        if self.session_id:
            trace_data['session_id'] = self.session_id

        if aigie._buffer:
            logger.debug(f"[AIGIE] TRACE_CREATE (session): id={self.trace_id}, name={trace_name}")
            await aigie._buffer.add(EventType.TRACE_CREATE, trace_data)

        # Create session span
        self.session_span_id = str(uuid.uuid4())
        session_span_data = {
            'id': self.session_span_id,
            'trace_id': self.trace_id,
            'name': 'session',
            'type': 'chain',
            'input': {'session_type': 'stateful'},
            'status': 'pending',
            'tags': self.tags or [],
            'metadata': trace_metadata,
            'start_time': _utc_isoformat(),
            'created_at': _utc_isoformat(),
        }

        if aigie._buffer:
            logger.debug(f"[AIGIE] SPAN_CREATE: id={self.session_span_id}, name=session, parent=None (trace root)")
            await aigie._buffer.add(EventType.SPAN_CREATE, session_span_data)

        return self.trace_id

    async def handle_session_end(
        self,
        turn_count: int,
        total_cost: float,
        error: Optional[str] = None,
    ) -> None:
        """
        Called when a ClaudeSDKClient session ends.

        Args:
            turn_count: Number of conversation turns
            total_cost: Total cost in USD
            error: Error message if session failed
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return

        end_time = _utc_now()
        success = error is None

        # Update session span with token data
        if self.session_span_id:
            session_tokens = self.total_input_tokens + self.total_output_tokens
            session_update = {
                'id': self.session_span_id,
                'trace_id': self.trace_id,  # Required for backend merge
                'name': 'session',  # Include name for race conditions
                'type': 'chain',  # Include type for race conditions
                'status': 'success' if success else 'failed',
                'output': {
                    'turn_count': turn_count,
                    'total_cost': total_cost,
                    'total_tokens': session_tokens,
                    'total_tool_calls': self.total_tool_calls,
                    'usage': {
                        'input_tokens': self.total_input_tokens,
                        'output_tokens': self.total_output_tokens,
                        'total_tokens': session_tokens,
                    },
                },
                'end_time': end_time.isoformat(),
                'prompt_tokens': self.total_input_tokens,
                'completion_tokens': self.total_output_tokens,
                'total_tokens': session_tokens,
                'total_cost': total_cost,
            }

            if error:
                session_update['error'] = error
                session_update['error_message'] = error

            if aigie._buffer:
                await aigie._buffer.add(EventType.SPAN_UPDATE, session_update)

        # Update trace with top-level token fields for backend aggregation
        update_data = {
            'id': self.trace_id,
            'status': 'success' if success else 'failed',
            'output': {
                'turn_count': turn_count,
                'total_cost': total_cost,
                'total_tokens': self.total_input_tokens + self.total_output_tokens,
                'total_tool_calls': self.total_tool_calls,
            },
            'end_time': end_time.isoformat(),
            # Top-level token/cost fields for backend aggregation display
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'prompt_tokens': self.total_input_tokens,
            'completion_tokens': self.total_output_tokens,
            'total_cost': total_cost,
        }

        if error:
            update_data['error'] = error
            update_data['error_message'] = error

        if aigie._buffer:
            logger.debug(f"[AIGIE] TRACE_UPDATE (session): id={self.trace_id}, total_tokens={update_data['total_tokens']}, cost={update_data['total_cost']}")
            await aigie._buffer.add(EventType.TRACE_UPDATE, update_data)

        # Complete any pending spans to ensure all have end_time
        await self.complete_pending_turn_spans()
        await self.complete_pending_tool_spans()
        await self.complete_pending_subagent_spans()

    async def handle_turn_start(
        self,
        turn_id: str,
        user_message: str,
        turn_number: Optional[int] = None,
    ) -> str:
        """
        Called when a conversation turn starts.

        Args:
            turn_id: Unique turn identifier
            user_message: The user's message
            turn_number: Turn number in the conversation (optional, uses session count if not provided)

        Returns:
            The span ID for this turn
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return ""

        # Use session context turn number if not provided
        if turn_number is None:
            if self._session_context:
                turn_number = self._session_context.increment_turn()
            else:
                self._local_total_turns += 1
                turn_number = self._local_total_turns
        else:
            # Update total_turns to match provided turn_number
            self.total_turns = turn_number

        span_id = str(uuid.uuid4())
        start_time = _utc_now()

        # Get parent span ID
        parent_id = self.session_span_id or self.query_span_id

        self.turn_map[turn_id] = {
            'spanId': span_id,
            'startTime': start_time,
            'turnNumber': turn_number,
        }

        span_data = {
            'id': span_id,
            'trace_id': self.trace_id,
            'parent_id': parent_id,
            'name': f'Turn {turn_number}',
            'type': 'chain',
            'input': {
                'user_message': user_message[:1000] if self.capture_messages else '[redacted]',
                'turn_number': turn_number,
            },
            'status': 'pending',
            'tags': self.tags or [],
            'metadata': {
                'turnId': turn_id,
                'turnNumber': turn_number,
                'framework': 'claude_agent_sdk',
            },
            'start_time': start_time.isoformat(),
            'created_at': start_time.isoformat(),
        }

        self._current_turn_span_id = span_id

        # Update session context current turn span ID and set as current parent
        if self._session_context:
            self._session_context.current_turn_span_id = span_id
            self._session_context.set_current_parent(span_id)

        if aigie._buffer:
            logger.debug(f"[AIGIE] SPAN_CREATE: id={span_id}, name=Turn {turn_number}, parent={parent_id}")
            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

        return span_id

    async def handle_turn_end(
        self,
        turn_id: str,
        output: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None,
        cost: float = 0.0,
        error: Optional[str] = None,
    ) -> None:
        """
        Called when a conversation turn completes.

        Args:
            turn_id: Unique turn identifier
            output: The assistant's response (optional)
            usage: Token usage for this turn
            cost: Cost for this turn
            error: Error message if turn failed
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        turn_data = self.turn_map.get(turn_id)
        if not turn_data:
            return

        end_time = _utc_now()
        duration = (end_time - turn_data['startTime']).total_seconds()

        # Update totals
        if usage:
            self.total_input_tokens += usage.get('input_tokens', 0)
            self.total_output_tokens += usage.get('output_tokens', 0)
        self.total_cost += cost

        # Determine status
        success = error is None

        update_data = {
            'id': turn_data['spanId'],
            'trace_id': self.trace_id,  # Required for backend merge
            'name': f"Turn {turn_data['turnNumber']}",  # Include name for race conditions
            'type': 'chain',  # Include type for race conditions
            'status': 'success' if success else 'error',
            'end_time': end_time.isoformat(),
            'duration_ns': int(duration * 1_000_000_000),
        }

        # Add output
        if output:
            update_data['output'] = {
                'assistant_message': output[:1000] if self.capture_messages else '[redacted]',
            }

        # Add error info
        if error:
            update_data['error'] = error
            update_data['error_message'] = error

        if usage:
            update_data['prompt_tokens'] = usage.get('input_tokens', 0)
            update_data['completion_tokens'] = usage.get('output_tokens', 0)
            update_data['total_tokens'] = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)

        if cost > 0:
            update_data['total_cost'] = cost

        if aigie._buffer:
            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

        del self.turn_map[turn_id]
        self._current_turn_span_id = None

        # Update session context - clear turn span and parent
        if self._session_context:
            self._session_context.current_turn_span_id = None
            # Revert parent to query span (if exists) since turn is done
            self._session_context.set_current_parent(self._current_query_span_id)

    async def handle_turn_error(self, turn_id: str, error: str) -> None:
        """Called when a turn encounters an error."""
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        turn_data = self.turn_map.get(turn_id)
        if not turn_data:
            return

        end_time = _utc_now()
        duration = (end_time - turn_data['startTime']).total_seconds()

        update_data = {
            'id': turn_data['spanId'],
            'trace_id': self.trace_id,  # Required for backend merge
            'name': f"Turn {turn_data['turnNumber']}",  # Include name for race conditions
            'type': 'chain',  # Include type for race conditions
            'status': 'failed',
            'error': error,
            'error_message': error,
            'end_time': end_time.isoformat(),
            'duration_ns': int(duration * 1_000_000_000),
        }

        if aigie._buffer:
            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

        del self.turn_map[turn_id]
        self._current_turn_span_id = None

        # Update session context - clear turn span and parent
        if self._session_context:
            self._session_context.current_turn_span_id = None
            # Revert parent to query span (if exists) since turn errored
            self._session_context.set_current_parent(self._current_query_span_id)

    async def handle_llm_response(
        self,
        message: Any,
        model: Optional[str] = None,
        response_index: int = 0,
        usage: Optional[Dict[str, int]] = None,
        cost: float = 0.0,
    ) -> str:
        """
        Called when an LLM response (AssistantMessage with text) is received.

        Creates a span for the reasoning/response step.

        Args:
            message: The AssistantMessage or similar message with text content
            model: The model name
            response_index: Index of this response in the conversation
            usage: Token usage for this response (optional)
            cost: Cost for this response (optional)

        Returns:
            The span ID for this LLM response
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return ""

        span_id = str(uuid.uuid4())
        start_time = _utc_now()

        # Get parent span ID from hierarchy
        parent_id = self._get_current_parent()

        # Extract text content from message
        text_content = ""
        if hasattr(message, 'content'):
            content = message.content
            if isinstance(content, str):
                text_content = content[:500]
            elif isinstance(content, list):
                for block in content:
                    if hasattr(block, 'text'):
                        text_content = block.text[:500]
                        break
                    elif hasattr(block, 'type') and block.type == 'text':
                        text_content = getattr(block, 'text', '')[:500]
                        break

        # Get model name
        model_name = model or getattr(message, 'model', None) or 'claude'
        model_short = _shorten_model_name(model_name)

        # Attribute tokens to current subagent if inside one
        if usage:
            current_subagent = self._get_current_subagent()
            if current_subagent:
                current_subagent['input_tokens'] = current_subagent.get('input_tokens', 0) + usage.get('input_tokens', 0)
                current_subagent['output_tokens'] = current_subagent.get('output_tokens', 0) + usage.get('output_tokens', 0)
                current_subagent['cost'] = current_subagent.get('cost', 0.0) + cost

        # Calculate depth for flow view ordering
        llm_depth = self._register_span_depth(span_id, parent_id)

        span_data = {
            'id': span_id,
            'trace_id': self.trace_id,
            'parent_id': parent_id,
            'name': 'LLM Response',  # Clean name without verbose model
            'type': 'llm',
            'input': {
                'response_index': response_index,
            },
            'output': {
                'text': text_content if self.capture_messages else '[redacted]',
            },
            'status': 'success',
            'tags': self.tags or [],
            'metadata': {
                'model': model_name,
                'model_short': model_short,
                'framework': 'claude_agent_sdk',
                'response_index': response_index,
                'depth': llm_depth,
            },
            'depth': llm_depth,  # For flow view ordering
            'model': model_name,
            'start_time': start_time.isoformat(),
            'end_time': start_time.isoformat(),  # Instant span
            'created_at': start_time.isoformat(),
        }

        if aigie._buffer:
            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

        # Record LLM response for drift detection (captures planning from first response)
        if text_content:
            self._drift_detector.record_llm_response(text_content, model_name)

        # Check for errors in LLM response
        detected_error = self._error_detector.detect_from_llm_response(message, model_name)
        if detected_error:
            self._detected_errors.append(detected_error)
            logger.warning(f"[AIGIE] LLM error detected: {detected_error.error_type.value} - {detected_error.message[:100]}")

        return span_id

    async def handle_message(
        self,
        message_type: str,
        content: Any,
        role: str = "assistant",
    ) -> None:
        """
        Called for each message in the stream.

        Args:
            message_type: Type of message (AssistantMessage, ToolUseBlock, etc.)
            content: Message content
            role: Message role (user, assistant, tool)
        """
        # This can be used for detailed message tracking if needed
        pass

    def set_parent_context(self, parent_tool_use_id: Optional[str]) -> None:
        """
        Set the current parent context for subagent hierarchy tracking.

        This is called when processing AssistantMessage with parent_tool_use_id
        to track which subagent context we're currently in. When we receive a message
        from a subagent, we need to set that subagent's span as the current parent
        so that tools and LLM responses are properly nested.

        Args:
            parent_tool_use_id: The parent tool use ID from the message
        """
        self._current_parent_tool_use_id = parent_tool_use_id
        logger.debug(f"[AIGIE] Set parent context: {parent_tool_use_id}")

        # If this is a subagent's tool_use_id, switch context to that subagent
        if parent_tool_use_id and parent_tool_use_id in self.subagent_map:
            subagent_data = self.subagent_map[parent_tool_use_id]
            subagent_span_id = subagent_data.get('spanId')
            if subagent_span_id:
                logger.debug(f"[AIGIE] Switching to subagent context: {subagent_span_id}")
                self._set_current_parent(subagent_span_id)

    async def handle_subagent_spawn(
        self,
        tool_use_id: str,
        subagent_type: str,
        description: str,
        prompt: str,
        override_parent_id: Optional[str] = None,
        is_parallel: bool = False,
    ) -> str:
        """
        Called when a Task tool is used to spawn a subagent.

        Creates a span for the subagent execution and sets it as the new parent
        for nested tool calls.

        Args:
            tool_use_id: The tool_use_id of the Task tool
            subagent_type: Type of subagent (e.g., 'researcher', 'report-writer')
            description: Brief description of the subagent task
            prompt: The prompt given to the subagent
            override_parent_id: Optional explicit parent ID for parallel subagent spawning
            is_parallel: If True, don't change current parent (parallel subagents)

        Returns:
            The span ID for this subagent
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return ""

        span_id = str(uuid.uuid4())
        start_time = _utc_now()

        # Use override parent if provided (for parallel subagent spawning),
        # otherwise get from current context
        parent_id = override_parent_id if override_parent_id else self._get_current_parent()

        # Format the subagent name nicely
        subagent_name = _format_subagent_name(subagent_type)

        # Record for drift detection (check if this is a retry)
        is_retry = any(
            sa.get('subagentType') == subagent_type and sa.get('description') == description
            for sa in self.subagent_map.values()
        )
        self._drift_detector.record_subagent_spawn(subagent_type, description, is_retry=is_retry)

        # Calculate depth for flow view ordering
        subagent_depth = self._register_span_depth(span_id, parent_id)

        # Initialize subagent tracking with token aggregation fields
        self.subagent_map[tool_use_id] = {
            'spanId': span_id,
            'parentId': parent_id,  # Store parent for restoration
            'startTime': start_time,
            'subagentType': subagent_type,
            'description': description,
            'depth': subagent_depth,
            # Token tracking for aggregation
            'input_tokens': 0,
            'output_tokens': 0,
            'cost': 0.0,
            'tool_count': 0,
        }

        span_data = {
            'id': span_id,
            'trace_id': self.trace_id,
            'parent_id': parent_id,
            'name': subagent_name,  # Clean name like "Researcher", "Data Analyst"
            'type': 'agent',
            'input': {
                'subagent_type': subagent_type,
                'description': description,
                'prompt': prompt[:2000] if self.capture_messages else '[redacted]',
            },
            'status': 'running',
            'tags': [*self.tags, f'subagent:{subagent_type}'],
            'metadata': {
                'subagentType': subagent_type,
                'toolUseId': tool_use_id,
                'framework': 'claude_agent_sdk',
                'description': description,
                'depth': subagent_depth,
            },
            'depth': subagent_depth,  # For flow view ordering
            'start_time': start_time.isoformat(),
            'created_at': start_time.isoformat(),
        }

        if aigie._buffer:
            logger.debug(f"[AIGIE] SPAN_CREATE: id={span_id}, name={subagent_name}, parent={parent_id}, is_parallel={is_parallel}")
            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

        # NEVER change the current parent when spawning subagents.
        # The parent context should ONLY be set when we receive messages FROM the subagent
        # (via set_parent_context with parent_tool_use_id).
        # This prevents cascading when subagents are spawned in separate messages.
        #
        # Old behavior (caused cascading):
        #   if not is_parallel:
        #       self._set_current_parent(span_id)
        #
        # New behavior: Don't change parent context when spawning.
        # Context is only switched when processing messages FROM subagents.

        return span_id

    async def handle_subagent_end(
        self,
        tool_use_id: str,
        result: Any,
        is_error: bool = False,
    ) -> None:
        """
        Called when a subagent completes execution.

        Restores the parent hierarchy and includes aggregated token/cost data.

        Args:
            tool_use_id: The tool_use_id of the Task tool
            result: Result from the subagent execution
            is_error: Whether the subagent execution failed
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        subagent_data = self.subagent_map.get(tool_use_id)
        if not subagent_data:
            return

        end_time = _utc_now()
        duration = (end_time - subagent_data['startTime']).total_seconds()
        duration_ms = duration * 1000

        # Format the subagent name nicely
        subagent_name = _format_subagent_name(subagent_data['subagentType'])
        tool_count = subagent_data.get('tool_count', 0)

        # Error detection - check subagent result for errors
        detected_error = self._error_detector.detect_from_subagent_result(
            subagent_type=subagent_data['subagentType'],
            tool_use_id=tool_use_id,
            result=result,
            is_error_flag=is_error,
            duration_ms=duration_ms,
            tool_count=tool_count,
        )

        # Update is_error if we detected an error in the result
        if detected_error and not is_error:
            is_error = True
            self._detected_errors.append(detected_error)
            logger.warning(f"[AIGIE] Error detected in subagent {subagent_name}: {detected_error.message[:100]}")

        # Record for drift detection
        self._drift_detector.record_subagent_end(subagent_data['subagentType'], tool_count)

        output_data = {}
        if self.capture_tool_results:
            if isinstance(result, str):
                output_data['result'] = result[:2000]
            elif hasattr(result, 'model_dump'):
                output_data['result'] = str(result.model_dump())[:2000]
            else:
                output_data['result'] = str(result)[:2000]
        output_data['is_error'] = is_error
        output_data['status'] = 'error' if is_error else 'success'

        # Get accumulated token data
        input_tokens = subagent_data.get('input_tokens', 0)
        output_tokens = subagent_data.get('output_tokens', 0)
        total_tokens = input_tokens + output_tokens
        total_cost = subagent_data.get('cost', 0.0)

        # Add error details if detected
        error_metadata = {}
        if detected_error:
            error_metadata = {
                'error_type': detected_error.error_type.value,
                'error_severity': detected_error.severity.value,
                'error_is_transient': detected_error.is_transient,
            }

        update_data = {
            'id': subagent_data['spanId'],
            'trace_id': self.trace_id,
            'name': subagent_name,  # Clean name like "Researcher"
            'type': 'agent',
            'output': output_data,
            'status': 'error' if is_error else 'success',
            'is_error': is_error,  # Top-level for backend visibility
            'end_time': end_time.isoformat(),
            'duration_ns': int(duration * 1_000_000_000),
            # Include aggregated token/cost data
            'prompt_tokens': input_tokens,
            'completion_tokens': output_tokens,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'metadata': {
                'subagentType': subagent_data['subagentType'],
                'tool_count': tool_count,
                'duration_ms': int(duration_ms),
                'status': 'error' if is_error else 'success',
                **error_metadata,
            },
        }

        if is_error:
            update_data['error'] = str(result)[:500]
            update_data['error_message'] = str(result)[:500]
            if detected_error:
                update_data['error_type'] = detected_error.error_type.value

        if aigie._buffer:
            logger.debug(f"[AIGIE] SPAN_UPDATE: id={subagent_data['spanId']}, {subagent_name} completed, tokens={total_tokens}, cost=${total_cost:.4f}, status={'error' if is_error else 'success'}")
            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

        # Restore parent context based on stored parentId
        stored_parent = subagent_data.get('parentId')
        if stored_parent:
            self._set_current_parent(stored_parent)
        else:
            # Fallback to query/turn span
            self._set_current_parent(self._current_turn_span_id or self._current_query_span_id)

        del self.subagent_map[tool_use_id]

    def __repr__(self) -> str:
        return (
            f"ClaudeAgentSDKHandler("
            f"trace_id={self.trace_id}, "
            f"turns={self.total_turns}, "
            f"tool_calls={self.total_tool_calls}, "
            f"tokens={self.total_input_tokens + self.total_output_tokens}, "
            f"cost=${self.total_cost:.4f})"
        )
