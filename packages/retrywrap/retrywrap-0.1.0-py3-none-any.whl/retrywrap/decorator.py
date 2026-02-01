"""
Core retry decorator implementation.
"""

import time
import functools
from typing import Callable, Tuple, Type, Union, Optional, Any


def retry(
    _func: Optional[Callable] = None,
    *,
    attempts: int = 3,
    delay: Union[int, float] = 1,
    backoff: Union[int, float] = 1,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    A decorator that retries a function on failure.

    Can be used with or without parentheses:
        @retry
        def func(): ...

        @retry(attempts=5, delay=2)
        def func(): ...

    Args:
        _func: The function to wrap (used when decorator is applied without parentheses)
        attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1)
        backoff: Multiplier for delay after each retry (default: 1, no backoff)
        exceptions: Tuple of exception types to catch and retry (default: all exceptions)

    Returns:
        The decorated function with retry behavior.

    Raises:
        The last exception raised if all retry attempts fail.

    Examples:
        >>> @retry
        ... def fetch_data():
        ...     # Will retry 3 times with 1 second delay
        ...     pass

        >>> @retry(attempts=5, delay=0.5, backoff=2, exceptions=(TimeoutError,))
        ... def call_api():
        ...     # Will retry 5 times, with exponential backoff
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: Optional[Exception] = None

            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff

            # All attempts failed, raise the last exception
            if last_exception is not None:
                raise last_exception

        return wrapper

    # Handle both @retry and @retry(...) syntax
    if _func is not None:
        # Called without parentheses: @retry
        return decorator(_func)
    else:
        # Called with parentheses: @retry(...) or @retry()
        return decorator
