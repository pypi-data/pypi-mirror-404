"""
Aigie LangChain Integration

Full workflow tracing for LangChain with the Aigie SDK.
Traces chains, agents, LLM calls, tool invocations, and retrievers.

Usage (Auto-Instrumentation - Recommended):
    import aigie
    from aigie.integrations.langchain import patch_langchain

    # Initialize Aigie
    aigie_client = aigie.Aigie()
    await aigie_client.initialize()

    # Enable auto-instrumentation
    patch_langchain()

    # Now all LangChain operations are automatically traced
    from langchain.agents import AgentExecutor
    from langchain_openai import ChatOpenAI

    agent = AgentExecutor(agent=..., tools=...)
    result = await agent.ainvoke({"input": "..."})  # Automatically traced!

Usage (Manual Callback Handler):
    from aigie.integrations.langchain import LangChainHandler
    from langchain.agents import AgentExecutor

    # Create handler with trace context
    async with aigie.trace("My Workflow") as trace:
        handler = LangChainHandler(trace=trace)
        result = await agent.ainvoke(
            {"input": "..."},
            config={"callbacks": [handler]}
        )

Usage (Configuration):
    from aigie.integrations.langchain import LangChainConfig, patch_langchain

    # Custom configuration
    config = LangChainConfig(
        trace_chains=True,
        trace_llm_calls=True,
        capture_prompts=True,
        max_retries=5,
        llm_timeout=180.0,
    )

    # Apply configuration (config is used by handlers)
    patch_langchain()
"""

__all__ = [
    # Handler (callback)
    "AigieCallbackHandler",
    "LangChainHandler",
    # Configuration
    "LangChainConfig",
    # Cost tracking
    "LANGCHAIN_MODEL_PRICING",
    "get_langchain_cost",
    "extract_tokens_from_response",
    "extract_model_from_llm",
    # Error detection
    "ErrorDetector",
    "ErrorType",
    "ErrorSeverity",
    "DetectedError",
    "ErrorStats",
    "get_error_detector",
    "reset_error_detector",
    # Drift detection
    "DriftDetector",
    "DriftType",
    "DriftSeverity",
    "DetectedDrift",
    "WorkflowPlan",
    "ExecutionTrace",
    # Auto-instrumentation
    "patch_langchain",
    "unpatch_langchain",
    "is_langchain_patched",
    # Utilities
    "is_langchain_available",
    "get_langchain_version",
    "safe_str",
    "extract_chain_name",
    "mask_sensitive_content",
    # Retry/Timeout utilities
    "RetryExhaustedError",
    "TimeoutExceededError",
    "with_timeout",
    "with_retry",
    "with_timeout_and_retry",
    "retry_decorator",
    "RetryContext",
]

from typing import TYPE_CHECKING, Any


def __getattr__(name: str) -> Any:
    """Lazy imports for performance."""

    # Handler
    if name == "AigieCallbackHandler":
        from .handler import AigieCallbackHandler
        return AigieCallbackHandler

    if name == "LangChainHandler":
        from .handler import LangChainHandler
        return LangChainHandler

    # Configuration
    if name == "LangChainConfig":
        from .config import LangChainConfig
        return LangChainConfig

    # Error detection
    if name == "ErrorDetector":
        from .error_detection import ErrorDetector
        return ErrorDetector

    if name == "ErrorType":
        from .error_detection import ErrorType
        return ErrorType

    if name == "ErrorSeverity":
        from .error_detection import ErrorSeverity
        return ErrorSeverity

    if name == "DetectedError":
        from .error_detection import DetectedError
        return DetectedError

    if name == "ErrorStats":
        from .error_detection import ErrorStats
        return ErrorStats

    if name == "get_error_detector":
        from .error_detection import get_error_detector
        return get_error_detector

    if name == "reset_error_detector":
        from .error_detection import reset_error_detector
        return reset_error_detector

    # Drift detection
    if name == "DriftDetector":
        from .drift_detection import DriftDetector
        return DriftDetector

    if name == "DriftType":
        from .drift_detection import DriftType
        return DriftType

    if name == "DriftSeverity":
        from .drift_detection import DriftSeverity
        return DriftSeverity

    if name == "DetectedDrift":
        from .drift_detection import DetectedDrift
        return DetectedDrift

    if name == "WorkflowPlan":
        from .drift_detection import WorkflowPlan
        return WorkflowPlan

    if name == "ExecutionTrace":
        from .drift_detection import ExecutionTrace
        return ExecutionTrace

    # Cost tracking
    if name == "LANGCHAIN_MODEL_PRICING":
        from .cost_tracking import LANGCHAIN_MODEL_PRICING
        return LANGCHAIN_MODEL_PRICING

    if name == "get_langchain_cost":
        from .cost_tracking import get_langchain_cost
        return get_langchain_cost

    if name == "extract_tokens_from_response":
        from .cost_tracking import extract_tokens_from_response
        return extract_tokens_from_response

    if name == "extract_model_from_llm":
        from .cost_tracking import extract_model_from_llm
        return extract_model_from_llm

    # Auto-instrumentation
    if name == "patch_langchain":
        from .auto_instrument import patch_langchain
        return patch_langchain

    if name == "unpatch_langchain":
        from .auto_instrument import unpatch_langchain
        return unpatch_langchain

    if name == "is_langchain_patched":
        from .auto_instrument import is_langchain_patched
        return is_langchain_patched

    # Utilities
    if name == "is_langchain_available":
        from .utils import is_langchain_available
        return is_langchain_available

    if name == "get_langchain_version":
        from .utils import get_langchain_version
        return get_langchain_version

    if name == "safe_str":
        from .utils import safe_str
        return safe_str

    if name == "extract_chain_name":
        from .utils import extract_chain_name
        return extract_chain_name

    if name == "mask_sensitive_content":
        from .utils import mask_sensitive_content
        return mask_sensitive_content

    # Retry/Timeout utilities
    if name == "RetryExhaustedError":
        from .retry import RetryExhaustedError
        return RetryExhaustedError

    if name == "TimeoutExceededError":
        from .retry import TimeoutExceededError
        return TimeoutExceededError

    if name == "with_timeout":
        from .retry import with_timeout
        return with_timeout

    if name == "with_retry":
        from .retry import with_retry
        return with_retry

    if name == "with_timeout_and_retry":
        from .retry import with_timeout_and_retry
        return with_timeout_and_retry

    if name == "retry_decorator":
        from .retry import retry_decorator
        return retry_decorator

    if name == "RetryContext":
        from .retry import RetryContext
        return RetryContext

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


if TYPE_CHECKING:
    from .handler import AigieCallbackHandler, LangChainHandler
    from .config import LangChainConfig
    from .cost_tracking import (
        LANGCHAIN_MODEL_PRICING,
        get_langchain_cost,
        extract_tokens_from_response,
        extract_model_from_llm,
    )
    from .error_detection import (
        ErrorDetector,
        ErrorType,
        ErrorSeverity,
        DetectedError,
        ErrorStats,
        get_error_detector,
        reset_error_detector,
    )
    from .drift_detection import (
        DriftDetector,
        DriftType,
        DriftSeverity,
        DetectedDrift,
        WorkflowPlan,
        ExecutionTrace,
    )
    from .auto_instrument import (
        patch_langchain,
        unpatch_langchain,
        is_langchain_patched,
    )
    from .utils import (
        is_langchain_available,
        get_langchain_version,
        safe_str,
        extract_chain_name,
        mask_sensitive_content,
    )
    from .retry import (
        RetryExhaustedError,
        TimeoutExceededError,
        with_timeout,
        with_retry,
        with_timeout_and_retry,
        retry_decorator,
        RetryContext,
    )
