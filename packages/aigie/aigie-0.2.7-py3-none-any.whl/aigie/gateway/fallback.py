"""
Fallback Strategies - Handling Gateway Unavailability

Defines fallback modes and strategies when the gateway is unavailable
or times out. Ensures graceful degradation without blocking execution.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import hashlib

from .validation import (
    GatewayDecision,
    PreExecutionRequest,
    PreExecutionResponse,
    ValidationSignal,
    SignalType,
)

logger = logging.getLogger("aigie.gateway.fallback")


class FallbackMode(str, Enum):
    """Fallback modes when gateway is unavailable."""
    ALLOW = "allow"      # Fail-open: allow all requests (default)
    BLOCK = "block"      # Fail-closed: block high-risk patterns
    CACHE = "cache"      # Use cached decisions
    LOCAL = "local"      # Use local pattern matching only


@dataclass
class CachedDecision:
    """Cached validation decision."""
    pattern_key: str
    decision: GatewayDecision
    reason: str
    signals: List[ValidationSignal]
    cached_at: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 300  # 5 minutes default

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.cached_at + timedelta(seconds=self.ttl_seconds)


class FallbackStrategy:
    """
    Strategy for handling gateway unavailability.

    Provides:
    - Configurable fallback modes
    - Local pattern matching for known risks
    - Decision caching for recently seen patterns
    - Statistics tracking
    """

    # Known high-risk tool patterns (for BLOCK mode)
    HIGH_RISK_TOOLS: Set[str] = {
        "shell_execute",
        "run_command",
        "execute_code",
        "delete_file",
        "drop_database",
    }

    # Loop detection threshold
    LOOP_THRESHOLD = 5

    def __init__(
        self,
        mode: FallbackMode = FallbackMode.ALLOW,
        cache_ttl_seconds: int = 300,
        max_cache_size: int = 1000,
        enable_local_loop_detection: bool = True,
    ):
        """
        Initialize fallback strategy.

        Args:
            mode: Fallback mode to use
            cache_ttl_seconds: TTL for cached decisions
            max_cache_size: Maximum cache entries
            enable_local_loop_detection: Enable local tool loop detection
        """
        self.mode = mode
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_cache_size = max_cache_size
        self.enable_local_loop_detection = enable_local_loop_detection

        # Decision cache
        self._cache: Dict[str, CachedDecision] = {}

        # Tool call tracking for loop detection
        self._tool_call_history: Dict[str, List[datetime]] = {}  # trace_id -> list of times

        # Statistics
        self._stats = {
            "fallback_invocations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "local_blocks": 0,
            "local_allows": 0,
        }

    def get_fallback_response(
        self,
        request: PreExecutionRequest,
        reason: str = "Gateway unavailable"
    ) -> PreExecutionResponse:
        """
        Get fallback response when gateway is unavailable.

        Args:
            request: The pre-execution request
            reason: Reason for using fallback

        Returns:
            Fallback PreExecutionResponse
        """
        self._stats["fallback_invocations"] += 1

        # Try cache first (for CACHE mode or as optimization)
        if self.mode in (FallbackMode.CACHE, FallbackMode.LOCAL):
            cached = self._get_cached_decision(request)
            if cached:
                self._stats["cache_hits"] += 1
                return PreExecutionResponse(
                    request_id=request.request_id,
                    decision=cached.decision,
                    reason=f"Cached: {cached.reason}",
                    signals=cached.signals,
                    confidence=0.7,  # Lower confidence for cached
                )
            self._stats["cache_misses"] += 1

        # Apply mode-specific logic
        if self.mode == FallbackMode.ALLOW:
            return self._allow_response(request, reason)

        elif self.mode == FallbackMode.BLOCK:
            return self._block_if_risky(request, reason)

        elif self.mode == FallbackMode.LOCAL:
            return self._local_validation(request, reason)

        # Default: allow
        return self._allow_response(request, reason)

    def cache_decision(
        self,
        request: PreExecutionRequest,
        response: PreExecutionResponse
    ):
        """
        Cache a decision for future fallback use.

        Args:
            request: The original request
            response: The response to cache
        """
        pattern_key = self._compute_pattern_key(request)

        # Evict old entries if cache is full
        if len(self._cache) >= self.max_cache_size:
            self._evict_expired_entries()

        self._cache[pattern_key] = CachedDecision(
            pattern_key=pattern_key,
            decision=response.decision,
            reason=response.reason,
            signals=response.signals,
            ttl_seconds=self.cache_ttl_seconds,
        )

    def record_tool_call(
        self,
        trace_id: str,
        tool_name: str
    ):
        """
        Record a tool call for loop detection.

        Args:
            trace_id: Trace ID
            tool_name: Name of the tool called
        """
        if not self.enable_local_loop_detection:
            return

        key = f"{trace_id}:{tool_name}"
        if key not in self._tool_call_history:
            self._tool_call_history[key] = []

        self._tool_call_history[key].append(datetime.utcnow())

        # Clean up old entries (older than 5 minutes)
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        self._tool_call_history[key] = [
            t for t in self._tool_call_history[key]
            if t > cutoff
        ]

    def detect_local_loop(
        self,
        trace_id: str,
        tool_name: str
    ) -> Optional[ValidationSignal]:
        """
        Detect tool loop using local history.

        Args:
            trace_id: Trace ID
            tool_name: Name of the tool

        Returns:
            ValidationSignal if loop detected, None otherwise
        """
        if not self.enable_local_loop_detection:
            return None

        key = f"{trace_id}:{tool_name}"
        call_times = self._tool_call_history.get(key, [])

        # Check if threshold exceeded in recent window
        recent_cutoff = datetime.utcnow() - timedelta(seconds=60)
        recent_calls = [t for t in call_times if t > recent_cutoff]

        if len(recent_calls) >= self.LOOP_THRESHOLD:
            return ValidationSignal(
                type=SignalType.TOOL_LOOP_RISK,
                confidence=min(0.6 + (len(recent_calls) - self.LOOP_THRESHOLD) * 0.1, 0.95),
                description=f"Tool '{tool_name}' called {len(recent_calls)} times in 60s",
                evidence={
                    "tool_name": tool_name,
                    "call_count": len(recent_calls),
                    "threshold": self.LOOP_THRESHOLD,
                    "window_sec": 60,
                },
            )

        return None

    def _get_cached_decision(
        self,
        request: PreExecutionRequest
    ) -> Optional[CachedDecision]:
        """Get cached decision for a request."""
        pattern_key = self._compute_pattern_key(request)
        cached = self._cache.get(pattern_key)

        if cached and not cached.is_expired:
            return cached

        # Remove expired entry
        if cached:
            del self._cache[pattern_key]

        return None

    def _compute_pattern_key(self, request: PreExecutionRequest) -> str:
        """Compute pattern key for caching."""
        # Hash based on tool name and argument structure (not values)
        key_parts = [
            request.tool_call.name,
            str(sorted(request.tool_call.arguments.keys())),
        ]
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]

    def _allow_response(
        self,
        request: PreExecutionRequest,
        reason: str
    ) -> PreExecutionResponse:
        """Create an allow response."""
        self._stats["local_allows"] += 1
        return PreExecutionResponse.allow(
            request_id=request.request_id,
            reason=f"Fallback allow: {reason}",
        )

    def _block_if_risky(
        self,
        request: PreExecutionRequest,
        reason: str
    ) -> PreExecutionResponse:
        """Block if request matches high-risk patterns."""
        signals = []

        # Check for high-risk tools
        if request.tool_call.name.lower() in self.HIGH_RISK_TOOLS:
            signals.append(ValidationSignal(
                type=SignalType.POLICY_VIOLATION,
                confidence=0.9,
                description=f"High-risk tool '{request.tool_call.name}' blocked in fallback mode",
            ))

        # Check for local loop detection
        loop_signal = self.detect_local_loop(
            request.trace_context.trace_id,
            request.tool_call.name
        )
        if loop_signal:
            signals.append(loop_signal)

        if signals:
            self._stats["local_blocks"] += 1
            return PreExecutionResponse.block(
                request_id=request.request_id,
                reason=f"Blocked in fallback mode: {signals[0].description}",
                signals=signals,
                confidence=max(s.confidence for s in signals),
            )

        self._stats["local_allows"] += 1
        return PreExecutionResponse.allow(
            request_id=request.request_id,
            reason=f"Allowed in fallback mode: {reason}",
        )

    def _local_validation(
        self,
        request: PreExecutionRequest,
        reason: str
    ) -> PreExecutionResponse:
        """Perform local validation without backend."""
        signals = []

        # Check for loop
        loop_signal = self.detect_local_loop(
            request.trace_context.trace_id,
            request.tool_call.name
        )
        if loop_signal:
            signals.append(loop_signal)

        # Check high iteration count
        if request.context.iteration_count > 50:
            signals.append(ValidationSignal(
                type=SignalType.RATE_LIMIT_RISK,
                confidence=0.8,
                description=f"High iteration count: {request.context.iteration_count}",
                evidence={"iteration_count": request.context.iteration_count},
            ))

        # Check high token usage
        if request.context.total_tokens_used > 100000:
            signals.append(ValidationSignal(
                type=SignalType.RATE_LIMIT_RISK,
                confidence=0.7,
                description=f"High token usage: {request.context.total_tokens_used}",
                evidence={"total_tokens": request.context.total_tokens_used},
            ))

        # Determine decision based on signals
        if signals:
            max_confidence = max(s.confidence for s in signals)
            if max_confidence >= 0.85:
                self._stats["local_blocks"] += 1
                return PreExecutionResponse.block(
                    request_id=request.request_id,
                    reason=f"Local validation: {signals[0].description}",
                    signals=signals,
                    confidence=max_confidence,
                )

        self._stats["local_allows"] += 1
        return PreExecutionResponse(
            request_id=request.request_id,
            decision=GatewayDecision.ALLOW,
            reason=f"Local validation passed: {reason}",
            signals=signals,
            confidence=0.6 if signals else 0.8,
        )

    def _evict_expired_entries(self):
        """Evict expired cache entries."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]

        # If still too large, evict oldest
        if len(self._cache) >= self.max_cache_size:
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].cached_at
            )
            # Remove oldest 20%
            remove_count = len(sorted_entries) // 5
            for key, _ in sorted_entries[:remove_count]:
                del self._cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get fallback statistics."""
        return {
            **self._stats,
            "mode": self.mode.value,
            "cache_size": len(self._cache),
            "tool_history_size": len(self._tool_call_history),
        }

    def reset_stats(self):
        """Reset statistics."""
        self._stats = {
            "fallback_invocations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "local_blocks": 0,
            "local_allows": 0,
        }
