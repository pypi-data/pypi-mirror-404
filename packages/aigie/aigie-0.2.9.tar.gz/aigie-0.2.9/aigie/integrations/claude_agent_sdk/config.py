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
        query_timeout: Timeout in seconds for query operations
        llm_timeout: Timeout in seconds for LLM calls
        tool_timeout: Timeout in seconds for tool executions
        max_retries: Maximum number of retries for failed operations
        retry_delay: Initial delay between retries in seconds (exponential backoff)
        retry_on_errors: List of error types to retry on (empty = retry all transient)
    """

    enabled: bool = True
    capture_tool_results: bool = True
    capture_messages: bool = True
    redact_pii: bool = False
    max_message_length: int = 2000
    max_tool_result_length: int = 1000

    # Timeout settings (in seconds)
    query_timeout: float = 300.0  # 5 minutes for query operations
    llm_timeout: float = 120.0  # 2 minutes for LLM calls
    tool_timeout: float = 60.0  # 1 minute for tools

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0  # Initial delay, doubles each retry
    retry_on_errors: list = None  # Empty = retry all transient errors

    def __post_init__(self):
        """Validate configuration."""
        if self.retry_on_errors is None:
            self.retry_on_errors = []
        if self.max_message_length < 100:
            raise ValueError("max_message_length must be at least 100")
        if self.max_tool_result_length < 100:
            raise ValueError("max_tool_result_length must be at least 100")
        if self.query_timeout <= 0:
            raise ValueError("query_timeout must be positive")
        if self.llm_timeout <= 0:
            raise ValueError("llm_timeout must be positive")
        if self.tool_timeout <= 0:
            raise ValueError("tool_timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")

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
            AIGIE_CLAUDE_QUERY_TIMEOUT: Query timeout in seconds (default: 300)
            AIGIE_CLAUDE_LLM_TIMEOUT: LLM timeout in seconds (default: 120)
            AIGIE_CLAUDE_TOOL_TIMEOUT: Tool timeout in seconds (default: 60)
            AIGIE_CLAUDE_MAX_RETRIES: Max retry attempts (default: 3)
            AIGIE_CLAUDE_RETRY_DELAY: Initial retry delay in seconds (default: 1.0)
        """
        return cls(
            enabled=os.getenv("AIGIE_CLAUDE_ENABLED", "true").lower() == "true",
            capture_tool_results=os.getenv("AIGIE_CLAUDE_CAPTURE_TOOLS", "true").lower() == "true",
            capture_messages=os.getenv("AIGIE_CLAUDE_CAPTURE_MESSAGES", "true").lower() == "true",
            redact_pii=os.getenv("AIGIE_CLAUDE_REDACT_PII", "false").lower() == "true",
            max_message_length=int(os.getenv("AIGIE_CLAUDE_MAX_MESSAGE_LENGTH", "2000")),
            max_tool_result_length=int(os.getenv("AIGIE_CLAUDE_MAX_TOOL_RESULT_LENGTH", "1000")),
            query_timeout=float(os.getenv("AIGIE_CLAUDE_QUERY_TIMEOUT", "300.0")),
            llm_timeout=float(os.getenv("AIGIE_CLAUDE_LLM_TIMEOUT", "120.0")),
            tool_timeout=float(os.getenv("AIGIE_CLAUDE_TOOL_TIMEOUT", "60.0")),
            max_retries=int(os.getenv("AIGIE_CLAUDE_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("AIGIE_CLAUDE_RETRY_DELAY", "1.0")),
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
            query_timeout=overrides.get("query_timeout", self.query_timeout),
            llm_timeout=overrides.get("llm_timeout", self.llm_timeout),
            tool_timeout=overrides.get("tool_timeout", self.tool_timeout),
            max_retries=overrides.get("max_retries", self.max_retries),
            retry_delay=overrides.get("retry_delay", self.retry_delay),
            retry_on_errors=overrides.get("retry_on_errors", self.retry_on_errors),
        )
