"""
Mode Controller - Dynamic Observe/Autonomous Mode Switching.

This module provides dynamic mode switching between "observe" and
"autonomous" operational modes. It coordinates with the backend
to determine the appropriate mode and propagates changes to other
SDK components.

Modes:
- observe: Monitor and recommend, don't auto-fix
- autonomous: Active interception and automatic fixes

Auto-Transition Criteria:
- samples >= 20: Sufficient data collected
- success_rate >= 0.85: 85% success rate on recommendations
- confidence >= 0.80: 80% confidence in patterns

Usage:
    from aigie import ModeController, Aigie

    # Initialize with Aigie client
    aigie = Aigie(api_key="...")
    controller = ModeController(aigie)

    # Get current mode from backend
    mode = await controller.get_mode_from_backend()

    # Set mode
    await controller.set_mode("autonomous")

    # Register for mode changes
    controller.on_mode_change(my_callback)

    # Check eligibility for autonomous mode
    eligible = await controller.check_autonomous_eligibility()
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Aigie
    from .gateway.websocket_client import GatewayWebSocketClient
    from .runtime.remediation_loop import RemediationLoop

logger = logging.getLogger("aigie.mode_controller")


class OperationMode(str, Enum):
    """Operational modes for the SDK."""
    OBSERVE = "observe"
    AUTONOMOUS = "autonomous"


class AutonomyLevel(str, Enum):
    """Autonomy levels matching backend configuration."""
    SUGGEST = "suggest"       # Only suggest fixes (observe mode)
    SEMI_AUTO = "semi_auto"   # Auto-fix with confirmation
    FULL_AUTO = "full_auto"   # Fully automatic fixes


@dataclass
class ModeConfig:
    """Configuration for mode controller."""
    # Default mode
    default_mode: OperationMode = OperationMode.OBSERVE

    # Auto-transition thresholds (matching backend)
    min_samples_for_autonomous: int = 20
    min_success_rate_for_autonomous: float = 0.85
    min_confidence_for_autonomous: float = 0.80

    # Sync settings
    sync_with_backend: bool = True
    sync_interval_sec: float = 30.0

    # Safety
    require_explicit_opt_in: bool = True
    auto_fallback_on_failure: bool = True
    failure_threshold_for_fallback: int = 3


@dataclass
class ModeState:
    """Current mode state."""
    mode: OperationMode
    autonomy_level: AutonomyLevel = AutonomyLevel.SUGGEST
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: str = "sdk"  # "sdk", "backend", "user"

    # Eligibility metrics
    samples_collected: int = 0
    success_rate: float = 0.0
    confidence: float = 0.0

    # Status
    is_eligible_for_autonomous: bool = False
    is_explicitly_opted_in: bool = False
    consecutive_failures: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "autonomy_level": self.autonomy_level.value,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": self.updated_by,
            "samples_collected": self.samples_collected,
            "success_rate": self.success_rate,
            "confidence": self.confidence,
            "is_eligible_for_autonomous": self.is_eligible_for_autonomous,
            "is_explicitly_opted_in": self.is_explicitly_opted_in,
            "consecutive_failures": self.consecutive_failures,
        }


@dataclass
class ModeMetrics:
    """Metrics for mode controller."""
    mode_changes: int = 0
    backend_syncs: int = 0
    sync_failures: int = 0
    eligibility_checks: int = 0
    auto_fallbacks: int = 0
    listener_notifications: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode_changes": self.mode_changes,
            "backend_syncs": self.backend_syncs,
            "sync_failures": self.sync_failures,
            "eligibility_checks": self.eligibility_checks,
            "auto_fallbacks": self.auto_fallbacks,
            "listener_notifications": self.listener_notifications,
        }


class ModeController:
    """
    Dynamic mode switching between observe and autonomous.

    Coordinates mode changes between SDK components and the backend.
    Supports automatic eligibility checking and mode transitions.

    Features:
    - Query backend for current mode setting
    - Subscribe to mode changes via WebSocket
    - Propagate mode changes to gateway client and remediation loop
    - Auto-check eligibility for autonomous mode transition
    """

    def __init__(
        self,
        aigie: Optional["Aigie"] = None,
        *,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[ModeConfig] = None,
        gateway_client: Optional["GatewayWebSocketClient"] = None,
        remediation_loop: Optional["RemediationLoop"] = None,
    ):
        """
        Initialize the mode controller.

        Args:
            aigie: Aigie client instance
            api_url: Backend API URL (if not using aigie)
            api_key: API key (if not using aigie)
            config: Mode controller configuration
            gateway_client: Gateway WebSocket client to update
            remediation_loop: Remediation loop to update
        """
        self._aigie = aigie
        self._api_url = api_url
        self._api_key = api_key
        self._config = config or ModeConfig()

        # Connected components
        self._gateway_client = gateway_client
        self._remediation_loop = remediation_loop

        # Current state
        self._state = ModeState(mode=self._config.default_mode)

        # Mode change listeners
        self._mode_listeners: List[Callable[[OperationMode, OperationMode], Awaitable[None]]] = []

        # Background task
        self._sync_task: Optional[asyncio.Task] = None

        # Metrics
        self._metrics = ModeMetrics()

        # Lock for thread safety
        self._lock = asyncio.Lock()

    @property
    def current_mode(self) -> OperationMode:
        """Get the current operational mode."""
        return self._state.mode

    @property
    def autonomy_level(self) -> AutonomyLevel:
        """Get the current autonomy level."""
        return self._state.autonomy_level

    @property
    def is_autonomous(self) -> bool:
        """Check if currently in autonomous mode."""
        return self._state.mode == OperationMode.AUTONOMOUS

    @property
    def is_observe(self) -> bool:
        """Check if currently in observe mode."""
        return self._state.mode == OperationMode.OBSERVE

    def set_gateway_client(self, client: "GatewayWebSocketClient") -> None:
        """Set the gateway client to update on mode changes."""
        self._gateway_client = client

    def set_remediation_loop(self, loop: "RemediationLoop") -> None:
        """Set the remediation loop to update on mode changes."""
        self._remediation_loop = loop

    async def get_mode_from_backend(self) -> OperationMode:
        """
        Query the backend for the current mode setting.

        Returns:
            Current OperationMode from backend
        """
        api_url = self._get_api_url()
        api_key = self._get_api_key()

        if not api_url or not api_key:
            logger.debug("No API URL/key, using local mode")
            return self._state.mode

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {api_key}"}

                async with session.get(
                    f"{api_url}/api/v1/gateway/mode",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        mode_str = data.get("mode", "observe")
                        mode = OperationMode(mode_str)

                        # Update state
                        async with self._lock:
                            if mode != self._state.mode:
                                await self._transition_mode(mode, "backend")

                            # Update additional state from backend
                            self._state.samples_collected = data.get("samples_collected", 0)
                            self._state.success_rate = data.get("success_rate", 0.0)
                            self._state.confidence = data.get("confidence", 0.0)
                            self._state.is_eligible_for_autonomous = data.get(
                                "eligible_for_autonomous", False
                            )

                        self._metrics.backend_syncs += 1
                        return mode

        except ImportError:
            logger.debug("aiohttp not installed")
        except Exception as e:
            logger.warning(f"Failed to get mode from backend: {e}")
            self._metrics.sync_failures += 1

        return self._state.mode

    async def set_mode(
        self,
        mode: Literal["observe", "autonomous"],
        *,
        sync_to_backend: bool = True,
    ) -> bool:
        """
        Set the operational mode.

        Args:
            mode: Mode to set ("observe" or "autonomous")
            sync_to_backend: Whether to sync the change to backend

        Returns:
            True if mode was changed successfully
        """
        new_mode = OperationMode(mode)

        # Check if autonomous mode requires explicit opt-in
        if (
            new_mode == OperationMode.AUTONOMOUS
            and self._config.require_explicit_opt_in
            and not self._state.is_explicitly_opted_in
        ):
            # Check eligibility first
            if not await self.check_autonomous_eligibility():
                logger.warning("Not eligible for autonomous mode")
                return False

        async with self._lock:
            if new_mode == self._state.mode:
                return True  # Already in desired mode

            # Transition mode
            success = await self._transition_mode(new_mode, "user")

            if success and new_mode == OperationMode.AUTONOMOUS:
                self._state.is_explicitly_opted_in = True

            # Sync to backend
            if success and sync_to_backend:
                await self._sync_mode_to_backend(new_mode)

            return success

    async def _transition_mode(
        self,
        new_mode: OperationMode,
        source: str,
    ) -> bool:
        """
        Internal method to transition between modes.

        Args:
            new_mode: Mode to transition to
            source: Source of the transition ("sdk", "backend", "user")

        Returns:
            True if transition was successful
        """
        old_mode = self._state.mode
        logger.info(f"Transitioning mode: {old_mode.value} -> {new_mode.value} (source: {source})")

        # Update state
        self._state.mode = new_mode
        self._state.updated_at = datetime.utcnow()
        self._state.updated_by = source

        # Update autonomy level
        if new_mode == OperationMode.AUTONOMOUS:
            self._state.autonomy_level = AutonomyLevel.FULL_AUTO
        else:
            self._state.autonomy_level = AutonomyLevel.SUGGEST

        # Propagate to connected components
        await self._propagate_mode_change(new_mode)

        # Notify listeners
        await self._notify_listeners(old_mode, new_mode)

        self._metrics.mode_changes += 1
        return True

    async def _propagate_mode_change(self, mode: OperationMode) -> None:
        """Propagate mode change to connected SDK components."""
        # Update remediation loop
        if self._remediation_loop:
            try:
                from .runtime.remediation_loop import OperationalMode as RLMode

                if mode == OperationMode.AUTONOMOUS:
                    self._remediation_loop.config.mode = RLMode.AUTONOMOUS
                    self._remediation_loop.config.auto_fix_enabled = True
                else:
                    self._remediation_loop.config.mode = RLMode.RECOMMENDATION
                    self._remediation_loop.config.auto_fix_enabled = False

                logger.debug(f"Updated remediation loop mode to {mode.value}")
            except Exception as e:
                logger.warning(f"Failed to update remediation loop: {e}")

        # Gateway client doesn't need mode update - it always validates
        # Mode affects how remediation loop responds to validation results

    async def _notify_listeners(
        self,
        old_mode: OperationMode,
        new_mode: OperationMode,
    ) -> None:
        """Notify registered listeners of mode change."""
        for listener in self._mode_listeners:
            try:
                await listener(old_mode, new_mode)
                self._metrics.listener_notifications += 1
            except Exception as e:
                logger.warning(f"Mode change listener error: {e}")

    def on_mode_change(
        self,
        callback: Callable[[OperationMode, OperationMode], Awaitable[None]],
    ) -> None:
        """
        Register callback for mode changes.

        Args:
            callback: Async callback that receives (old_mode, new_mode)
        """
        self._mode_listeners.append(callback)

    def remove_mode_change_listener(
        self,
        callback: Callable[[OperationMode, OperationMode], Awaitable[None]],
    ) -> bool:
        """Remove a mode change listener."""
        try:
            self._mode_listeners.remove(callback)
            return True
        except ValueError:
            return False

    async def check_autonomous_eligibility(self) -> bool:
        """
        Check if the system is eligible for autonomous mode.

        Criteria:
        - samples >= 20: Sufficient data collected
        - success_rate >= 0.85: 85% success rate
        - confidence >= 0.80: 80% confidence

        Returns:
            True if eligible for autonomous mode
        """
        self._metrics.eligibility_checks += 1

        # First, try to get fresh data from backend
        await self.get_mode_from_backend()

        # Check thresholds
        samples_ok = self._state.samples_collected >= self._config.min_samples_for_autonomous
        success_ok = self._state.success_rate >= self._config.min_success_rate_for_autonomous
        confidence_ok = self._state.confidence >= self._config.min_confidence_for_autonomous

        is_eligible = samples_ok and success_ok and confidence_ok
        self._state.is_eligible_for_autonomous = is_eligible

        if not is_eligible:
            reasons = []
            if not samples_ok:
                reasons.append(
                    f"samples ({self._state.samples_collected}/{self._config.min_samples_for_autonomous})"
                )
            if not success_ok:
                reasons.append(
                    f"success_rate ({self._state.success_rate:.0%}/{self._config.min_success_rate_for_autonomous:.0%})"
                )
            if not confidence_ok:
                reasons.append(
                    f"confidence ({self._state.confidence:.0%}/{self._config.min_confidence_for_autonomous:.0%})"
                )
            logger.debug(f"Not eligible for autonomous mode: {', '.join(reasons)}")

        return is_eligible

    async def record_fix_outcome(self, success: bool) -> None:
        """
        Record the outcome of a fix attempt.

        Used to track success rate and potentially trigger auto-fallback.

        Args:
            success: Whether the fix was successful
        """
        async with self._lock:
            if success:
                self._state.consecutive_failures = 0
            else:
                self._state.consecutive_failures += 1

                # Check for auto-fallback
                if (
                    self._config.auto_fallback_on_failure
                    and self._state.mode == OperationMode.AUTONOMOUS
                    and self._state.consecutive_failures >= self._config.failure_threshold_for_fallback
                ):
                    logger.warning(
                        f"Auto-falling back to observe mode after "
                        f"{self._state.consecutive_failures} consecutive failures"
                    )
                    await self._transition_mode(OperationMode.OBSERVE, "auto_fallback")
                    self._metrics.auto_fallbacks += 1

    async def _sync_mode_to_backend(self, mode: OperationMode) -> None:
        """Sync the mode setting to the backend."""
        api_url = self._get_api_url()
        api_key = self._get_api_key()

        if not api_url or not api_key:
            return

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

                async with session.put(
                    f"{api_url}/api/v1/gateway/mode",
                    json={"mode": mode.value},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status in (200, 201):
                        self._metrics.backend_syncs += 1
                    else:
                        logger.warning(f"Failed to sync mode to backend: {response.status}")
                        self._metrics.sync_failures += 1

        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Failed to sync mode to backend: {e}")
            self._metrics.sync_failures += 1

    def _get_api_url(self) -> Optional[str]:
        """Get API URL from aigie client or direct config."""
        if self._aigie:
            return getattr(self._aigie, '_api_url', None) or getattr(self._aigie, 'api_url', None)
        return self._api_url

    def _get_api_key(self) -> Optional[str]:
        """Get API key from aigie client or direct config."""
        if self._aigie:
            return getattr(self._aigie, '_api_key', None) or getattr(self._aigie, 'api_key', None)
        return self._api_key

    async def start_sync(self) -> None:
        """Start background sync with backend."""
        if self._config.sync_with_backend:
            if self._sync_task is None or self._sync_task.done():
                self._sync_task = asyncio.create_task(self._sync_loop())
                logger.debug("Started mode sync background task")

    async def stop_sync(self) -> None:
        """Stop background sync."""
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

    async def _sync_loop(self) -> None:
        """Background loop for syncing mode with backend."""
        while True:
            try:
                await asyncio.sleep(self._config.sync_interval_sec)
                await self.get_mode_from_backend()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Mode sync error: {e}")

    def get_state(self) -> ModeState:
        """Get current mode state."""
        return self._state

    def get_metrics(self) -> ModeMetrics:
        """Get mode controller metrics."""
        return self._metrics

    def get_stats(self) -> Dict[str, Any]:
        """Get mode controller statistics."""
        return {
            **self._state.to_dict(),
            **self._metrics.to_dict(),
            "config": {
                "min_samples": self._config.min_samples_for_autonomous,
                "min_success_rate": self._config.min_success_rate_for_autonomous,
                "min_confidence": self._config.min_confidence_for_autonomous,
                "require_explicit_opt_in": self._config.require_explicit_opt_in,
            },
            "listeners_registered": len(self._mode_listeners),
        }

    def get_eligibility_status(self) -> Dict[str, Any]:
        """Get detailed eligibility status for autonomous mode."""
        return {
            "is_eligible": self._state.is_eligible_for_autonomous,
            "samples": {
                "current": self._state.samples_collected,
                "required": self._config.min_samples_for_autonomous,
                "met": self._state.samples_collected >= self._config.min_samples_for_autonomous,
            },
            "success_rate": {
                "current": self._state.success_rate,
                "required": self._config.min_success_rate_for_autonomous,
                "met": self._state.success_rate >= self._config.min_success_rate_for_autonomous,
            },
            "confidence": {
                "current": self._state.confidence,
                "required": self._config.min_confidence_for_autonomous,
                "met": self._state.confidence >= self._config.min_confidence_for_autonomous,
            },
            "is_opted_in": self._state.is_explicitly_opted_in,
        }


# Convenience function for global mode controller
_global_controller: Optional[ModeController] = None


def get_mode_controller() -> Optional[ModeController]:
    """Get the global mode controller instance."""
    return _global_controller


def set_mode_controller(controller: ModeController) -> None:
    """Set the global mode controller instance."""
    global _global_controller
    _global_controller = controller
