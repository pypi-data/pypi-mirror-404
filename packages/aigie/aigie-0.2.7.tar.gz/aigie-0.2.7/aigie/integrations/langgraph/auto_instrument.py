"""
LangGraph auto-instrumentation.

Automatically patches LangGraph workflows to create traces and inject handlers.
"""

import functools
import logging
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)

_patched_classes: Set[Any] = set()


def patch_langgraph() -> bool:
    """Patch LangGraph classes for auto-instrumentation.

    Returns:
        True if patching was successful (or already patched)
    """
    success = True
    success = _patch_state_graph() and success
    success = _patch_compiled_graph() and success
    return success


def unpatch_langgraph() -> None:
    """Remove LangGraph patches (for testing)."""
    global _patched_classes
    _patched_classes.clear()


def is_langgraph_patched() -> bool:
    """Check if LangGraph has been patched."""
    return len(_patched_classes) > 0


def _extract_workflow_name(inputs: Any, graph_schema: Any = None) -> str:
    """Extract meaningful workflow name from inputs or graph schema.

    Priority:
    1. inputs.metadata.workflow_name
    2. inputs.metadata.workflow_type
    3. inputs.metadata.use_case
    4. Graph schema class name (e.g., ResearchState -> research_workflow)
    5. Fallback to "LangGraph Workflow"
    """
    if isinstance(inputs, dict):
        metadata = inputs.get('metadata', {})
        if isinstance(metadata, dict):
            # Check for explicit workflow name
            if metadata.get('workflow_name'):
                return metadata['workflow_name']
            # Check for workflow type
            if metadata.get('workflow_type'):
                wf_type = metadata['workflow_type']
                # Convert to readable name: "deep_research" -> "deep_research_workflow"
                if not wf_type.endswith('_workflow'):
                    return f"{wf_type}_workflow"
                return wf_type
            # Check for use case
            if metadata.get('use_case'):
                return f"{metadata['use_case']}_workflow"

    # Try to extract from graph schema class name
    if graph_schema is not None:
        schema_name = None
        if hasattr(graph_schema, '__name__'):
            schema_name = graph_schema.__name__
        elif hasattr(graph_schema, '__class__'):
            schema_name = graph_schema.__class__.__name__

        if schema_name and schema_name not in ('dict', 'Dict', 'TypedDict', 'State'):
            # Convert PascalCase to snake_case: ResearchState -> research_state
            import re
            snake_name = re.sub(r'(?<!^)(?=[A-Z])', '_', schema_name).lower()
            # Remove 'state' suffix if present: research_state -> research
            if snake_name.endswith('_state'):
                snake_name = snake_name[:-6]
            if snake_name:
                return f"{snake_name}_workflow"

    return "LangGraph Workflow"


def _patch_state_graph() -> bool:
    """Patch StateGraph.compile() to return auto-instrumented app."""
    try:
        from langgraph.graph import StateGraph

        if StateGraph in _patched_classes:
            return True

        original_compile = StateGraph.compile

        @functools.wraps(original_compile)
        def traced_compile(self, **kwargs):
            """Traced version of compile."""
            app = original_compile(self, **kwargs)

            # Store reference to graph schema for name extraction
            graph_schema = None
            if hasattr(self, 'schema') and self.schema:
                graph_schema = self.schema
            elif hasattr(self, 'channels') and self.channels:
                # Try to get schema from first channel's annotation
                graph_schema = next(iter(self.channels.keys()), None) if self.channels else None

            # Patch the compiled app's invoke methods
            if hasattr(app, 'ainvoke'):
                original_ainvoke = app.ainvoke

                async def traced_ainvoke(inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
                    from ...client import get_aigie
                    from ...langgraph import LangGraphHandler
                    from ...callback import AigieCallbackHandler
                    from ...auto_instrument.trace import get_or_create_trace

                    aigie = get_aigie()
                    if aigie and aigie._initialized:
                        # Extract meaningful workflow name
                        workflow_name = _extract_workflow_name(inputs, graph_schema)

                        trace = await get_or_create_trace(
                            name=workflow_name,
                            metadata={
                                "type": "langgraph",
                                "inputs": inputs if isinstance(inputs, dict) else {},
                                "framework": "langgraph"
                            }
                        )

                        # Ensure _current_trace is set for nested LLM calls
                        from ...auto_instrument.trace import set_current_trace
                        set_current_trace(trace)

                        # Create LangGraph handler for node tracking
                        langgraph_handler = LangGraphHandler(
                            trace_name=workflow_name,
                            metadata={"type": "langgraph", "framework": "langgraph"}
                        )
                        langgraph_handler._aigie = aigie
                        langgraph_handler._trace_context = trace
                        langgraph_handler.trace_id = trace.id if trace else None

                        # Create LangChain callback handler for LLM/tool tracking
                        # Link to LangGraphHandler so it can access current node span
                        callback_handler = AigieCallbackHandler(trace=trace)
                        callback_handler._langgraph_handler = langgraph_handler

                        if config is None:
                            config = {}
                        if 'callbacks' not in config:
                            config['callbacks'] = []
                        config['callbacks'].append(langgraph_handler)
                        config['callbacks'].append(callback_handler)

                        # Set run_name in metadata for LangChain tracing
                        if 'metadata' not in config:
                            config['metadata'] = {}
                        config['metadata']['run_name'] = workflow_name

                    return await original_ainvoke(inputs, config=config, **kwargs)

                app.ainvoke = traced_ainvoke

            if hasattr(app, 'invoke'):
                original_invoke = app.invoke

                def traced_invoke(inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
                    """Traced version of invoke."""
                    from ...client import get_aigie
                    from ...langgraph import LangGraphHandler
                    from ...callback import AigieCallbackHandler
                    from ...auto_instrument.trace import get_or_create_trace_sync

                    aigie = get_aigie()
                    if aigie and aigie._initialized:
                        # Extract meaningful workflow name
                        workflow_name = _extract_workflow_name(inputs, graph_schema)

                        trace = get_or_create_trace_sync(
                            name=workflow_name,
                            metadata={
                                "type": "langgraph",
                                "inputs": inputs if isinstance(inputs, dict) else {},
                                "framework": "langgraph"
                            }
                        )

                        if trace:
                            # Ensure _current_trace is set for nested LLM calls
                            from ...auto_instrument.trace import set_current_trace
                            set_current_trace(trace)

                            # Create LangGraph handler for node tracking
                            langgraph_handler = LangGraphHandler(
                                trace_name=workflow_name,
                                metadata={"type": "langgraph", "framework": "langgraph"}
                            )
                            langgraph_handler._aigie = aigie
                            langgraph_handler._trace_context = trace
                            langgraph_handler.trace_id = trace.id if trace else None

                            # Create LangChain callback handler for LLM/tool tracking
                            # Link to LangGraphHandler so it can access current node span
                            callback_handler = AigieCallbackHandler(trace=trace)
                            callback_handler._langgraph_handler = langgraph_handler

                            if config is None:
                                config = {}
                            if 'callbacks' not in config:
                                config['callbacks'] = []
                            config['callbacks'].append(langgraph_handler)
                            config['callbacks'].append(callback_handler)

                            # Set run_name in metadata for LangChain tracing
                            if 'metadata' not in config:
                                config['metadata'] = {}
                            config['metadata']['run_name'] = workflow_name

                    return original_invoke(inputs, config=config, **kwargs)

                app.invoke = traced_invoke

            return app

        StateGraph.compile = traced_compile
        _patched_classes.add(StateGraph)

        logger.debug("Patched StateGraph.compile for auto-instrumentation")
        return True

    except ImportError:
        logger.debug("LangGraph not installed, skipping StateGraph patch")
        return True  # Not an error if LangGraph not installed
    except Exception as e:
        logger.warning(f"Failed to patch StateGraph: {e}")
        return False


def _patch_compiled_graph() -> bool:
    """Patch CompiledStateGraph/Pregel methods directly."""
    try:
        # Try to import the actual compiled graph class (varies by langgraph version)
        CompiledGraph = None
        try:
            from langgraph.graph.state import CompiledStateGraph
            CompiledGraph = CompiledStateGraph
        except ImportError:
            pass

        if not CompiledGraph:
            try:
                from langgraph.graph.graph import CompiledGraph as CG
                CompiledGraph = CG
            except ImportError:
                pass

        if not CompiledGraph:
            try:
                from langgraph.pregel import Pregel
                CompiledGraph = Pregel
            except ImportError:
                pass

        if not CompiledGraph:
            logger.debug("Could not find CompiledGraph/CompiledStateGraph/Pregel class to patch")
            return True

        if CompiledGraph in _patched_classes:
            return True

        logger.debug(f"Patching {CompiledGraph.__name__} for auto-instrumentation")

        original_ainvoke = CompiledGraph.ainvoke
        original_invoke = CompiledGraph.invoke

        @functools.wraps(original_ainvoke)
        async def traced_ainvoke(self, inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
            """Traced version of CompiledGraph.ainvoke."""
            from ...client import get_aigie
            from ...langgraph import LangGraphHandler
            from ...callback import AigieCallbackHandler
            from ...auto_instrument.trace import get_or_create_trace

            aigie = get_aigie()
            if aigie and aigie._initialized:
                # Extract meaningful workflow name
                graph_schema = getattr(self, 'builder', None)
                if graph_schema and hasattr(graph_schema, 'schema'):
                    graph_schema = graph_schema.schema
                workflow_name = _extract_workflow_name(inputs, graph_schema)

                trace = await get_or_create_trace(
                    name=workflow_name,
                    metadata={
                        "type": "langgraph",
                        "inputs": inputs if isinstance(inputs, dict) else {},
                        "framework": "langgraph"
                    }
                )

                # Ensure _current_trace is set for nested LLM calls
                from ...auto_instrument.trace import set_current_trace
                set_current_trace(trace)

                # Create LangGraph handler for node tracking
                langgraph_handler = LangGraphHandler(
                    trace_name=workflow_name,
                    metadata={"type": "langgraph", "framework": "langgraph"}
                )
                langgraph_handler._aigie = aigie
                langgraph_handler._trace_context = trace
                langgraph_handler.trace_id = trace.id if trace else None

                # Create LangChain callback handler for LLM/tool tracking
                # Link to LangGraphHandler so it can access current node span
                callback_handler = AigieCallbackHandler(trace=trace)
                callback_handler._langgraph_handler = langgraph_handler

                if config is None:
                    config = {}
                if 'callbacks' not in config:
                    config['callbacks'] = []
                config['callbacks'].append(langgraph_handler)
                config['callbacks'].append(callback_handler)

                # Set run_name in metadata for LangChain tracing
                if 'metadata' not in config:
                    config['metadata'] = {}
                config['metadata']['run_name'] = workflow_name

            return await original_ainvoke(self, inputs, config=config, **kwargs)

        @functools.wraps(original_invoke)
        def traced_invoke(self, inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
            """Traced version of CompiledGraph.invoke."""
            from ...client import get_aigie
            from ...langgraph import LangGraphHandler
            from ...callback import AigieCallbackHandler
            from ...auto_instrument.trace import get_or_create_trace_sync

            aigie = get_aigie()
            if aigie and aigie._initialized:
                # Extract meaningful workflow name
                graph_schema = getattr(self, 'builder', None)
                if graph_schema and hasattr(graph_schema, 'schema'):
                    graph_schema = graph_schema.schema
                workflow_name = _extract_workflow_name(inputs, graph_schema)

                trace = get_or_create_trace_sync(
                    name=workflow_name,
                    metadata={
                        "type": "langgraph",
                        "inputs": inputs if isinstance(inputs, dict) else {},
                        "framework": "langgraph"
                    }
                )

                if trace:
                    # Ensure _current_trace is set for nested LLM calls
                    from ...auto_instrument.trace import set_current_trace
                    set_current_trace(trace)

                    # Create LangGraph handler for node tracking
                    langgraph_handler = LangGraphHandler(
                        trace_name=workflow_name,
                        metadata={"type": "langgraph", "framework": "langgraph"}
                    )
                    langgraph_handler._aigie = aigie
                    langgraph_handler._trace_context = trace
                    langgraph_handler.trace_id = trace.id if trace else None

                    # Create LangChain callback handler for LLM/tool tracking
                    # Link to LangGraphHandler so it can access current node span
                    callback_handler = AigieCallbackHandler(trace=trace)
                    callback_handler._langgraph_handler = langgraph_handler

                    if config is None:
                        config = {}
                    if 'callbacks' not in config:
                        config['callbacks'] = []
                    config['callbacks'].append(langgraph_handler)
                    config['callbacks'].append(callback_handler)

                    # Set run_name in metadata for LangChain tracing
                    if 'metadata' not in config:
                        config['metadata'] = {}
                    config['metadata']['run_name'] = workflow_name

            return original_invoke(self, inputs, config=config, **kwargs)

        CompiledGraph.ainvoke = traced_ainvoke
        CompiledGraph.invoke = traced_invoke
        _patched_classes.add(CompiledGraph)

        logger.debug(f"Patched {CompiledGraph.__name__} for auto-instrumentation")
        return True

    except ImportError:
        return True
    except Exception as e:
        logger.warning(f"Failed to patch CompiledGraph: {e}")
        return False
