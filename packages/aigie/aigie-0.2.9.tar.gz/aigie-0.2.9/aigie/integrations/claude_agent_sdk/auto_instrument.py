"""
Claude Agent SDK auto-instrumentation.

Automatically patches Claude Agent SDK functions to create traces and inject handlers.
"""

import functools
import logging
import re
from typing import Any, Dict, Optional, Set

from .session_context import (
    get_or_create_session_context,
    get_session_context,
    clear_session_context,
    ClaudeSessionContext,
)

logger = logging.getLogger(__name__)


def _extract_agent_name(system_prompt: str, model: str) -> str:
    """
    Extract a descriptive agent name from system prompt or fall back to model name.

    Looks for patterns like "You are a researcher" or "You are an expert analyst".

    Args:
        system_prompt: The system prompt given to the agent
        model: The model being used

    Returns:
        A descriptive name for the trace
    """
    if system_prompt:
        # Look for "You are a/an [role]" pattern
        match = re.search(r'You are (?:a |an |the )?([^.!\n]+)', system_prompt, re.IGNORECASE)
        if match:
            role = match.group(1).strip()
            # Remove trailing relative clauses (who, that, which, and their content)
            role = re.sub(r'\s+(?:who|that|which)\s+.*$', '', role, flags=re.IGNORECASE)
            # If role is still too long, take just the first 4 words
            words = role.split()
            if len(words) > 4:
                role = ' '.join(words[:4])
            # Clean up and capitalize
            if role:
                return role.title()

    # Fall back to model-based name
    return _shorten_model_name(model) + " Agent"


def _shorten_model_name(model: str) -> str:
    """Convert full model name to short display name."""
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

_patched_functions: Set[str] = set()
_original_functions: Dict[str, Any] = {}


def patch_claude_agent_sdk() -> bool:
    """
    Patch Claude Agent SDK functions for auto-instrumentation.

    This patches:
    - claude_agent_sdk.query() for stateless queries
    - ClaudeSDKClient.query() for stateful client queries
    - ClaudeSDKClient.connect() for WebSocket connections

    Returns:
        True if patching was successful (or already patched)
    """
    success = True
    success = _patch_query_function() and success
    success = _patch_client_query() and success
    success = _patch_client_connect() and success
    success = _patch_receive_response() and success
    return success


def unpatch_claude_agent_sdk() -> None:
    """Remove Claude Agent SDK patches (for testing)."""
    global _patched_functions, _original_functions

    try:
        import claude_agent_sdk

        if 'query' in _original_functions:
            claude_agent_sdk.query = _original_functions['query']

        if 'ClaudeSDKClient.query' in _original_functions:
            from claude_agent_sdk import ClaudeSDKClient
            ClaudeSDKClient.query = _original_functions['ClaudeSDKClient.query']

        if 'ClaudeSDKClient.connect' in _original_functions:
            from claude_agent_sdk import ClaudeSDKClient
            ClaudeSDKClient.connect = _original_functions['ClaudeSDKClient.connect']

    except ImportError:
        pass

    _patched_functions.clear()
    _original_functions.clear()


def is_claude_agent_sdk_patched() -> bool:
    """Check if Claude Agent SDK has been patched."""
    return len(_patched_functions) > 0


def _patch_query_function() -> bool:
    """Patch the standalone query() function."""
    try:
        import claude_agent_sdk

        if 'query' in _patched_functions:
            return True

        original_query = claude_agent_sdk.query
        _original_functions['query'] = original_query

        @functools.wraps(original_query)
        async def traced_query(*, prompt: str, **kwargs):
            """Traced version of claude_agent_sdk.query()."""
            from ...client import get_aigie
            from .handler import ClaudeAgentSDKHandler
            from .config import ClaudeAgentSDKConfig

            aigie = get_aigie()
            config = ClaudeAgentSDKConfig.from_env()

            if aigie and aigie._initialized and config.enabled:
                prompt_str = prompt if isinstance(prompt, str) else "<async_input>"

                # Check if we're already in a session scope (e.g., claude_session context manager)
                existing_ctx = get_session_context()
                owns_context = existing_ctx is None

                # Extract model from kwargs
                model = kwargs.get('model', 'claude-sonnet-4-20250514')

                # Extract agent name from system prompt or use model-based name
                system_prompt = kwargs.get('system_prompt', '')
                trace_name = _extract_agent_name(system_prompt, model)

                # Get or create session context - reuse existing trace if in a session
                session_ctx = get_or_create_session_context(trace_name=trace_name)

                handler = ClaudeAgentSDKHandler(
                    trace_name=trace_name,
                    metadata={'prompt_preview': prompt_str[:100] if isinstance(prompt_str, str) else ""},
                    capture_tool_results=config.capture_tool_results,
                    capture_messages=config.capture_messages,
                    session_context=session_ctx,
                )
                handler._aigie = aigie

                # Build options from kwargs
                options = {
                    'model': model,
                    'tools': kwargs.get('tools', []),
                    'system_prompt': kwargs.get('system_prompt', ''),
                    'max_tokens': kwargs.get('max_tokens'),
                    'max_turns': kwargs.get('max_turns'),
                }

                query_id = await handler.handle_query_start(prompt, options, model)

                # Collect messages from the generator
                messages = []
                result_message = None
                error_msg = None
                response_index = 0

                try:
                    async for message in original_query(prompt=prompt, **kwargs):
                        messages.append(message)

                        # Get message type name for detection
                        msg_type = type(message).__name__

                        # Create LLM span for AssistantMessage with text content
                        # Note: AssistantMessage doesn't have .role, we check by type name
                        if msg_type == 'AssistantMessage' and hasattr(message, 'content'):
                            content = message.content
                            has_text = False
                            if isinstance(content, str) and content:
                                has_text = True
                            elif isinstance(content, list):
                                for block in content:
                                    # TextBlock has .text but no .type attribute
                                    if hasattr(block, 'text') and block.text:
                                        has_text = True
                                        break
                            if has_text:
                                await handler.handle_llm_response(message, model, response_index)
                                response_index += 1

                        # Track tool usage from content blocks
                        # Note: ToolUseBlock/ToolResultBlock don't have .type, check class name
                        if hasattr(message, 'content') and isinstance(message.content, list):
                            # IMPORTANT: For parallel subagent spawning, we need to process all
                            # Task tools with the SAME parent. Collect them first, then process.
                            task_tools = []
                            other_tool_uses = []
                            tool_results = []

                            for block in message.content:
                                block_class = type(block).__name__
                                logger.debug(f"[AIGIE] Block detected: {block_class}")

                                if block_class == 'ToolUseBlock':
                                    tool_name = getattr(block, 'name', 'unknown')
                                    if tool_name == 'Task':
                                        task_tools.append(block)
                                    else:
                                        other_tool_uses.append(block)
                                elif block_class == 'ToolResultBlock':
                                    tool_results.append(block)

                            # Track parent context from AssistantMessage (for subagent hierarchy)
                            # CRITICAL: If this message is from a subagent, switch context FIRST
                            # so that any nested subagents spawned here get the correct parent
                            parent_tool_use_id = getattr(message, 'parent_tool_use_id', None)
                            if parent_tool_use_id:
                                logger.debug(f"[AIGIE] Message has parent_tool_use_id: {parent_tool_use_id}")
                                handler.set_parent_context(parent_tool_use_id)

                            # NOW get batch_parent (which will be correct subagent span if inside one)
                            # All parallel subagents in this message should have this same parent
                            batch_parent = handler._get_current_parent()
                            logger.debug(f"[AIGIE] Batch parent for {len(task_tools)} Task tools: {batch_parent}")

                            # Process all Task tools (subagents) with the same parent
                            # If there are multiple Task tools in one message, they're parallel
                            is_parallel = len(task_tools) > 1
                            for block in task_tools:
                                tool_use_id = getattr(block, 'id', str(len(handler.subagent_map)))
                                tool_input = getattr(block, 'input', {})
                                subagent_type = tool_input.get('subagent_type', 'unknown')
                                description = tool_input.get('description', '')
                                subagent_prompt = tool_input.get('prompt', '')
                                logger.debug(f"[AIGIE] Creating subagent span: {subagent_type} ({tool_use_id}), parent={batch_parent}, is_parallel={is_parallel}")

                                # Pass batch_parent explicitly to ensure all parallel subagents
                                # have the same parent, bypassing any state changes
                                await handler.handle_subagent_spawn(
                                    tool_use_id, subagent_type, description, subagent_prompt,
                                    override_parent_id=batch_parent,
                                    is_parallel=is_parallel,
                                )

                            # Process other tool uses
                            for block in other_tool_uses:
                                tool_use_id = getattr(block, 'id', str(len(handler.tool_map)))
                                tool_name = getattr(block, 'name', 'unknown')
                                tool_input = getattr(block, 'input', {})
                                logger.debug(f"[AIGIE] Creating tool span: {tool_name} ({tool_use_id}), parent_tool_use_id={parent_tool_use_id}")
                                await handler.handle_tool_use_start(
                                    tool_name, tool_input, tool_use_id,
                                    parent_tool_use_id=parent_tool_use_id,
                                )

                            # Process tool results
                            for block in tool_results:
                                tool_use_id = getattr(block, 'tool_use_id', '')
                                content = getattr(block, 'content', '')
                                is_error = getattr(block, 'is_error', False)
                                # Check both tool_map and subagent_map
                                if tool_use_id and tool_use_id in handler.tool_map:
                                    await handler.handle_tool_use_end(
                                        tool_use_id, content, is_error
                                    )
                                elif tool_use_id and tool_use_id in handler.subagent_map:
                                    await handler.handle_subagent_end(
                                        tool_use_id, content, is_error
                                    )

                        # Check for ResultMessage (final message with usage/cost)
                        if hasattr(message, 'usage') or hasattr(message, 'total_cost_usd'):
                            result_message = message

                        yield message

                except Exception as e:
                    error_msg = str(e)
                    raise
                finally:
                    # Complete any pending tool and subagent spans first
                    await handler.complete_pending_tool_spans()
                    await handler.complete_pending_subagent_spans()
                    # Then end the query
                    await handler.handle_query_end(
                        query_id, messages, result_message, error_msg
                    )
                    # Clear session context if this query created it
                    # This ensures each standalone query() gets its own trace
                    if owns_context:
                        clear_session_context()

            else:
                # No tracing, just yield through
                async for message in original_query(prompt=prompt, **kwargs):
                    yield message

        claude_agent_sdk.query = traced_query
        _patched_functions.add('query')

        logger.debug("Patched claude_agent_sdk.query for auto-instrumentation")
        return True

    except ImportError:
        logger.debug("claude_agent_sdk not installed, skipping query patch")
        return True  # Not an error if not installed
    except Exception as e:
        logger.warning(f"Failed to patch claude_agent_sdk.query: {e}")
        return False


def _patch_client_query() -> bool:
    """Patch ClaudeSDKClient.query() method.

    Note: ClaudeSDKClient.query() returns None and sends a message.
    Messages are received via receive_messages() or receive_response().
    We just trace the call itself here.
    """
    try:
        from claude_agent_sdk import ClaudeSDKClient

        if 'ClaudeSDKClient.query' in _patched_functions:
            return True

        original_query = ClaudeSDKClient.query
        _original_functions['ClaudeSDKClient.query'] = original_query

        @functools.wraps(original_query)
        async def traced_client_query(self, prompt, session_id: str = 'default'):
            """Traced version of ClaudeSDKClient.query()."""
            from ...client import get_aigie
            from .handler import ClaudeAgentSDKHandler
            from .config import ClaudeAgentSDKConfig

            aigie = get_aigie()
            config = ClaudeAgentSDKConfig.from_env()

            if aigie and aigie._initialized and config.enabled:
                # Get model and system_prompt from client options
                client_options = getattr(self, 'options', None)
                model = getattr(client_options, 'model', None) or getattr(self, 'model', 'claude-sonnet-4-20250514')
                system_prompt = getattr(client_options, 'system_prompt', '') or ''

                # Extract agent name from system prompt if available
                trace_name = _extract_agent_name(system_prompt, model) if system_prompt else f"{_shorten_model_name(model)} Client Session"

                # Get or create session context - reuse existing trace
                session_ctx = get_or_create_session_context(trace_name=trace_name)

                # Get or create handler with session context
                handler = getattr(self, '_aigie_handler', None)
                if handler is None:
                    handler = ClaudeAgentSDKHandler(
                        trace_name=trace_name,
                        capture_tool_results=config.capture_tool_results,
                        capture_messages=config.capture_messages,
                        session_context=session_ctx,
                    )
                    handler._aigie = aigie
                    self._aigie_handler = handler
                prompt_str = prompt if isinstance(prompt, str) else "<async_input>"

                # Generate turn ID
                import uuid
                turn_id = str(uuid.uuid4())

                # Start a turn for this query - turn number comes from session context
                await handler.handle_turn_start(turn_id, prompt_str)

                # Store the turn_id for later completion
                if not hasattr(self, '_pending_turn_ids'):
                    self._pending_turn_ids = []
                self._pending_turn_ids.append(turn_id)

                try:
                    # Call original - returns None (sends message)
                    result = await original_query(self, prompt, session_id)
                    return result
                except Exception as e:
                    # Remove from pending and complete with error
                    if turn_id in self._pending_turn_ids:
                        self._pending_turn_ids.remove(turn_id)
                    await handler.handle_turn_end(turn_id, error=str(e))
                    raise
            else:
                return await original_query(self, prompt, session_id)

        ClaudeSDKClient.query = traced_client_query
        _patched_functions.add('ClaudeSDKClient.query')

        logger.debug("Patched ClaudeSDKClient.query for auto-instrumentation")
        return True

    except ImportError:
        logger.debug("claude_agent_sdk not installed, skipping client query patch")
        return True
    except Exception as e:
        logger.warning(f"Failed to patch ClaudeSDKClient.query: {e}")
        return False


def _patch_client_connect() -> bool:
    """Patch ClaudeSDKClient.connect() for WebSocket sessions."""
    try:
        from claude_agent_sdk import ClaudeSDKClient

        if 'ClaudeSDKClient.connect' in _patched_functions:
            return True

        # Check if connect method exists (may not exist in all versions)
        if not hasattr(ClaudeSDKClient, 'connect'):
            logger.debug("ClaudeSDKClient.connect not found, skipping patch")
            return True

        original_connect = ClaudeSDKClient.connect
        _original_functions['ClaudeSDKClient.connect'] = original_connect

        @functools.wraps(original_connect)
        async def traced_connect(self, *args, **kwargs):
            """Traced version of ClaudeSDKClient.connect()."""
            from ...client import get_aigie
            from .handler import ClaudeAgentSDKHandler
            from .config import ClaudeAgentSDKConfig

            aigie = get_aigie()
            config = ClaudeAgentSDKConfig.from_env()

            if aigie and aigie._initialized and config.enabled:
                # Check if we're already in an explicit session scope (e.g., claude_session context manager)
                existing_ctx = get_session_context()
                owns_context = existing_ctx is None

                # Get model and system_prompt from client options
                client_options = getattr(self, 'options', None)
                model = getattr(client_options, 'model', None) or getattr(self, 'model', 'claude-sonnet-4-20250514')
                system_prompt = getattr(client_options, 'system_prompt', '') or ''

                # Extract agent name from system prompt if available
                trace_name = _extract_agent_name(system_prompt, model) if system_prompt else f"{_shorten_model_name(model)} Session"

                if owns_context:
                    # Create new session context for this connection
                    session_ctx = get_or_create_session_context(trace_name=trace_name)
                else:
                    # Reuse existing session context - this connection is part of a larger session
                    session_ctx = existing_ctx

                # Track whether this connection owns the context
                self._owns_session_context = owns_context

                handler = ClaudeAgentSDKHandler(
                    trace_name=trace_name,
                    capture_tool_results=config.capture_tool_results,
                    capture_messages=config.capture_messages,
                    session_context=session_ctx,
                )
                handler._aigie = aigie
                self._aigie_handler = handler

                options = {
                    'model': model,
                }

                await handler.handle_session_start(self, options)

                try:
                    result = await original_connect(self, *args, **kwargs)
                    return result
                except Exception as e:
                    await handler.handle_session_end(
                        handler.total_turns,
                        handler.total_cost,
                        str(e)
                    )
                    raise
            else:
                return await original_connect(self, *args, **kwargs)

        ClaudeSDKClient.connect = traced_connect
        _patched_functions.add('ClaudeSDKClient.connect')

        # Also patch __aexit__ to properly end sessions
        if hasattr(ClaudeSDKClient, '__aexit__'):
            original_aexit = ClaudeSDKClient.__aexit__
            _original_functions['ClaudeSDKClient.__aexit__'] = original_aexit

            @functools.wraps(original_aexit)
            async def traced_aexit(self, exc_type, exc_val, exc_tb):
                """Traced version of ClaudeSDKClient.__aexit__()."""
                handler = getattr(self, '_aigie_handler', None)
                if handler:
                    error = str(exc_val) if exc_val else None
                    await handler.handle_session_end(
                        handler.total_turns,
                        handler.total_cost,
                        error
                    )
                # Only clear session context if this connection created it
                # This preserves context for operations that share a session scope
                if getattr(self, '_owns_session_context', True):
                    clear_session_context()
                return await original_aexit(self, exc_type, exc_val, exc_tb)

            ClaudeSDKClient.__aexit__ = traced_aexit
            _patched_functions.add('ClaudeSDKClient.__aexit__')

        logger.debug("Patched ClaudeSDKClient.connect for auto-instrumentation")
        return True

    except ImportError:
        logger.debug("claude_agent_sdk not installed, skipping connect patch")
        return True
    except Exception as e:
        logger.warning(f"Failed to patch ClaudeSDKClient.connect: {e}")
        return False


def _patch_receive_response() -> bool:
    """Patch ClaudeSDKClient.receive_response() to complete turns and track tools/subagents."""
    try:
        from claude_agent_sdk import ClaudeSDKClient

        if 'ClaudeSDKClient.receive_response' in _patched_functions:
            return True

        if not hasattr(ClaudeSDKClient, 'receive_response'):
            logger.debug("ClaudeSDKClient.receive_response not found, skipping patch")
            return True

        original_receive = ClaudeSDKClient.receive_response
        _original_functions['ClaudeSDKClient.receive_response'] = original_receive

        @functools.wraps(original_receive)
        async def traced_receive_response(self):
            """Traced version of ClaudeSDKClient.receive_response()."""
            from ...client import get_aigie

            handler = getattr(self, '_aigie_handler', None)
            pending_turn_ids = getattr(self, '_pending_turn_ids', [])

            # Collect all messages
            messages = []
            result_message = None
            error_msg = None
            response_index = 0

            try:
                async for message in original_receive(self):
                    messages.append(message)

                    # Get message type name for detection
                    msg_type = type(message).__name__

                    if handler:
                        # Create LLM span for AssistantMessage with text content
                        if msg_type == 'AssistantMessage' and hasattr(message, 'content'):
                            content = message.content
                            has_text = False
                            if isinstance(content, str) and content:
                                has_text = True
                            elif isinstance(content, list):
                                for block in content:
                                    if hasattr(block, 'text') and block.text:
                                        has_text = True
                                        break
                            if has_text:
                                model = getattr(self, 'model', 'claude-sonnet-4-20250514')
                                await handler.handle_llm_response(message, model, response_index)
                                response_index += 1

                        # Track tool usage and subagent spawning from content blocks
                        if hasattr(message, 'content') and isinstance(message.content, list):
                            # IMPORTANT: For parallel subagent spawning, we need to process all
                            # Task tools with the SAME parent. Collect them first, then process.
                            task_tools = []
                            other_tool_uses = []
                            tool_results = []

                            for block in message.content:
                                block_class = type(block).__name__
                                logger.debug(f"[AIGIE] Block detected (client): {block_class}")

                                if block_class == 'ToolUseBlock':
                                    tool_name = getattr(block, 'name', 'unknown')
                                    if tool_name == 'Task':
                                        task_tools.append(block)
                                    else:
                                        other_tool_uses.append(block)
                                elif block_class == 'ToolResultBlock':
                                    tool_results.append(block)

                            # Track parent context from AssistantMessage (for subagent hierarchy)
                            # CRITICAL: If this message is from a subagent, switch context FIRST
                            # so that any nested subagents spawned here get the correct parent
                            parent_tool_use_id = getattr(message, 'parent_tool_use_id', None)
                            if parent_tool_use_id:
                                logger.debug(f"[AIGIE] Message has parent_tool_use_id: {parent_tool_use_id}")
                                handler.set_parent_context(parent_tool_use_id)

                            # NOW get batch_parent (which will be correct subagent span if inside one)
                            # All parallel subagents in this message should have this same parent
                            batch_parent = handler._get_current_parent()
                            logger.debug(f"[AIGIE] Batch parent for {len(task_tools)} Task tools: {batch_parent}")

                            # Process all Task tools (subagents) with the same parent
                            # If there are multiple Task tools in one message, they're parallel
                            is_parallel = len(task_tools) > 1
                            for block in task_tools:
                                tool_use_id = getattr(block, 'id', str(len(handler.subagent_map)))
                                tool_input = getattr(block, 'input', {})
                                subagent_type = tool_input.get('subagent_type', 'unknown')
                                description = tool_input.get('description', '')
                                subagent_prompt = tool_input.get('prompt', '')
                                logger.debug(f"[AIGIE] Creating subagent span (client): {subagent_type} ({tool_use_id}), parent={batch_parent}, is_parallel={is_parallel}")

                                # Pass batch_parent explicitly to ensure all parallel subagents
                                # have the same parent, bypassing any state changes
                                await handler.handle_subagent_spawn(
                                    tool_use_id, subagent_type, description, subagent_prompt,
                                    override_parent_id=batch_parent,
                                    is_parallel=is_parallel,
                                )

                            # Process other tool uses
                            for block in other_tool_uses:
                                tool_use_id = getattr(block, 'id', str(len(handler.tool_map)))
                                tool_name = getattr(block, 'name', 'unknown')
                                tool_input = getattr(block, 'input', {})
                                logger.debug(f"[AIGIE] Creating tool span (client): {tool_name} ({tool_use_id}), parent_tool_use_id={parent_tool_use_id}")
                                await handler.handle_tool_use_start(
                                    tool_name, tool_input, tool_use_id,
                                    parent_tool_use_id=parent_tool_use_id,
                                )

                            # Process tool results
                            for block in tool_results:
                                tool_use_id = getattr(block, 'tool_use_id', '')
                                content = getattr(block, 'content', '')
                                is_error = getattr(block, 'is_error', False)
                                # Check both tool_map and subagent_map
                                if tool_use_id and tool_use_id in handler.tool_map:
                                    await handler.handle_tool_use_end(
                                        tool_use_id, content, is_error
                                    )
                                elif tool_use_id and tool_use_id in handler.subagent_map:
                                    await handler.handle_subagent_end(
                                        tool_use_id, content, is_error
                                    )

                    # Check for ResultMessage (final message with usage/cost)
                    if hasattr(message, 'usage') or hasattr(message, 'total_cost_usd'):
                        result_message = message

                    yield message

            except Exception as e:
                error_msg = str(e)
                raise
            finally:
                # Complete any pending tool and subagent spans first
                if handler:
                    await handler.complete_pending_tool_spans()
                    await handler.complete_pending_subagent_spans()

                # Complete ALL pending turns, not just the first
                if handler and pending_turn_ids:
                    # Process all pending turns
                    while pending_turn_ids:
                        turn_id = pending_turn_ids.pop(0)

                        # Extract output and usage from messages
                        output = None
                        usage = {}
                        cost = 0.0

                        if result_message:
                            if hasattr(result_message, 'usage'):
                                u = result_message.usage
                                # Handle both dict and object formats
                                if isinstance(u, dict):
                                    usage = {
                                        'input_tokens': u.get('input_tokens', 0),
                                        'output_tokens': u.get('output_tokens', 0),
                                    }
                                else:
                                    usage = {
                                        'input_tokens': getattr(u, 'input_tokens', 0),
                                        'output_tokens': getattr(u, 'output_tokens', 0),
                                    }
                            if hasattr(result_message, 'total_cost_usd'):
                                cost = result_message.total_cost_usd or 0.0

                        # Extract text output from messages
                        for msg in messages:
                            if hasattr(msg, 'content'):
                                content = msg.content
                                if isinstance(content, list):
                                    for block in content:
                                        if hasattr(block, 'text'):
                                            output = block.text[:2000]
                                            break

                        await handler.handle_turn_end(
                            turn_id,
                            output=output,
                            usage=usage,
                            cost=cost,
                            error=error_msg
                        )

        ClaudeSDKClient.receive_response = traced_receive_response
        _patched_functions.add('ClaudeSDKClient.receive_response')

        logger.debug("Patched ClaudeSDKClient.receive_response for auto-instrumentation")
        return True

    except ImportError:
        logger.debug("claude_agent_sdk not installed, skipping receive_response patch")
        return True
    except Exception as e:
        logger.warning(f"Failed to patch ClaudeSDKClient.receive_response: {e}")
        return False


def _patch_hooks() -> bool:
    """
    Patch hook registration for tool use tracking.

    This patches the hook system to automatically track:
    - PreToolUse: Called before a tool is executed
    - PostToolUse: Called after a tool execution completes
    - UserPromptSubmit: Called when user submits a prompt
    """
    # Hook patching is optional and depends on the SDK version
    # The main tracing happens through query/client patching
    return True
