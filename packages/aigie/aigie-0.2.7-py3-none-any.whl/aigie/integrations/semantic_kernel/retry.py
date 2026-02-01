"""
Retry and timeout utilities for Semantic Kernel integration.

Provides decorators and context managers for handling transient failures
with exponential backoff and configurable timeouts for kernel functions,
plugins, and planners.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, List, Optional, Type, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Common transient errors that should be retried
TRANSIENT_ERRORS = (
    TimeoutError,
    ConnectionError,
    ConnectionResetError,
    ConnectionRefusedError,
    OSError,  # Includes network errors
)

# Semantic Kernel-specific retryable errors
SK_RETRYABLE_ERRORS = (
    # Connector/service errors
    "ServiceResponseException",
    "KernelException",
    "FunctionExecutionException",
    # Planner errors that might be transient
    "PlannerException",
    # API rate limits
    "RateLimitError",
    # Temporary service errors
    "ServiceUnavailableError",
)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, last_error: Optional[Exception] = None, attempts: int = 0):
        super().__init__(message)
        self.last_error = last_error
        self.attempts = attempts


class TimeoutExceededError(Exception):
    """Raised when an operation exceeds its timeout."""

    def __init__(self, message: str, timeout: float, operation: str = ""):
        super().__init__(message)
        self.timeout = timeout
        self.operation = operation


class KernelFunctionError(Exception):
    """Raised when a Semantic Kernel function fails after all retries."""

    def __init__(
        self,
        message: str,
        function_name: str = "",
        plugin_name: str = "",
        last_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.function_name = function_name
        self.plugin_name = plugin_name
        self.last_error = last_error


class PlanExecutionError(Exception):
    """Raised when a Semantic Kernel plan fails after all retries."""

    def __init__(
        self,
        message: str,
        plan_type: str = "",
        step_failed: Optional[int] = None,
        last_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.plan_type = plan_type
        self.step_failed = step_failed
        self.last_error = last_error


def is_kernel_error(e: Exception) -> bool:
    """Check if an exception is a Semantic Kernel-specific error."""
    error_type = type(e).__name__
    module = getattr(type(e), '__module__', '')

    # Check against known SK error types
    if error_type in SK_RETRYABLE_ERRORS:
        return True

    # Check if from semantic_kernel module
    if 'semantic_kernel' in module.lower():
        return True

    return False


def is_retryable_error(e: Exception) -> bool:
    """Check if an exception should be retried."""
    error_type = type(e).__name__
    error_str = str(e).lower()

    # Check against known retryable types
    if error_type in SK_RETRYABLE_ERRORS:
        return True

    # Check for rate limit indicators
    if "rate" in error_str and "limit" in error_str:
        return True

    # Check for temporary service issues
    if any(term in error_str for term in ["temporarily", "unavailable", "503", "429", "timeout"]):
        return True

    # Check if it's a transient network error
    if isinstance(e, TRANSIENT_ERRORS):
        return True

    return False


async def with_timeout(
    coro: Any,
    timeout: float,
    operation_name: str = "operation",
) -> Any:
    """Execute a coroutine with a timeout.

    Args:
        coro: The coroutine to execute
        timeout: Timeout in seconds
        operation_name: Name of the operation (for error messages)

    Returns:
        The result of the coroutine

    Raises:
        TimeoutExceededError: If the operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutExceededError(
            f"{operation_name} timed out after {timeout}s",
            timeout=timeout,
            operation=operation_name,
        )


async def with_retry(
    func: Callable[..., Any],
    *args,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_on: Optional[List[Type[Exception]]] = None,
    operation_name: str = "operation",
    **kwargs,
) -> Any:
    """Execute a function with retry logic.

    Uses exponential backoff between retries.

    Args:
        func: The async function to execute
        *args: Positional arguments for the function
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (doubles each retry)
        retry_on: List of exception types to retry on (None = use defaults)
        operation_name: Name of the operation (for logging)
        **kwargs: Keyword arguments for the function

    Returns:
        The result of the function

    Raises:
        RetryExhaustedError: If all retries are exhausted
    """
    retry_errors = tuple(retry_on) if retry_on else TRANSIENT_ERRORS
    last_error: Optional[Exception] = None
    delay = retry_delay

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        except retry_errors as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(
                    f"{operation_name} failed after {max_retries + 1} attempts: {e}"
                )

        except Exception as e:
            # Check for SK-specific retryable errors
            if is_retryable_error(e):
                last_error = e
                if attempt < max_retries:
                    logger.warning(
                        f"{operation_name} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.error(
                        f"{operation_name} failed after {max_retries + 1} attempts: {e}"
                    )
            else:
                # Non-retryable error
                raise

    raise RetryExhaustedError(
        f"{operation_name} failed after {max_retries + 1} attempts",
        last_error=last_error,
        attempts=max_retries + 1,
    )


async def with_timeout_and_retry(
    func: Callable[..., Any],
    *args,
    timeout: float = 30.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_on: Optional[List[Type[Exception]]] = None,
    operation_name: str = "operation",
    **kwargs,
) -> Any:
    """Execute a function with both timeout and retry logic.

    Each attempt has its own timeout. Retries are attempted if the operation
    times out or encounters a transient error.

    Args:
        func: The async function to execute
        *args: Positional arguments for the function
        timeout: Timeout per attempt in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries
        retry_on: List of exception types to retry on
        operation_name: Name of the operation
        **kwargs: Keyword arguments for the function

    Returns:
        The result of the function
    """
    # Include TimeoutExceededError in retryable errors
    retry_errors = list(retry_on) if retry_on else list(TRANSIENT_ERRORS)
    retry_errors.append(TimeoutExceededError)
    retry_errors.append(asyncio.TimeoutError)

    async def timed_func(*a, **kw):
        if asyncio.iscoroutinefunction(func):
            return await with_timeout(func(*a, **kw), timeout, operation_name)
        else:
            return func(*a, **kw)

    return await with_retry(
        timed_func,
        *args,
        max_retries=max_retries,
        retry_delay=retry_delay,
        retry_on=retry_errors,
        operation_name=operation_name,
        **kwargs,
    )


def retry_decorator(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_on: Optional[List[Type[Exception]]] = None,
    timeout: Optional[float] = None,
):
    """Decorator to add retry logic to an async function.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries
        retry_on: List of exception types to retry on
        timeout: Optional timeout per attempt

    Example:
        @retry_decorator(max_retries=3, timeout=30.0)
        async def my_kernel_function():
            return await kernel.invoke(my_plugin.my_function)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            operation_name = func.__name__

            if timeout:
                return await with_timeout_and_retry(
                    func,
                    *args,
                    timeout=timeout,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    retry_on=retry_on,
                    operation_name=operation_name,
                    **kwargs,
                )
            else:
                return await with_retry(
                    func,
                    *args,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    retry_on=retry_on,
                    operation_name=operation_name,
                    **kwargs,
                )

        return wrapper
    return decorator


class FunctionRetryContext:
    """Context manager for Semantic Kernel function retries with metrics tracking.

    Tracks retry attempts, total time, and errors for observability.

    Example:
        async with FunctionRetryContext(
            max_retries=3,
            function_name="summarize",
            plugin_name="text_plugin"
        ) as ctx:
            result = await ctx.execute(kernel.invoke, text_plugin.summarize, input_text)
            print(f"Completed in {ctx.total_time}s with {ctx.attempts} attempts")
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        retry_on: Optional[List[Type[Exception]]] = None,
        function_name: str = "",
        plugin_name: str = "",
        operation: str = "function_invoke",
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.retry_on = retry_on
        self.function_name = function_name
        self.plugin_name = plugin_name
        self.operation = operation

        # Metrics
        self.attempts = 0
        self.total_time = 0.0
        self.errors: List[Exception] = []
        self.success = False
        self._start_time: Optional[float] = None

    async def __aenter__(self) -> "FunctionRetryContext":
        self._start_time = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._start_time:
            self.total_time = time.perf_counter() - self._start_time
        return False  # Don't suppress exceptions

    async def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute the function with retry logic.

        Args:
            func: The function to execute (e.g., kernel.invoke)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of the function
        """
        retry_errors = tuple(self.retry_on) if self.retry_on else TRANSIENT_ERRORS
        delay = self.retry_delay

        for attempt in range(self.max_retries + 1):
            self.attempts = attempt + 1

            try:
                if self.timeout:
                    result = await with_timeout(
                        func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else asyncio.coroutine(lambda: func(*args, **kwargs))(),
                        self.timeout,
                        self.operation,
                    )
                else:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                self.success = True
                return result

            except (TimeoutExceededError, asyncio.TimeoutError, *retry_errors) as e:
                self.errors.append(e)

                if attempt < self.max_retries:
                    logger.warning(
                        f"{self.operation} failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    raise KernelFunctionError(
                        f"{self.operation} failed after {self.max_retries + 1} attempts",
                        function_name=self.function_name,
                        plugin_name=self.plugin_name,
                        last_error=e,
                    )

            except Exception as e:
                self.errors.append(e)

                if is_retryable_error(e):
                    if attempt < self.max_retries:
                        logger.warning(
                            f"{self.operation} failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                        )
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        raise KernelFunctionError(
                            f"{self.operation} failed after {self.max_retries + 1} attempts",
                            function_name=self.function_name,
                            plugin_name=self.plugin_name,
                            last_error=e,
                        )
                else:
                    raise

    def get_metrics(self) -> dict:
        """Get retry metrics for tracing."""
        return {
            "attempts": self.attempts,
            "total_time": self.total_time,
            "success": self.success,
            "error_count": len(self.errors),
            "function_name": self.function_name,
            "plugin_name": self.plugin_name,
            "errors": [str(e) for e in self.errors[-3:]],  # Last 3 errors
        }


class PlanRetryContext:
    """Context manager for Semantic Kernel plan execution with metrics tracking.

    Tracks retry attempts, step progress, and errors for observability.

    Example:
        async with PlanRetryContext(max_retries=3, plan_type="stepwise") as ctx:
            result = await ctx.execute(planner.invoke, kernel, goal)
            print(f"Plan completed in {ctx.total_time}s with {ctx.steps_executed} steps")
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        retry_on: Optional[List[Type[Exception]]] = None,
        plan_type: str = "sequential",
        operation: str = "plan_invoke",
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.retry_on = retry_on
        self.plan_type = plan_type
        self.operation = operation

        # Metrics
        self.attempts = 0
        self.total_time = 0.0
        self.errors: List[Exception] = []
        self.success = False
        self.steps_executed = 0
        self.step_failed: Optional[int] = None
        self._start_time: Optional[float] = None

    async def __aenter__(self) -> "PlanRetryContext":
        self._start_time = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._start_time:
            self.total_time = time.perf_counter() - self._start_time
        return False  # Don't suppress exceptions

    async def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute the plan with retry logic.

        Args:
            func: The function to execute (e.g., planner.invoke)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of the plan execution
        """
        retry_errors = tuple(self.retry_on) if self.retry_on else TRANSIENT_ERRORS
        delay = self.retry_delay

        for attempt in range(self.max_retries + 1):
            self.attempts = attempt + 1
            self.steps_executed = 0
            self.step_failed = None

            try:
                if self.timeout:
                    result = await with_timeout(
                        func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else asyncio.coroutine(lambda: func(*args, **kwargs))(),
                        self.timeout,
                        self.operation,
                    )
                else:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                self.success = True
                return result

            except (TimeoutExceededError, asyncio.TimeoutError, *retry_errors) as e:
                self.errors.append(e)

                if attempt < self.max_retries:
                    logger.warning(
                        f"{self.operation} failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    raise PlanExecutionError(
                        f"{self.operation} failed after {self.max_retries + 1} attempts",
                        plan_type=self.plan_type,
                        step_failed=self.step_failed,
                        last_error=e,
                    )

            except Exception as e:
                self.errors.append(e)

                # Try to extract step information from error
                error_str = str(e)
                if "step" in error_str.lower():
                    import re
                    match = re.search(r'step\s*(\d+)', error_str.lower())
                    if match:
                        self.step_failed = int(match.group(1))

                if is_retryable_error(e):
                    if attempt < self.max_retries:
                        logger.warning(
                            f"{self.operation} failed at step {self.step_failed or 'unknown'} "
                            f"(attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                        )
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        raise PlanExecutionError(
                            f"{self.operation} failed after {self.max_retries + 1} attempts",
                            plan_type=self.plan_type,
                            step_failed=self.step_failed,
                            last_error=e,
                        )
                else:
                    raise

    def get_metrics(self) -> dict:
        """Get retry metrics for tracing."""
        return {
            "attempts": self.attempts,
            "total_time": self.total_time,
            "success": self.success,
            "error_count": len(self.errors),
            "plan_type": self.plan_type,
            "steps_executed": self.steps_executed,
            "step_failed": self.step_failed,
            "errors": [str(e) for e in self.errors[-3:]],  # Last 3 errors
        }
