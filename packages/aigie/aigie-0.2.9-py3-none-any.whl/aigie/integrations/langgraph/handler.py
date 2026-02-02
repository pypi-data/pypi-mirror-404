"""
LangGraph callback handler for Aigie SDK.

This module provides the LangGraphHandler which implements LangChain's
BaseCallbackHandler protocol for automatic trace/span creation in
LangGraph stateful graph workflows.

Features:
    - Automatic trace/span creation for graph executions, nodes, and edges
    - State transition tracking with version history
    - Token usage tracking with cost estimation
    - Error detection and classification
    - Drift detection for workflow execution paths
    - Configurable timeout and retry settings

Usage:
    from aigie.integrations.langgraph import LangGraphHandler

    # With explicit trace
    async with aigie.trace("My Workflow") as trace:
        handler = LangGraphHandler(trace_name="My Graph")
        handler._trace_context = trace
        result = await app.ainvoke(
            {"input": "..."},
            config={"callbacks": [handler]}
        )

    # Auto-instrumentation (recommended)
    from aigie.integrations.langgraph import patch_langgraph
    patch_langgraph()  # Now all graphs are automatically traced

Configuration:
    Use LangGraphConfig to customize behavior:

    from aigie.integrations.langgraph import LangGraphConfig, LangGraphHandler

    config = LangGraphConfig(
        trace_graphs=True,
        trace_nodes=True,
        trace_edges=True,
        graph_timeout=600.0,  # 10 minutes
        max_retries=3,
        redact_pii=True,
        max_content_length=2000,
    )

Decorators:
    Use decorators for fine-grained tracing:

    from aigie.integrations.langgraph import trace_langgraph_node, trace_langgraph_edge

    @trace_langgraph_node
    async def my_node(state):
        # Node logic
        return {"result": "..."}

    @trace_langgraph_edge
    def my_conditional_edge(state):
        # Route logic
        return "next_node"

For implementation details, see the core LangGraph module at aigie/langgraph.py.
"""

from typing import TYPE_CHECKING

# Re-export the main handler and wrapper functions from core module
from ...langgraph import (
    LangGraphHandler,
    wrap_langgraph,
    trace_langgraph_node,
    trace_langgraph_edge,
    create_langgraph_handler,
)

# Import config for easy access
from .config import LangGraphConfig

# Import error detection components
from .error_detection import (
    ErrorDetector,
    ErrorType,
    ErrorSeverity,
    DetectedError,
    ErrorStats,
    get_error_detector,
    reset_error_detector,
)

# Import session management
from .session import (
    LangGraphSessionContext,
    get_session_context,
    set_session_context,
    reset_session_context,
    get_or_create_session_context,
    langgraph_session,
    clear_session_context,
)

if TYPE_CHECKING:
    from langchain_core.callbacks import BaseCallbackHandler

# Export all public symbols
__all__ = [
    # Primary handler
    "LangGraphHandler",
    # Wrapper functions
    "wrap_langgraph",
    "trace_langgraph_node",
    "trace_langgraph_edge",
    "create_langgraph_handler",
    # Configuration
    "LangGraphConfig",
    # Error detection
    "ErrorDetector",
    "ErrorType",
    "ErrorSeverity",
    "DetectedError",
    "ErrorStats",
    "get_error_detector",
    "reset_error_detector",
    # Session management
    "LangGraphSessionContext",
    "get_session_context",
    "set_session_context",
    "reset_session_context",
    "get_or_create_session_context",
    "langgraph_session",
    "clear_session_context",
]
