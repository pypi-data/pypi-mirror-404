"""
LangGraph auto-instrumentation.

Automatically patches LangGraph workflows to create traces and inject handlers.

Name extraction follows Langfuse's pattern with prioritized fallbacks:
1. inputs.metadata.workflow_name (explicit)
2. inputs.metadata.workflow_type (e.g., "deep_research" -> "deep_research_workflow")
3. Graph schema class name (e.g., ResearchState -> research_workflow)
4. Fallback to "LangGraph Workflow"
"""

import functools
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_patched_classes = set()


def _extract_workflow_name(inputs: Any, graph_schema: Any = None) -> str:
    """Extract meaningful workflow name from inputs or graph schema.

    Follows Langfuse's pattern with prioritized fallbacks.
    """
    logger.debug(f"_extract_workflow_name called with inputs type: {type(inputs)}, graph_schema: {graph_schema}")

    # Check inputs metadata first
    if isinstance(inputs, dict):
        metadata = inputs.get('metadata', {})
        logger.debug(f"Extracting workflow name - inputs.metadata: {metadata}")
        if isinstance(metadata, dict):
            # 1. Explicit workflow name
            if metadata.get('workflow_name'):
                logger.debug(f"Using workflow_name from metadata: {metadata['workflow_name']}")
                return metadata['workflow_name']
            # 2. Workflow type -> workflow name
            if metadata.get('workflow_type'):
                wf_type = metadata['workflow_type']
                result = f"{wf_type}_workflow" if not wf_type.endswith('_workflow') else wf_type
                logger.debug(f"Using workflow_type from metadata: {wf_type} -> {result}")
                return result
            # 3. Use case -> workflow name
            if metadata.get('use_case'):
                result = f"{metadata['use_case']}_workflow"
                logger.debug(f"Using use_case from metadata: {result}")
                return result
        else:
            logger.debug(f"metadata is not a dict: {type(metadata)}")
    else:
        logger.debug(f"inputs is not a dict: {type(inputs)}")

    # 4. Extract from graph schema class name
    if graph_schema is not None:
        logger.debug(f"Extracting from graph_schema: {graph_schema}, type: {type(graph_schema)}")
        schema_name = None

        # Only use __name__ if it's actually a class/type
        if isinstance(graph_schema, type):
            schema_name = graph_schema.__name__
            logger.debug(f"Got schema name from type.__name__: {schema_name}")
        elif hasattr(graph_schema, '__name__'):
            schema_name = graph_schema.__name__
            logger.debug(f"Got schema name from __name__: {schema_name}")
        elif hasattr(graph_schema, '__class__') and graph_schema.__class__ != type:
            schema_name = graph_schema.__class__.__name__
            logger.debug(f"Got schema name from __class__.__name__: {schema_name}")

        # Filter out built-in types and common non-meaningful names
        if schema_name and schema_name not in ('dict', 'Dict', 'TypedDict', 'State', 'str', 'int', 'list', 'bool', 'float', 'NoneType'):
            # Convert PascalCase to snake_case
            snake_name = re.sub(r'(?<!^)(?=[A-Z])', '_', schema_name).lower()
            # Remove 'state' suffix if present
            if snake_name.endswith('_state'):
                snake_name = snake_name[:-6]
            if snake_name:
                result = f"{snake_name}_workflow"
                logger.debug(f"Using schema-derived name: {result}")
                return result
        else:
            logger.debug(f"Schema name filtered out: {schema_name}")

    # 5. Fallback
    logger.debug("Using fallback name: LangGraph Workflow")
    return "LangGraph Workflow"


def patch_langgraph() -> None:
    """Patch LangGraph classes for auto-instrumentation."""
    _patch_state_graph()
    _patch_compiled_graph()


def _patch_state_graph() -> None:
    """Patch StateGraph.compile() to return auto-instrumented app."""
    try:
        from langgraph.graph import StateGraph

        if StateGraph in _patched_classes:
            return

        original_compile = StateGraph.compile

        @functools.wraps(original_compile)
        def traced_compile(self, **kwargs):
            """Traced version of compile."""
            app = original_compile(self, **kwargs)

            # Store reference to graph schema for name extraction
            # The schema should be the TypedDict/class used to define the state
            graph_schema = None

            # Method 1: Direct schema attribute (preferred - set by StateGraph.__init__)
            if hasattr(self, 'schema') and self.schema:
                schema = self.schema
                # Make sure it's actually a class/type, not a string or primitive
                if isinstance(schema, type) and schema not in (dict, str, int, list, bool, float):
                    graph_schema = schema
                    logger.debug(f"Got graph_schema from self.schema: {graph_schema}")

            # Method 2: Try _schema (internal attribute)
            if not graph_schema and hasattr(self, '_schema') and self._schema:
                schema = self._schema
                if isinstance(schema, type) and schema not in (dict, str, int, list, bool, float):
                    graph_schema = schema
                    logger.debug(f"Got graph_schema from self._schema: {graph_schema}")

            # Method 3: Check 'schemas' attribute (LangGraph >= 0.2.x stores state class as key)
            if not graph_schema and hasattr(self, 'schemas') and self.schemas:
                # self.schemas is a dict with the state class as keys
                for schema_class in self.schemas.keys():
                    if isinstance(schema_class, type) and schema_class not in (dict, str, int, list, bool, float):
                        graph_schema = schema_class
                        logger.debug(f"Got graph_schema from self.schemas: {graph_schema}")
                        break

            # Method 4: Check channels for the state type (fallback for older versions)
            if not graph_schema and hasattr(self, 'channels') and self.channels:
                logger.debug(f"channels.keys(): {list(self.channels.keys())}")

            # Patch the compiled app's invoke methods
            if hasattr(app, 'ainvoke'):
                original_ainvoke = app.ainvoke

                async def traced_ainvoke(inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
                    import os
                    if os.environ.get('AIGIE_DEBUG'):
                        print(f"  [DEBUG traced_ainvoke] ENTERED")
                        print(f"  [DEBUG traced_ainvoke] config before: {config}")

                    from ..client import get_aigie
                    from ..langgraph import LangGraphHandler
                    from ..callback import AigieCallbackHandler
                    from ..auto_instrument.trace import get_or_create_trace

                    aigie = get_aigie()
                    if os.environ.get('AIGIE_DEBUG'):
                        print(f"  [DEBUG traced_ainvoke] aigie={aigie}, initialized={aigie._initialized if aigie else 'N/A'}")

                    # Ensure aigie is initialized (it might still be initializing in background)
                    if aigie and not aigie._initialized:
                        try:
                            await aigie.initialize()
                        except Exception as e:
                            logger.debug(f"Failed to initialize aigie: {e}")

                    langgraph_span = None
                    if aigie and aigie._initialized:
                        # Extract workflow name from inputs/schema
                        workflow_name = _extract_workflow_name(inputs, graph_schema)

                        trace = await get_or_create_trace(
                            name=workflow_name,
                            metadata={"type": "langgraph", "inputs": inputs if isinstance(inputs, dict) else {}, "framework": "langgraph"}
                        )

                        # Ensure _current_trace is set for nested LLM calls
                        from ..auto_instrument.trace import set_current_trace
                        set_current_trace(trace)

                        # Create parent "LangGraph" span to wrap all workflow nodes
                        # This matches LangFuse's visualization pattern
                        langgraph_span = trace.span(
                            name="LangGraph",
                            type="workflow",
                            parent=None  # Direct child of trace
                        )
                        await langgraph_span.__aenter__()
                        langgraph_span.set_input(inputs if isinstance(inputs, dict) else {"input": str(inputs)})
                        langgraph_span.set_metadata({
                            "framework": "langgraph",
                            "workflow_name": workflow_name,
                            "nodeType": "langgraph_wrapper"
                        })

                        # Create LangChain callback handler for LLM/tool tracking
                        callback_handler = AigieCallbackHandler(aigie=aigie, trace=trace)
                        # Set the LangGraph span as the root parent for all callback spans
                        callback_handler._langgraph_parent_span_id = langgraph_span.id

                        # Debug logging
                        import os
                        if os.environ.get('AIGIE_DEBUG'):
                            print(f"  [DEBUG langgraph.py] Created callback_handler instance: {id(callback_handler)}")
                            print(f"  [DEBUG langgraph.py] Set _langgraph_parent_span_id: {callback_handler._langgraph_parent_span_id}")

                        # Create LangGraph handler for node tracking
                        langgraph_handler = LangGraphHandler(
                            trace_name=workflow_name,
                            metadata={"type": "langgraph", "framework": "langgraph"}
                        )
                        langgraph_handler._aigie = aigie
                        langgraph_handler._trace_context = trace
                        langgraph_handler.trace_id = trace.id if trace else None
                        # Set the LangGraph span as the parent for all node spans
                        langgraph_handler._langgraph_span_id = langgraph_span.id

                        if config is None:
                            config = {}
                        if 'callbacks' not in config:
                            config['callbacks'] = []
                        config['callbacks'].append(langgraph_handler)
                        config['callbacks'].append(callback_handler)

                        # Set run_name in config metadata
                        if 'metadata' not in config:
                            config['metadata'] = {}
                        config['metadata']['run_name'] = workflow_name

                        if os.environ.get('AIGIE_DEBUG'):
                            print(f"  [DEBUG traced_ainvoke] config['callbacks'] = {config['callbacks']}")
                            print(f"  [DEBUG traced_ainvoke] callback_handler id: {id(callback_handler)}")

                    # Set callback context to prevent LLM auto-instrumentation from creating duplicate spans
                    # The callbacks will handle LLM tracing via on_llm_start/on_llm_end
                    from ..auto_instrument.trace import set_callback_context
                    set_callback_context(True)

                    try:
                        result = await original_ainvoke(inputs, config=config, **kwargs)
                        # Close the LangGraph span with success
                        if langgraph_span:
                            langgraph_span.set_output(result if isinstance(result, dict) else {"output": str(result)})
                            await langgraph_span.__aexit__(None, None, None)
                        return result
                    except Exception as e:
                        # Close the LangGraph span with error
                        if langgraph_span:
                            await langgraph_span.__aexit__(type(e), e, e.__traceback__)
                        raise
                    finally:
                        # Reset callback context after workflow completes
                        set_callback_context(False)

                app.ainvoke = traced_ainvoke

            if hasattr(app, 'invoke'):
                original_invoke = app.invoke

                def traced_invoke(inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
                    """Traced version of invoke."""
                    from ..client import get_aigie
                    from ..langgraph import LangGraphHandler
                    from ..callback import AigieCallbackHandler
                    from ..auto_instrument.trace import get_or_create_trace_sync

                    aigie = get_aigie()
                    if aigie and aigie._initialized:
                        # Extract workflow name from inputs/schema
                        workflow_name = _extract_workflow_name(inputs, graph_schema)

                        trace = get_or_create_trace_sync(
                            name=workflow_name,
                            metadata={"type": "langgraph", "inputs": inputs if isinstance(inputs, dict) else {}, "framework": "langgraph"}
                        )

                        if trace:
                            # Ensure _current_trace is set for nested LLM calls
                            from ..auto_instrument.trace import set_current_trace
                            set_current_trace(trace)

                            # Create LangChain callback handler for LLM/tool tracking
                            callback_handler = AigieCallbackHandler(aigie=aigie, trace=trace)

                            # Create LangGraph handler for node tracking
                            langgraph_handler = LangGraphHandler(
                                trace_name=workflow_name,
                                metadata={"type": "langgraph", "framework": "langgraph"}
                            )
                            langgraph_handler._aigie = aigie
                            langgraph_handler._trace_context = trace
                            langgraph_handler.trace_id = trace.id if trace else None

                            if config is None:
                                config = {}
                            if 'callbacks' not in config:
                                config['callbacks'] = []
                            config['callbacks'].append(langgraph_handler)
                            config['callbacks'].append(callback_handler)

                            # Set run_name in config metadata
                            if 'metadata' not in config:
                                config['metadata'] = {}
                            config['metadata']['run_name'] = workflow_name

                    return original_invoke(inputs, config=config, **kwargs)

                app.invoke = traced_invoke

            return app

        StateGraph.compile = traced_compile
        _patched_classes.add(StateGraph)

        logger.debug("Patched StateGraph.compile for auto-instrumentation")

    except ImportError:
        pass  # LangGraph not installed
    except Exception as e:
        logger.warning(f"Failed to patch StateGraph: {e}")


def _patch_compiled_graph() -> None:
    """Patch CompiledGraph methods directly."""
    try:
        from langgraph.graph.graph import CompiledGraph
        
        if CompiledGraph in _patched_classes:
            return
        
        original_ainvoke = CompiledGraph.ainvoke
        original_invoke = CompiledGraph.invoke
        
        @functools.wraps(original_ainvoke)
        async def traced_ainvoke(self, inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
            """Traced version of CompiledGraph.ainvoke."""
            from ..client import get_aigie
            from ..langgraph import LangGraphHandler
            from ..callback import AigieCallbackHandler
            from ..auto_instrument.trace import get_or_create_trace
            
            aigie = get_aigie()
            if aigie and aigie._initialized:
                trace = await get_or_create_trace(
                    name="LangGraph Workflow",
                    metadata={"type": "langgraph", "inputs": inputs if isinstance(inputs, dict) else {}}
                )
                
                # Create LangChain callback handler for LLM/tool tracking FIRST
                callback_handler = AigieCallbackHandler(trace=trace)
                
                # Create LangGraph handler for node tracking
                langgraph_handler = LangGraphHandler(
                    trace_name="LangGraph Workflow",
                    metadata={"type": "langgraph"}
                )
                langgraph_handler._aigie = aigie
                langgraph_handler._trace_context = trace  # Share trace context
                langgraph_handler.trace_id = trace.id if trace else None
                
                if config is None:
                    config = {}
                if 'callbacks' not in config:
                    config['callbacks'] = []
                config['callbacks'].append(langgraph_handler)
                config['callbacks'].append(callback_handler)  # Add LangChain callback handler
            
            return await original_ainvoke(self, inputs, config=config, **kwargs)
        
        @functools.wraps(original_invoke)
        def traced_invoke(self, inputs: Any, config: Optional[Dict[str, Any]] = None, **kwargs):
            """Traced version of CompiledGraph.invoke."""
            from ..client import get_aigie
            from ..langgraph import LangGraphHandler
            from ..callback import AigieCallbackHandler
            from ..auto_instrument.trace import get_or_create_trace_sync
            
            aigie = get_aigie()
            if aigie and aigie._initialized:
                trace = get_or_create_trace_sync(
                    name="LangGraph Workflow",
                    metadata={"type": "langgraph", "inputs": inputs if isinstance(inputs, dict) else {}}
                )
                
                if trace:
                    # Create LangGraph handler for node tracking
                    langgraph_handler = LangGraphHandler(
                        trace_name="LangGraph Workflow",
                        metadata={"type": "langgraph"}
                    )
                    langgraph_handler._aigie = aigie
                    langgraph_handler.trace_id = trace.id if trace else None
                    
                    # Create LangChain callback handler for LLM/tool tracking
                    callback_handler = AigieCallbackHandler(trace=trace)
                    
                    if config is None:
                        config = {}
                    if 'callbacks' not in config:
                        config['callbacks'] = []
                    config['callbacks'].append(langgraph_handler)
                    config['callbacks'].append(callback_handler)  # Add LangChain callback handler
            
            return original_invoke(self, inputs, config=config, **kwargs)
        
        CompiledGraph.ainvoke = traced_ainvoke
        CompiledGraph.invoke = traced_invoke
        _patched_classes.add(CompiledGraph)
        
        logger.debug("Patched CompiledGraph for auto-instrumentation")
        
    except ImportError:
        pass  # LangGraph not installed
    except Exception as e:
        logger.warning(f"Failed to patch CompiledGraph: {e}")

