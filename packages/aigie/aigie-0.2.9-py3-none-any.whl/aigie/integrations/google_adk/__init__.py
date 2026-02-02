"""
Google ADK integration for Aigie.

This module provides automatic tracing for Google ADK (Agent Development Kit),
capturing agent invocations, tool calls, LLM calls, and events.

Usage:
    # Manual handler usage
    from google.adk import Runner, LlmAgent
    from aigie.integrations.google_adk import GoogleADKHandler

    handler = GoogleADKHandler(trace_name="my-agent")
    # Use handler methods in custom callbacks

    # Plugin-based usage (recommended)
    from google.adk import Runner, LlmAgent
    from aigie.integrations.google_adk import AigiePlugin

    plugin = AigiePlugin(trace_name="my-agent")
    runner = Runner(agent=agent, session_service=..., plugins=[plugin])

    # Auto-instrumentation
    from aigie.integrations.google_adk import patch_google_adk
    patch_google_adk()  # Patches Runner to auto-inject AigiePlugin

    # Now all runners are automatically traced
    runner = Runner(agent=agent, session_service=...)
"""

from .handler import GoogleADKHandler
from .plugin import AigiePlugin
from .auto_instrument import (
    patch_google_adk,
    unpatch_google_adk,
    is_google_adk_patched,
)
from .config import GoogleADKConfig
from .cost_tracking import (
    calculate_google_adk_cost,
    get_model_pricing,
    GEMINI_MODEL_PRICING,
)
from .session import (
    GoogleADKSessionContext,
    google_adk_session,
    get_session_context,
    set_session_context,
    get_or_create_session_context,
    clear_session_context,
)

__all__ = [
    "GoogleADKHandler",
    "AigiePlugin",
    "GoogleADKConfig",
    "patch_google_adk",
    "unpatch_google_adk",
    "is_google_adk_patched",
    "calculate_google_adk_cost",
    "get_model_pricing",
    "GEMINI_MODEL_PRICING",
    # Session context API
    "GoogleADKSessionContext",
    "google_adk_session",
    "get_session_context",
    "set_session_context",
    "get_or_create_session_context",
    "clear_session_context",
]
