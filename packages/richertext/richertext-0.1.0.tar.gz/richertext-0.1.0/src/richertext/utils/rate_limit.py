"""Rate limiting and retry utilities."""

import time
from functools import wraps


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
):
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()

                    # Only retry on rate limit or resource exhausted errors
                    if "429" in str(e) or "resource_exhausted" in error_str or "rate" in error_str:
                        if attempt < max_retries:
                            time.sleep(delay)
                            delay = min(delay * exponential_base, max_delay)
                            continue

                    # For other errors, raise immediately
                    raise

            # If we exhausted all retries, raise the last exception
            raise last_exception

        return wrapper
    return decorator


class RateLimiter:
    """Simple rate limiter that adds delay between calls."""

    def __init__(self, min_delay: float = 1.0):
        self.min_delay = min_delay
        self.last_call_time = 0

    def wait(self):
        """Wait if needed to respect rate limit."""
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_call_time = time.time()
