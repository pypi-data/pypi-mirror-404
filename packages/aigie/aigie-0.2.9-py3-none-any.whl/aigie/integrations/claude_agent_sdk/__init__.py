"""
Claude Agent SDK integration for Aigie.

This module provides automatic tracing for the official Anthropic Claude Agent SDK,
capturing query execution, tool usage, and conversation sessions.

Usage:
    # Manual handler usage
    from aigie.integrations.claude_agent_sdk import ClaudeAgentSDKHandler

    handler = ClaudeAgentSDKHandler(trace_name="my-agent")
    # ... use with claude_agent_sdk

    # Auto-instrumentation
    from aigie.integrations.claude_agent_sdk import patch_claude_agent_sdk
    patch_claude_agent_sdk()  # Patches query(), ClaudeSDKClient, etc.

    # Explicit session scoping
    from aigie.integrations.claude_agent_sdk import claude_session

    with claude_session("My Agent"):
        await query("First question")
        await query("Follow-up")  # Shares same trace
"""

from .handler import ClaudeAgentSDKHandler
from .auto_instrument import (
    patch_claude_agent_sdk,
    unpatch_claude_agent_sdk,
    is_claude_agent_sdk_patched,
)
from .config import ClaudeAgentSDKConfig
from .cost_tracking import calculate_claude_cost, CLAUDE_MODEL_PRICING
from .session_context import (
    claude_session,
    get_session_context,
    get_or_create_session_context,
    clear_session_context,
    ClaudeSessionContext,
)

__all__ = [
    "ClaudeAgentSDKHandler",
    "ClaudeAgentSDKConfig",
    "patch_claude_agent_sdk",
    "unpatch_claude_agent_sdk",
    "is_claude_agent_sdk_patched",
    "calculate_claude_cost",
    "CLAUDE_MODEL_PRICING",
    # Session context API
    "claude_session",
    "get_session_context",
    "get_or_create_session_context",
    "clear_session_context",
    "ClaudeSessionContext",
]
