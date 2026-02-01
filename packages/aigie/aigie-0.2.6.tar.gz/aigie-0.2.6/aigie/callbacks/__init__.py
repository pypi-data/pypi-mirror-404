"""
Aigie Callbacks - Custom callback handlers for observability data.

This module provides callback handlers that allow sending span/trace data
to custom destinations, inspired by LiteLLM's GenericAPILogger pattern.

Available Callbacks:
- GenericWebhookCallback: Send span data to any HTTP endpoint
- ConsoleCallback: Log spans to console (for debugging)
- FileCallback: Write spans to file

Usage:
    from aigie.callbacks import GenericWebhookCallback

    # Create webhook callback
    webhook = GenericWebhookCallback(
        endpoint="https://my-service.com/logs",
        headers={"Authorization": "Bearer token123"}
    )

    # Add to Aigie
    aigie.add_callback(webhook)
"""

from .generic_webhook import GenericWebhookCallback
from .base import BaseCallback, CallbackEvent, CallbackEventType

__all__ = [
    "GenericWebhookCallback",
    "BaseCallback",
    "CallbackEvent",
    "CallbackEventType",
]
