"""
Instructor integration for Aigie.

This module provides automatic tracing for Instructor, the popular structured
output library for LLMs. Captures structured extraction calls, validation
retries, and model schema information.

Usage:
    # Manual handler usage
    from aigie.integrations.instructor import InstructorHandler

    handler = InstructorHandler(trace_name="extraction-job")
    # ... use with instructor

    # Auto-instrumentation
    from aigie.integrations.instructor import patch_instructor
    patch_instructor()  # Patches instructor.patch(), instructor.from_openai(), etc.
"""

from .handler import InstructorHandler
from .auto_instrument import (
    patch_instructor,
    unpatch_instructor,
    is_instructor_patched,
)
from .config import InstructorConfig

__all__ = [
    "InstructorHandler",
    "InstructorConfig",
    "patch_instructor",
    "unpatch_instructor",
    "is_instructor_patched",
]
