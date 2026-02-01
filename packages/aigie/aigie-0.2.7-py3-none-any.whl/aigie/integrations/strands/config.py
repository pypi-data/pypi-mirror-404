"""
Configuration for Strands Agents integration.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class StrandsConfig:
    """
    Configuration for Strands Agents integration.

    Attributes:
        enabled: Whether tracing is enabled
        trace_agents: Whether to trace agent invocations
        trace_tools: Whether to trace tool calls
        trace_llm_calls: Whether to trace LLM calls
        trace_multi_agent: Whether to trace multi-agent orchestrations
        trace_streaming: Whether to trace BidiAgent streaming events
        capture_inputs: Whether to capture input data
        capture_outputs: Whether to capture output data
        capture_messages: Whether to capture message content
        redact_pii: Whether to redact PII from traces
        max_content_length: Maximum length of captured content
        max_message_length: Maximum length of captured messages
        max_tool_result_length: Maximum length of captured tool results
    """

    enabled: bool = True
    trace_agents: bool = True
    trace_tools: bool = True
    trace_llm_calls: bool = True
    trace_multi_agent: bool = True
    trace_streaming: bool = False  # BidiAgent streaming support (disabled by default)
    capture_inputs: bool = True
    capture_outputs: bool = True
    capture_messages: bool = True
    redact_pii: bool = False
    max_content_length: int = 2000
    max_message_length: int = 2000
    max_tool_result_length: int = 1000

    @classmethod
    def from_env(cls) -> "StrandsConfig":
        """
        Create configuration from environment variables.

        Environment variables:
            AIGIE_STRANDS_ENABLED: Enable/disable tracing (default: true)
            AIGIE_STRANDS_TRACE_AGENTS: Trace agent invocations (default: true)
            AIGIE_STRANDS_TRACE_TOOLS: Trace tool calls (default: true)
            AIGIE_STRANDS_TRACE_LLM: Trace LLM calls (default: true)
            AIGIE_STRANDS_TRACE_MULTI_AGENT: Trace multi-agent orchestrations (default: true)
            AIGIE_STRANDS_TRACE_STREAMING: Trace BidiAgent streaming events (default: false)
            AIGIE_STRANDS_CAPTURE_INPUTS: Capture input data (default: true)
            AIGIE_STRANDS_CAPTURE_OUTPUTS: Capture output data (default: true)
            AIGIE_STRANDS_CAPTURE_MESSAGES: Capture messages (default: true)
            AIGIE_STRANDS_REDACT_PII: Redact PII (default: false)
            AIGIE_STRANDS_MAX_CONTENT_LENGTH: Max content length (default: 2000)
            AIGIE_STRANDS_MAX_MESSAGE_LENGTH: Max message length (default: 2000)
            AIGIE_STRANDS_MAX_TOOL_RESULT_LENGTH: Max tool result length (default: 1000)
        """
        return cls(
            enabled=os.getenv("AIGIE_STRANDS_ENABLED", "true").lower() == "true",
            trace_agents=os.getenv("AIGIE_STRANDS_TRACE_AGENTS", "true").lower() == "true",
            trace_tools=os.getenv("AIGIE_STRANDS_TRACE_TOOLS", "true").lower() == "true",
            trace_llm_calls=os.getenv("AIGIE_STRANDS_TRACE_LLM", "true").lower() == "true",
            trace_multi_agent=os.getenv("AIGIE_STRANDS_TRACE_MULTI_AGENT", "true").lower() == "true",
            trace_streaming=os.getenv("AIGIE_STRANDS_TRACE_STREAMING", "false").lower() == "true",
            capture_inputs=os.getenv("AIGIE_STRANDS_CAPTURE_INPUTS", "true").lower() == "true",
            capture_outputs=os.getenv("AIGIE_STRANDS_CAPTURE_OUTPUTS", "true").lower() == "true",
            capture_messages=os.getenv("AIGIE_STRANDS_CAPTURE_MESSAGES", "true").lower() == "true",
            redact_pii=os.getenv("AIGIE_STRANDS_REDACT_PII", "false").lower() == "true",
            max_content_length=int(os.getenv("AIGIE_STRANDS_MAX_CONTENT_LENGTH", "2000")),
            max_message_length=int(os.getenv("AIGIE_STRANDS_MAX_MESSAGE_LENGTH", "2000")),
            max_tool_result_length=int(os.getenv("AIGIE_STRANDS_MAX_TOOL_RESULT_LENGTH", "1000")),
        )

    def merge(self, **overrides) -> "StrandsConfig":
        """
        Create a new config with overridden values.

        Args:
            **overrides: Values to override

        Returns:
            New StrandsConfig with overrides applied
        """
        return StrandsConfig(
            enabled=overrides.get("enabled", self.enabled),
            trace_agents=overrides.get("trace_agents", self.trace_agents),
            trace_tools=overrides.get("trace_tools", self.trace_tools),
            trace_llm_calls=overrides.get("trace_llm_calls", self.trace_llm_calls),
            trace_multi_agent=overrides.get("trace_multi_agent", self.trace_multi_agent),
            trace_streaming=overrides.get("trace_streaming", self.trace_streaming),
            capture_inputs=overrides.get("capture_inputs", self.capture_inputs),
            capture_outputs=overrides.get("capture_outputs", self.capture_outputs),
            capture_messages=overrides.get("capture_messages", self.capture_messages),
            redact_pii=overrides.get("redact_pii", self.redact_pii),
            max_content_length=overrides.get("max_content_length", self.max_content_length),
            max_message_length=overrides.get("max_message_length", self.max_message_length),
            max_tool_result_length=overrides.get("max_tool_result_length", self.max_tool_result_length),
        )
