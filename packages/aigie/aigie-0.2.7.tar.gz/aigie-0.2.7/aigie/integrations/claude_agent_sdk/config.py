"""
Configuration for Claude Agent SDK integration.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ClaudeAgentSDKConfig:
    """
    Configuration for Claude Agent SDK integration.

    Attributes:
        enabled: Whether tracing is enabled
        capture_tool_results: Whether to capture tool execution results
        capture_messages: Whether to capture message content
        redact_pii: Whether to redact PII from traces
        max_message_length: Maximum length of captured messages
        max_tool_result_length: Maximum length of captured tool results
    """

    enabled: bool = True
    capture_tool_results: bool = True
    capture_messages: bool = True
    redact_pii: bool = False
    max_message_length: int = 2000
    max_tool_result_length: int = 1000

    @classmethod
    def from_env(cls) -> "ClaudeAgentSDKConfig":
        """
        Create configuration from environment variables.

        Environment variables:
            AIGIE_CLAUDE_ENABLED: Enable/disable tracing (default: true)
            AIGIE_CLAUDE_CAPTURE_TOOLS: Capture tool results (default: true)
            AIGIE_CLAUDE_CAPTURE_MESSAGES: Capture messages (default: true)
            AIGIE_CLAUDE_REDACT_PII: Redact PII (default: false)
            AIGIE_CLAUDE_MAX_MESSAGE_LENGTH: Max message length (default: 2000)
            AIGIE_CLAUDE_MAX_TOOL_RESULT_LENGTH: Max tool result length (default: 1000)
        """
        return cls(
            enabled=os.getenv("AIGIE_CLAUDE_ENABLED", "true").lower() == "true",
            capture_tool_results=os.getenv("AIGIE_CLAUDE_CAPTURE_TOOLS", "true").lower() == "true",
            capture_messages=os.getenv("AIGIE_CLAUDE_CAPTURE_MESSAGES", "true").lower() == "true",
            redact_pii=os.getenv("AIGIE_CLAUDE_REDACT_PII", "false").lower() == "true",
            max_message_length=int(os.getenv("AIGIE_CLAUDE_MAX_MESSAGE_LENGTH", "2000")),
            max_tool_result_length=int(os.getenv("AIGIE_CLAUDE_MAX_TOOL_RESULT_LENGTH", "1000")),
        )

    def merge(self, **overrides) -> "ClaudeAgentSDKConfig":
        """
        Create a new config with overridden values.

        Args:
            **overrides: Values to override

        Returns:
            New ClaudeAgentSDKConfig with overrides applied
        """
        return ClaudeAgentSDKConfig(
            enabled=overrides.get("enabled", self.enabled),
            capture_tool_results=overrides.get("capture_tool_results", self.capture_tool_results),
            capture_messages=overrides.get("capture_messages", self.capture_messages),
            redact_pii=overrides.get("redact_pii", self.redact_pii),
            max_message_length=overrides.get("max_message_length", self.max_message_length),
            max_tool_result_length=overrides.get("max_tool_result_length", self.max_tool_result_length),
        )
