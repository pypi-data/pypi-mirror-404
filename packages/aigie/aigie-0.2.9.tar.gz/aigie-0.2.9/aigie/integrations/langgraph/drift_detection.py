"""
Drift Detection for LangGraph Workflows.

Tracks graph execution planning vs actual node execution to detect behavioral drifts.
Useful for monitoring workflow reliability and detecting deviations.
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class DriftType(Enum):
    """Types of behavioral drift."""
    # Planning drifts
    MISSING_STEP = "missing_step"           # Planned step not executed
    EXTRA_STEP = "extra_step"               # Unplanned step executed
    STEP_ORDER = "step_order"               # Steps executed in wrong order

    # Tool usage drifts
    UNEXPECTED_TOOL = "unexpected_tool"     # Tool used that wasn't mentioned
    MISSING_TOOL = "missing_tool"           # Expected tool not used
    TOOL_OVERUSE = "tool_overuse"           # Tool used more than expected

    # Node/graph drifts
    EXTRA_NODE = "extra_node"               # More nodes executed than planned
    MISSING_NODE = "missing_node"           # Fewer nodes than planned
    NODE_RETRY = "node_retry"               # Node had to be retried
    UNEXPECTED_EDGE = "unexpected_edge"     # Unexpected edge transition

    # State drifts
    STATE_DRIFT = "state_drift"             # State changed unexpectedly
    MISSING_STATE_KEY = "missing_state_key" # Expected state key not present

    # Output drifts
    INCOMPLETE_OUTPUT = "incomplete_output" # Output missing expected components
    FORMAT_DRIFT = "format_drift"           # Output format differs from plan

    # Performance drifts
    DURATION_ANOMALY = "duration_anomaly"   # Execution took much longer/shorter
    TOKEN_ANOMALY = "token_anomaly"         # Token usage anomaly


class DriftSeverity(Enum):
    """Severity of detected drift."""
    INFO = "info"           # Expected variation, informational
    WARNING = "warning"     # Notable deviation, worth monitoring
    ALERT = "alert"         # Significant drift, may need intervention


@dataclass
class DetectedDrift:
    """Represents a detected drift with full context."""
    drift_type: DriftType
    severity: DriftSeverity
    description: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "drift_type": self.drift_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "expected": self.expected,
            "actual": self.actual,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class GraphPlan:
    """Captures the graph's plan/intent for execution."""
    # Graph structure
    graph_name: Optional[str] = None
    defined_nodes: Set[str] = field(default_factory=set)
    defined_edges: List[Dict[str, str]] = field(default_factory=list)

    # Expected execution
    expected_node_sequence: List[str] = field(default_factory=list)
    expected_tools: Set[str] = field(default_factory=set)
    expected_state_keys: Set[str] = field(default_factory=set)

    # Raw planning
    raw_plan: Optional[str] = None
    initial_input: Optional[str] = None
    system_prompt: Optional[str] = None

    # Planning node outputs (from nodes like "planner", "think", etc.)
    planning_node_outputs: List[Dict[str, Any]] = field(default_factory=list)

    # Extracted planned steps from agent responses
    planned_steps: List[str] = field(default_factory=list)

    # Plan metadata
    timestamp: datetime = field(default_factory=datetime.now)
    model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "graph_name": self.graph_name,
            "defined_nodes": list(self.defined_nodes),
            "defined_edges": self.defined_edges,
            "expected_node_sequence": self.expected_node_sequence,
            "expected_tools": list(self.expected_tools),
            "expected_state_keys": list(self.expected_state_keys),
            "raw_plan": self.raw_plan,
            "initial_input_preview": self.initial_input[:200] if self.initial_input else None,
            "system_prompt_preview": self.system_prompt[:500] if self.system_prompt else None,
            "planning_node_outputs": self.planning_node_outputs,
            "planned_steps": self.planned_steps,
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
        }


@dataclass
class ExecutionTrace:
    """Tracks actual execution for comparison against plan."""
    # Execution events
    nodes_executed: List[Dict[str, Any]] = field(default_factory=list)
    edges_traversed: List[Dict[str, Any]] = field(default_factory=list)
    tools_used: List[Dict[str, Any]] = field(default_factory=list)
    llm_responses: List[Dict[str, Any]] = field(default_factory=list)
    state_changes: List[Dict[str, Any]] = field(default_factory=list)

    # Metrics
    total_duration_ms: float = 0
    total_tokens: int = 0
    total_cost: float = 0
    error_count: int = 0
    retry_count: int = 0

    # Outputs
    final_output: Optional[str] = None
    final_state: Optional[Dict[str, Any]] = None

    def add_node_execution(
        self,
        node_name: str,
        duration_ms: float,
        input_state: Optional[Dict] = None,
        output_state: Optional[Dict] = None,
        is_error: bool = False,
        is_retry: bool = False,
    ) -> None:
        """Record a node execution."""
        self.nodes_executed.append({
            "node_name": node_name,
            "duration_ms": duration_ms,
            "input_state_preview": str(input_state)[:200] if input_state else None,
            "output_state_preview": str(output_state)[:200] if output_state else None,
            "is_error": is_error,
            "is_retry": is_retry,
            "timestamp": datetime.now().isoformat(),
        })
        if is_error:
            self.error_count += 1
        if is_retry:
            self.retry_count += 1

    def add_edge_traversal(self, from_node: str, to_node: str, condition: Optional[str] = None) -> None:
        """Record an edge traversal."""
        self.edges_traversed.append({
            "from_node": from_node,
            "to_node": to_node,
            "condition": condition,
            "timestamp": datetime.now().isoformat(),
        })

    def add_tool_use(self, tool_name: str, tool_input: Dict, duration_ms: float, is_error: bool = False) -> None:
        """Record a tool use."""
        self.tools_used.append({
            "tool_name": tool_name,
            "tool_input_preview": str(tool_input)[:200],
            "duration_ms": duration_ms,
            "is_error": is_error,
            "timestamp": datetime.now().isoformat(),
        })
        if is_error:
            self.error_count += 1

    def add_llm_response(self, text_preview: str, model: Optional[str] = None) -> None:
        """Record an LLM response."""
        self.llm_responses.append({
            "text_preview": text_preview[:200],
            "model": model,
            "timestamp": datetime.now().isoformat(),
        })

    def add_state_change(self, node_name: str, changed_keys: List[str], state_preview: Optional[str] = None) -> None:
        """Record a state change."""
        self.state_changes.append({
            "node_name": node_name,
            "changed_keys": changed_keys,
            "state_preview": state_preview[:200] if state_preview else None,
            "timestamp": datetime.now().isoformat(),
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "nodes_executed": self.nodes_executed,
            "nodes_summary": self._get_nodes_summary(),
            "edges_traversed": self.edges_traversed,
            "tools_used": self.tools_used,
            "tools_summary": self._get_tools_summary(),
            "llm_response_count": len(self.llm_responses),
            "state_changes": self.state_changes,
            "total_duration_ms": self.total_duration_ms,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "error_count": self.error_count,
            "retry_count": self.retry_count,
        }

    def _get_nodes_summary(self) -> Dict[str, int]:
        """Get summary of nodes executed."""
        summary = {}
        for node in self.nodes_executed:
            name = node["node_name"]
            summary[name] = summary.get(name, 0) + 1
        return summary

    def _get_tools_summary(self) -> Dict[str, int]:
        """Get summary of tools used."""
        summary = {}
        for tool in self.tools_used:
            name = tool["tool_name"]
            summary[name] = summary.get(name, 0) + 1
        return summary

    def get_execution_path(self) -> List[str]:
        """Get the actual execution path as list of node names."""
        return [n["node_name"] for n in self.nodes_executed if not n.get("is_retry")]


class DriftDetector:
    """
    Detects drift between graph planning and actual execution.

    Captures:
    - Graph structure (nodes, edges)
    - Actual execution path
    - Compares and reports deviations
    """

    def __init__(self):
        self.plan = GraphPlan()
        self.execution = ExecutionTrace()
        self.detected_drifts: List[DetectedDrift] = []
        self._plan_captured = False

    def capture_graph_structure(
        self,
        graph_name: str,
        nodes: List[str],
        edges: List[Dict[str, str]],
    ) -> None:
        """Capture graph structure for plan extraction."""
        self.plan.graph_name = graph_name
        self.plan.defined_nodes = set(nodes)
        self.plan.defined_edges = edges

    def capture_initial_input(self, input_data: Any) -> None:
        """Capture initial workflow input."""
        if isinstance(input_data, dict):
            self.plan.initial_input = str(input_data)[:500]
            # Extract expected state keys from input
            self.plan.expected_state_keys.update(input_data.keys())
        else:
            self.plan.initial_input = str(input_data)[:500]

    def capture_expected_sequence(self, node_sequence: List[str]) -> None:
        """Capture expected node execution sequence."""
        self.plan.expected_node_sequence = node_sequence

    def capture_system_prompt(self, system_prompt: str) -> None:
        """Capture system prompt for plan extraction."""
        self.plan.system_prompt = system_prompt
        self._extract_plan_from_prompt(system_prompt)

    def capture_planning_node_output(
        self,
        node_name: str,
        output: Any,
        is_planning_node: bool = False,
    ) -> None:
        """
        Capture output from a planning node.

        Planning nodes are nodes that contain planning logic, typically named:
        - planner, plan, planning
        - think, thinking, reason, reasoning
        - decide, decision
        - route, router
        """
        output_str = str(output) if output else ""

        # Check if this looks like a planning node by name
        planning_keywords = {'planner', 'plan', 'planning', 'think', 'thinking',
                           'reason', 'reasoning', 'decide', 'decision', 'route', 'router'}
        node_lower = node_name.lower()
        is_planning = is_planning_node or any(kw in node_lower for kw in planning_keywords)

        if is_planning and output_str:
            self.plan.planning_node_outputs.append({
                "node_name": node_name,
                "output_preview": output_str[:1000],
                "timestamp": datetime.now().isoformat(),
            })
            # Extract planning from this output
            self._extract_plan_from_response(output_str)
            self._plan_captured = True

    def capture_planning_response(self, response_text: str) -> None:
        """
        Capture agent's planning response.

        Looks for planning patterns like:
        - "I'll process through nodes..."
        - "Steps: search -> analyze -> output"
        """
        if self._plan_captured:
            return

        self.plan.raw_plan = response_text
        self._extract_plan_from_response(response_text)
        self._plan_captured = True

    def record_node_execution(
        self,
        node_name: str,
        duration_ms: float = 0,
        input_state: Optional[Dict] = None,
        output_state: Optional[Dict] = None,
        is_error: bool = False,
        is_retry: bool = False,
    ) -> Optional[DetectedDrift]:
        """Record a node execution and check for drift."""
        self.execution.add_node_execution(
            node_name, duration_ms, input_state, output_state, is_error, is_retry
        )

        # Check if this is a planning node and capture its output
        planning_keywords = {'planner', 'plan', 'planning', 'think', 'thinking',
                           'reason', 'reasoning', 'decide', 'decision', 'route', 'router'}
        node_lower = node_name.lower()
        is_planning_node = any(kw in node_lower for kw in planning_keywords)

        if is_planning_node and output_state:
            # Capture planning node output
            self.capture_planning_node_output(node_name, output_state, is_planning_node=True)

        # Check for retry drift
        if is_retry:
            drift = DetectedDrift(
                drift_type=DriftType.NODE_RETRY,
                severity=DriftSeverity.WARNING,
                description=f"Node '{node_name}' was retried",
                expected="Single execution",
                actual="Retry required",
                metadata={"node_name": node_name},
            )
            self.detected_drifts.append(drift)
            return drift

        # Check for unexpected node
        if self.plan.defined_nodes and node_name not in self.plan.defined_nodes:
            drift = DetectedDrift(
                drift_type=DriftType.EXTRA_NODE,
                severity=DriftSeverity.INFO,
                description=f"Node '{node_name}' executed but not in defined graph",
                expected=f"Defined nodes: {', '.join(self.plan.defined_nodes)}",
                actual=node_name,
            )
            self.detected_drifts.append(drift)
            return drift

        return None

    def record_edge_traversal(
        self,
        from_node: str,
        to_node: str,
        condition: Optional[str] = None,
    ) -> Optional[DetectedDrift]:
        """Record an edge traversal and check for drift."""
        self.execution.add_edge_traversal(from_node, to_node, condition)

        # Check if edge is defined
        if self.plan.defined_edges:
            edge_found = any(
                e.get("from") == from_node and e.get("to") == to_node
                for e in self.plan.defined_edges
            )
            if not edge_found:
                drift = DetectedDrift(
                    drift_type=DriftType.UNEXPECTED_EDGE,
                    severity=DriftSeverity.INFO,
                    description=f"Edge '{from_node}' -> '{to_node}' not in defined graph",
                    expected=f"Defined edges",
                    actual=f"{from_node} -> {to_node}",
                    metadata={"condition": condition},
                )
                self.detected_drifts.append(drift)
                return drift

        return None

    def record_tool_use(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        duration_ms: float = 0,
        is_error: bool = False,
    ) -> Optional[DetectedDrift]:
        """Record a tool use and check for drift."""
        self.execution.add_tool_use(tool_name, tool_input, duration_ms, is_error)

        # Check for unexpected tool
        if self.plan.expected_tools and tool_name not in self.plan.expected_tools:
            drift = DetectedDrift(
                drift_type=DriftType.UNEXPECTED_TOOL,
                severity=DriftSeverity.INFO,
                description=f"Tool '{tool_name}' used but not in original plan",
                expected=f"Expected tools: {', '.join(self.plan.expected_tools)}",
                actual=tool_name,
                metadata={"tool_input_preview": str(tool_input)[:100]},
            )
            self.detected_drifts.append(drift)
            return drift

        return None

    def record_state_change(
        self,
        node_name: str,
        old_state: Optional[Dict] = None,
        new_state: Optional[Dict] = None,
    ) -> Optional[DetectedDrift]:
        """Record a state change and check for drift."""
        if not old_state or not new_state:
            return None

        # Find changed keys
        changed_keys = []
        for key in set(old_state.keys()) | set(new_state.keys()):
            old_val = old_state.get(key)
            new_val = new_state.get(key)
            if old_val != new_val:
                changed_keys.append(key)

        if changed_keys:
            self.execution.add_state_change(
                node_name, changed_keys, str(new_state)[:200]
            )

        return None

    def record_llm_response(self, text: str, model: Optional[str] = None) -> None:
        """Record an LLM response."""
        self.execution.add_llm_response(text, model)

        # Capture planning from first substantial response
        if not self._plan_captured and len(text) > 50:
            self.capture_planning_response(text)

    def finalize(
        self,
        total_duration_ms: float,
        total_tokens: int,
        total_cost: float,
        final_output: Optional[str] = None,
        final_state: Optional[Dict] = None,
    ) -> List[DetectedDrift]:
        """
        Finalize execution tracking and perform final drift analysis.

        Returns all detected drifts.
        """
        self.execution.total_duration_ms = total_duration_ms
        self.execution.total_tokens = total_tokens
        self.execution.total_cost = total_cost
        self.execution.final_output = final_output
        self.execution.final_state = final_state

        # Perform final drift analysis
        self._analyze_node_coverage()
        self._analyze_tool_coverage()
        self._analyze_execution_sequence()

        return self.detected_drifts

    def _extract_plan_from_prompt(self, text: str) -> None:
        """Extract planning information from system prompt."""
        if not text:
            return

        # Extract tool definitions/mentions from prompt
        tool_patterns = [
            r"tools?[:\s]+\[([^\]]+)\]",  # tools: [search, analyze]
            r"available tools?[:\s]*([^\n]+)",  # available tools: search, analyze
            r"you (?:have access to|can use)[:\s]*([^\n]+tools?[^\n]*)",  # you have access to the following tools
        ]
        for pattern in tool_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract individual tool names
                tools = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', match)
                # Filter out common words
                stopwords = {'the', 'and', 'or', 'to', 'a', 'an', 'use', 'using', 'tools', 'tool', 'following'}
                self.plan.expected_tools.update(t for t in tools if t.lower() not in stopwords)

        # Extract expected steps/workflow from prompt
        step_patterns = [
            r"(?:step|phase)\s*(\d+)[:\s]*([^\n]+)",  # Step 1: Do something
            r"(\d+)\.\s+([^\n]+)",  # 1. Do something
            r"(?:first|then|next|finally)[,:\s]+([^\n]+)",  # First, do something
        ]
        for pattern in step_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                step_text = match[-1] if isinstance(match, tuple) else match
                if step_text and len(step_text) > 5:
                    self.plan.planned_steps.append(step_text.strip()[:200])

    def _extract_plan_from_response(self, text: str) -> None:
        """Extract planning from agent response with improved pattern matching."""
        if not text:
            return

        # Look for tool mentions - multiple patterns
        tool_patterns = [
            r"\[(?:Using|Tool)[:\s]*(\w+)\]",  # [Using: search]
            r"(?:use|using|call|calling)\s+(?:the\s+)?(\w+)\s+tool",  # use the search tool
            r"(?:invoke|invoking)\s+(?:the\s+)?(\w+)",  # invoke search
            r"tool[:\s]+['\"]?(\w+)['\"]?",  # tool: "search"
            r"function[:\s]+['\"]?(\w+)['\"]?",  # function: "search"
        ]
        for pattern in tool_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            self.plan.expected_tools.update(matches)

        # Look for node mentions
        node_patterns = [
            r"(?:process|execute|run|go to|move to)\s+(?:the\s+)?(\w+)\s+(?:node|step)",
            r"(?:node|step)[:\s]+['\"]?(\w+)['\"]?",
        ]
        for pattern in node_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for node in matches:
                if node not in self.plan.expected_node_sequence:
                    self.plan.expected_node_sequence.append(node)

        # Extract planned steps from numbered lists
        numbered_steps = re.findall(r'(?:^|\n)\s*(\d+)[.):]\s*([^\n]+)', text)
        for num, step in numbered_steps:
            step_text = step.strip()
            if step_text and len(step_text) > 5 and step_text not in self.plan.planned_steps:
                self.plan.planned_steps.append(step_text[:200])

        # Extract steps from "I will..." or "My plan is..." patterns
        plan_patterns = [
            r"(?:I will|I'll|I'm going to|Let me|My plan is to)[:\s]*([^\n.]+)",
            r"(?:First|Then|Next|Finally|After that)[,:\s]+(?:I will|I'll|we)?[:\s]*([^\n.]+)",
            r"(?:Step \d+|Phase \d+)[:\s]*([^\n]+)",
        ]
        for pattern in plan_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                step_text = match.strip()
                if step_text and len(step_text) > 5 and step_text not in self.plan.planned_steps:
                    self.plan.planned_steps.append(step_text[:200])

        # Extract from arrow notation: search -> analyze -> output
        arrow_pattern = r'(\w+)\s*(?:->|→|=>)\s*(\w+)'
        arrow_matches = re.findall(arrow_pattern, text)
        for from_step, to_step in arrow_matches:
            if from_step not in self.plan.expected_node_sequence:
                self.plan.expected_node_sequence.append(from_step)
            if to_step not in self.plan.expected_node_sequence:
                self.plan.expected_node_sequence.append(to_step)

    def _analyze_node_coverage(self) -> None:
        """Analyze if expected nodes were executed."""
        if not self.plan.defined_nodes:
            return

        executed_nodes = set(self.execution._get_nodes_summary().keys())
        missing = self.plan.defined_nodes - executed_nodes

        # Only report if most nodes were executed (not just a single path)
        if missing and len(executed_nodes) > len(missing):
            drift = DetectedDrift(
                drift_type=DriftType.MISSING_NODE,
                severity=DriftSeverity.INFO,
                description=f"Defined nodes not executed: {', '.join(missing)}",
                expected=f"Nodes: {', '.join(self.plan.defined_nodes)}",
                actual=f"Executed: {', '.join(executed_nodes)}",
            )
            self.detected_drifts.append(drift)

    def _analyze_tool_coverage(self) -> None:
        """Analyze if expected tools were used."""
        if not self.plan.expected_tools:
            return

        used_tools = set(self.execution._get_tools_summary().keys())
        missing = self.plan.expected_tools - used_tools

        if missing:
            drift = DetectedDrift(
                drift_type=DriftType.MISSING_TOOL,
                severity=DriftSeverity.INFO,
                description=f"Expected tools not used: {', '.join(missing)}",
                expected=f"Tools: {', '.join(self.plan.expected_tools)}",
                actual=f"Used: {', '.join(used_tools)}",
            )
            self.detected_drifts.append(drift)

    def _analyze_execution_sequence(self) -> None:
        """Analyze if execution sequence matches expected."""
        if not self.plan.expected_node_sequence:
            return

        actual_path = self.execution.get_execution_path()

        # Check for sequence mismatch
        if actual_path and self.plan.expected_node_sequence:
            expected_set = set(self.plan.expected_node_sequence)
            actual_set = set(actual_path)

            # Check if order differs
            if actual_path != self.plan.expected_node_sequence[:len(actual_path)]:
                drift = DetectedDrift(
                    drift_type=DriftType.STEP_ORDER,
                    severity=DriftSeverity.INFO,
                    description="Execution order differs from expected sequence",
                    expected=f"Sequence: {' -> '.join(self.plan.expected_node_sequence)}",
                    actual=f"Actual: {' -> '.join(actual_path)}",
                )
                self.detected_drifts.append(drift)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of plan vs execution."""
        return {
            "plan": self.plan.to_dict(),
            "execution": self.execution.to_dict(),
            "drifts": [d.to_dict() for d in self.detected_drifts],
            "drift_count": len(self.detected_drifts),
            "has_warnings": any(d.severity in [DriftSeverity.WARNING, DriftSeverity.ALERT] for d in self.detected_drifts),
        }

    def get_drift_report(self) -> str:
        """Get a human-readable drift report."""
        if not self.detected_drifts:
            return "No drifts detected - execution matched plan"

        report = f"Detected {len(self.detected_drifts)} drift(s):\n"
        for i, drift in enumerate(self.detected_drifts, 1):
            report += f"\n{i}. [{drift.severity.value.upper()}] {drift.drift_type.value}\n"
            report += f"   {drift.description}\n"
            if drift.expected:
                report += f"   Expected: {drift.expected}\n"
            if drift.actual:
                report += f"   Actual: {drift.actual}\n"

        return report
