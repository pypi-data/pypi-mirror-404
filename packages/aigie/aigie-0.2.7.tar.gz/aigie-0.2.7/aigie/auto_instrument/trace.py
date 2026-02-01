"""
Automatic trace creation for workflows.

Provides utilities to automatically create traces when workflows start,
without requiring manual trace creation.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Context variable to track current trace
_current_trace: ContextVar[Optional[Any]] = ContextVar('_current_trace', default=None)

# Context variable to indicate we're in a callback-traced context (skip LLM auto-instrumentation)
_in_callback_context: ContextVar[bool] = ContextVar('_in_callback_context', default=False)


async def get_or_create_trace(
    name: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None
) -> Any:
    """
    Get current trace or create a new one if none exists.
    
    This is used by auto-instrumentation to ensure traces exist
    without requiring manual creation.
    
    Args:
        name: Trace name
        metadata: Optional metadata
        tags: Optional tags
    
    Returns:
        TraceContext instance
    """
    from ..client import get_aigie
    
    # Check if we already have a trace in context
    current = _current_trace.get()
    if current:
        return current
    
    # Get global aigie instance
    aigie = get_aigie()
    if not aigie or not aigie._initialized:
        # No aigie instance, return None (instrumentation will skip)
        return None
    
    # Create new trace
    try:
        trace = aigie.trace(
            name=name,
            metadata=metadata or {},
            tags=tags or []
        )
        
        # Enter the trace context (it's an async context manager)
        trace_context = await trace.__aenter__()
        
        # Store in context variable
        _current_trace.set(trace_context)
        
        return trace_context
    except Exception as e:
        logger.warning(f"Failed to create auto-trace: {e}")
        return None


def get_current_trace() -> Optional[Any]:
    """Get the current trace from context."""
    return _current_trace.get()


def set_current_trace(trace: Optional[Any]) -> None:
    """Set the current trace in context."""
    _current_trace.set(trace)


def clear_current_trace() -> None:
    """Clear the current trace from context."""
    _current_trace.set(None)


def is_in_callback_context() -> bool:
    """Check if we're in a callback-traced context (LangChain/LangGraph callbacks are handling tracing)."""
    return _in_callback_context.get()


def set_callback_context(active: bool) -> None:
    """Set whether we're in a callback-traced context."""
    _in_callback_context.set(active)


def get_or_create_trace_sync(
    name: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None
) -> Any:
    """
    Synchronous version of get_or_create_trace.

    This handles sync contexts by running async code in a new event loop
    if needed, or reusing existing loop if available.

    Args:
        name: Trace name
        metadata: Optional metadata
        tags: Optional tags

    Returns:
        TraceContext instance or None
    """
    from uuid import uuid4
    from ..client import get_aigie

    # Check if we already have a trace in context
    current = _current_trace.get()
    if current:
        return current

    # Get global aigie instance
    aigie = get_aigie()
    if not aigie or not aigie._initialized:
        return None

    # Try to get trace synchronously
    try:
        # Check if we're in an async context
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        if loop:
            # We're in an async context - use synchronous trace initialization
            # Create trace object
            trace = aigie.trace(
                name=name,
                metadata=metadata or {},
                tags=tags or []
            )

            # Initialize the trace synchronously (what __aenter__ does)
            # 1. Generate trace ID
            if not trace.id:
                trace.id = str(uuid4())

            # 2. Set as current trace
            _current_trace.set(trace)

            # 3. Schedule trace creation in the running event loop
            # Use create_task to send the trace start event without blocking
            async def _send_trace_start():
                try:
                    # Prepare and send trace start payload (similar to __aenter__)
                    enriched_metadata = dict(trace.metadata)
                    user_id = enriched_metadata.get("user_id") or enriched_metadata.get("userId")
                    session_id = enriched_metadata.get("session_id") or enriched_metadata.get("sessionId")
                    environment = enriched_metadata.get("environment") or enriched_metadata.get("env", "default")

                    payload = {
                        "id": trace.id,
                        "name": trace.name,
                        "status": "running",
                        "metadata": enriched_metadata,
                        "tags": trace.tags,
                        "spans": []
                    }

                    if user_id:
                        payload["user_id"] = user_id
                    if session_id:
                        payload["session_id"] = session_id
                    if environment:
                        payload["environment"] = environment

                    # Send via buffer or direct
                    if trace.buffer:
                        trace.buffer.add({
                            "type": "trace_create",
                            "trace_id": trace.id,
                            "data": payload
                        })
                    else:
                        try:
                            await trace.client.post(
                                f"{trace.api_url}/traces",
                                json=payload
                            )
                        except Exception as e:
                            logger.debug(f"Failed to send trace start: {e}")
                except Exception as e:
                    logger.debug(f"Error in _send_trace_start: {e}")

            # Schedule but don't await (fire-and-forget)
            loop.create_task(_send_trace_start())

            return trace

        # No running loop - we can create one
        return asyncio.run(get_or_create_trace(name, metadata, tags))
    except Exception as e:
        logger.warning(f"Failed to create sync trace: {e}")
        return None

