"""
Validation Models - Request/Response Models for Gateway Communication

These models define the protocol between SDK and backend for real-time validation.
They mirror the backend models for consistent serialization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class GatewayDecision(str, Enum):
    """Decision types from backend validation."""
    ALLOW = "allow"
    BLOCK = "block"
    MODIFY = "modify"
    DELAY = "delay"
    CONSULT = "consult"


class SignalType(str, Enum):
    """Types of risk signals detected during validation."""
    TOOL_LOOP_RISK = "tool_loop_risk"
    CONTEXT_DRIFT_RISK = "context_drift_risk"
    RATE_LIMIT_RISK = "rate_limit_risk"
    HALLUCINATION_RISK = "hallucination_risk"
    POLICY_VIOLATION = "policy_violation"
    PATTERN_MATCH = "pattern_match"
    EXECUTION_ANOMALY = "execution_anomaly"


@dataclass
class ValidationSignal:
    """Signal detected during validation."""
    type: SignalType
    confidence: float
    description: str
    evidence: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "confidence": self.confidence,
            "description": self.description,
            "evidence": self.evidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationSignal":
        return cls(
            type=SignalType(data["type"]),
            confidence=data["confidence"],
            description=data["description"],
            evidence=data.get("evidence"),
        )


@dataclass
class ModificationSuggestion:
    """Suggested modification to tool call arguments."""
    field: str
    original_value: Any
    suggested_value: Any
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "original_value": self.original_value,
            "suggested_value": self.suggested_value,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModificationSuggestion":
        return cls(
            field=data["field"],
            original_value=data["original_value"],
            suggested_value=data["suggested_value"],
            reason=data["reason"],
        )


@dataclass
class TraceContext:
    """Trace context for correlation."""
    trace_id: str
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
        }


@dataclass
class ToolCallInfo:
    """Information about the tool call being validated."""
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    tool_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "arguments": self.arguments,
            "tool_type": self.tool_type,
        }


@dataclass
class AgentContext:
    """Context about the agent making the tool call."""
    agent_type: Optional[str] = None
    agent_name: Optional[str] = None
    recent_actions: List[Dict[str, Any]] = field(default_factory=list)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    iteration_count: int = 0
    total_tokens_used: int = 0
    estimated_cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_type": self.agent_type,
            "agent_name": self.agent_name,
            "recent_actions": self.recent_actions[-10:],  # Limit to last 10
            "session_id": self.session_id,
            "user_id": self.user_id,
            "iteration_count": self.iteration_count,
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


@dataclass
class PreExecutionRequest:
    """Request for pre-execution validation."""
    trace_context: TraceContext
    tool_call: ToolCallInfo
    context: AgentContext = field(default_factory=AgentContext)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    recent_messages: Optional[List[Dict[str, Any]]] = None
    guideline_ids: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "trace_context": self.trace_context.to_dict(),
            "tool_call": self.tool_call.to_dict(),
            "context": self.context.to_dict(),
            "recent_messages": self.recent_messages[-5:] if self.recent_messages else None,
            "guideline_ids": self.guideline_ids,
        }


@dataclass
class PreExecutionResponse:
    """Response from pre-execution validation."""
    request_id: str
    decision: GatewayDecision
    reason: str = ""
    modifications: Optional[Dict[str, Any]] = None
    modification_suggestions: List[ModificationSuggestion] = field(default_factory=list)
    signals: List[ValidationSignal] = field(default_factory=list)
    confidence: float = 1.0
    delay_ms: Optional[int] = None
    retry_after: Optional[datetime] = None
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PreExecutionResponse":
        """Parse response from backend."""
        signals = []
        for signal_data in data.get("signals", []):
            try:
                signals.append(ValidationSignal.from_dict(signal_data))
            except Exception:
                pass

        suggestions = []
        for sugg_data in data.get("modification_suggestions", []):
            try:
                suggestions.append(ModificationSuggestion.from_dict(sugg_data))
            except Exception:
                pass

        return cls(
            request_id=data["request_id"],
            decision=GatewayDecision(data["decision"]),
            reason=data.get("reason", ""),
            modifications=data.get("modifications"),
            modification_suggestions=suggestions,
            signals=signals,
            confidence=data.get("confidence", 1.0),
            delay_ms=data.get("delay_ms"),
            retry_after=datetime.fromisoformat(data["retry_after"]) if data.get("retry_after") else None,
            latency_ms=data.get("latency_ms", 0.0),
        )

    @classmethod
    def allow(
        cls,
        request_id: str,
        reason: str = "No issues detected",
        latency_ms: float = 0.0
    ) -> "PreExecutionResponse":
        """Factory for ALLOW decision."""
        return cls(
            request_id=request_id,
            decision=GatewayDecision.ALLOW,
            reason=reason,
            latency_ms=latency_ms,
        )

    @classmethod
    def block(
        cls,
        request_id: str,
        reason: str,
        signals: Optional[List[ValidationSignal]] = None,
        confidence: float = 1.0,
        latency_ms: float = 0.0
    ) -> "PreExecutionResponse":
        """Factory for BLOCK decision."""
        return cls(
            request_id=request_id,
            decision=GatewayDecision.BLOCK,
            reason=reason,
            signals=signals or [],
            confidence=confidence,
            latency_ms=latency_ms,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "decision": self.decision.value,
            "reason": self.reason,
            "modifications": self.modifications,
            "modification_suggestions": [s.to_dict() for s in self.modification_suggestions],
            "signals": [s.to_dict() for s in self.signals],
            "confidence": self.confidence,
            "delay_ms": self.delay_ms,
            "retry_after": self.retry_after.isoformat() if self.retry_after else None,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class InterventionSignal:
    """Intervention signal pushed from backend."""
    id: str
    trace_id: str
    span_id: Optional[str]
    intervention_type: str
    confidence: float
    reason: str
    evidence: Dict[str, Any]
    payload: Dict[str, Any]
    priority: int = 5

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterventionSignal":
        return cls(
            id=data["id"],
            trace_id=data["trace_id"],
            span_id=data.get("span_id"),
            intervention_type=data["intervention_type"],
            confidence=data.get("confidence", 0.0),
            reason=data.get("reason", ""),
            evidence=data.get("evidence", {}),
            payload=data.get("payload", {}),
            priority=data.get("priority", 5),
        )
