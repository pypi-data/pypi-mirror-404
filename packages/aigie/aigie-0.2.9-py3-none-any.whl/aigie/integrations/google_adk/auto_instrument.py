"""
Google ADK auto-instrumentation.

Automatically patches Google ADK's Runner to inject AigiePlugin
for automatic tracing without requiring manual plugin registration.
"""

import functools
import logging
from typing import Any, Set

logger = logging.getLogger(__name__)

_patched_runners: Set[int] = set()
_original_runner_init = None


def patch_google_adk() -> bool:
    """
    Patch Google ADK Runner for auto-instrumentation.

    This patches Runner.__init__ to automatically add AigiePlugin
    to the plugins list when Runners are created.

    Returns:
        True if patching was successful (or already patched)

    Example:
        >>> import aigie
        >>> aigie.patch("google_adk")
        >>>
        >>> # All Runners are now automatically traced
        >>> from google.adk import Runner, LlmAgent
        >>> runner = Runner(agent=agent, session_service=...)
        >>> async for event in runner.run_async(...):
        ...     process(event)
    """
    global _original_runner_init

    try:
        from google.adk.runners import Runner
    except ImportError:
        try:
            from google.adk import Runner
        except ImportError:
            logger.warning(
                "[AIGIE] Google ADK not available. "
                "Install with: pip install google-adk"
            )
            return False

    # Check if already patched
    if id(Runner.__init__) in _patched_runners:
        logger.debug("[AIGIE] Google ADK Runner already patched")
        return True

    # Store original __init__
    if _original_runner_init is None:
        _original_runner_init = Runner.__init__

    # Create patched __init__
    @functools.wraps(_original_runner_init)
    def patched_init(self, *args, plugins=None, **kwargs):
        """Patched Runner.__init__ that auto-injects AigiePlugin."""
        try:
            from .plugin import AigiePlugin
            from .config import GoogleADKConfig

            # Ensure plugins is a list
            if plugins is None:
                plugins = []
            else:
                plugins = list(plugins)

            # Check if AigiePlugin is already in the list
            has_aigie_plugin = any(
                isinstance(p, AigiePlugin) or
                (hasattr(p, 'name') and p.name == 'aigie')
                for p in plugins
            )

            if not has_aigie_plugin:
                # Create plugin with default config from env
                config = GoogleADKConfig.from_env()
                if config.enabled:
                    aigie_plugin = AigiePlugin(config=config)
                    # Prepend to ensure it's called first
                    plugins = [aigie_plugin] + plugins

                    logger.debug(
                        "[AIGIE] Auto-injecting AigiePlugin into Runner"
                    )

        except Exception as e:
            logger.warning(f"[AIGIE] Failed to auto-inject AigiePlugin: {e}")

        # Call original __init__ with potentially modified plugins
        _original_runner_init(self, *args, plugins=plugins, **kwargs)

    # Patch Runner.__init__
    Runner.__init__ = patched_init
    _patched_runners.add(id(Runner.__init__))

    logger.info("[AIGIE] Google ADK Runner patched for auto-instrumentation")
    return True


def unpatch_google_adk() -> None:
    """
    Remove Google ADK patches.

    Restores Runner.__init__ to its original implementation.
    """
    global _original_runner_init

    try:
        from google.adk.runners import Runner
    except ImportError:
        try:
            from google.adk import Runner
        except ImportError:
            return

    if _original_runner_init is not None:
        Runner.__init__ = _original_runner_init
        _original_runner_init = None
        _patched_runners.clear()
        logger.info("[AIGIE] Google ADK patches removed")


def is_google_adk_patched() -> bool:
    """
    Check if Google ADK is currently patched.

    Returns:
        True if patched, False otherwise
    """
    try:
        from google.adk.runners import Runner
    except ImportError:
        try:
            from google.adk import Runner
        except ImportError:
            return False

    return id(Runner.__init__) in _patched_runners
