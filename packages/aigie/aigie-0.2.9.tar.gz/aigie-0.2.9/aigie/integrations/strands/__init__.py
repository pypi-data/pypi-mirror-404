"""
Strands Agents integration for Aigie.

This module provides automatic tracing for Strands Agents, capturing
agent invocations, tool calls, LLM calls, and multi-agent orchestrations.

Usage:
    # Manual handler usage
    from strands import Agent
    from aigie.integrations.strands import StrandsHandler

    handler = StrandsHandler(trace_name="my-agent")
    agent = Agent(tools=[...], hooks=[handler])
    result = agent("What is the capital of France?")

    # Auto-instrumentation
    from aigie.integrations.strands import patch_strands
    patch_strands()  # Patches Agent.__init__ to auto-register handler

    # Now all agents are automatically traced
    agent = Agent(tools=[...])
    result = agent("What is the capital of France?")
"""

from .handler import StrandsHandler
from .auto_instrument import (
    patch_strands,
    unpatch_strands,
    is_strands_patched,
)
from .config import StrandsConfig
from .cost_tracking import (
    calculate_strands_cost,
    get_model_pricing,
    STRANDS_MODEL_PRICING,
)
from .session import (
    StrandsSessionContext,
    strands_session,
    get_session_context,
    set_session_context,
    get_or_create_session_context,
    clear_session_context,
)

__all__ = [
    "StrandsHandler",
    "StrandsConfig",
    "patch_strands",
    "unpatch_strands",
    "is_strands_patched",
    "calculate_strands_cost",
    "get_model_pricing",
    "STRANDS_MODEL_PRICING",
    # Session context API
    "StrandsSessionContext",
    "strands_session",
    "get_session_context",
    "set_session_context",
    "get_or_create_session_context",
    "clear_session_context",
]
