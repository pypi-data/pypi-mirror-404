"""Google Gemini provider implementation."""

import os
import time
import threading
from google import genai


class TokenBucket:
    """Thread-safe token bucket rate limiter."""

    def __init__(self, rpm: int, burst_multiplier: float = 0.1):
        """
        Initialize token bucket.

        Args:
            rpm: Requests per minute limit
            burst_multiplier: Burst capacity as fraction of RPM (default 10%)
        """
        self.rpm = rpm
        self.refill_rate = rpm / 60.0  # tokens per second
        self.capacity = max(1, int(rpm * burst_multiplier))  # burst capacity
        self.tokens = self.capacity  # start full
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def acquire(self) -> float:
        """
        Acquire a token, blocking if necessary.

        Returns:
            Time spent waiting (0 if no wait needed)
        """
        with self._lock:
            now = time.time()

            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            if self.tokens >= 1:
                # Token available, take it
                self.tokens -= 1
                return 0.0
            else:
                # Calculate wait time for next token
                wait_time = (1 - self.tokens) / self.refill_rate
                self.tokens = 0
                self.last_refill = now + wait_time

        # Wait outside the lock so other threads can queue up
        time.sleep(wait_time)

        with self._lock:
            # We've waited, now we have our token
            return wait_time


class GeminiProvider:
    """Google Gemini API provider with token bucket rate limiting and retry."""

    # Rate limits by model (requests per minute)
    RATE_LIMITS = {
        "gemini-2.5-flash-lite": 4000,  # 4K RPM
        "gemini-2.5-flash": 1000,       # 1K RPM
        "gemini-2.5-pro": 150,          # 150 RPM
        "gemini-2.0-flash": 2000,       # 2K RPM
        "gemini-2.0-flash-lite": 4000,  # 4K RPM
    }

    def __init__(self, model: str = "gemini-2.0-flash", api_key: str = None):
        self.model = model
        api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)

        # Token bucket rate limiting (10% burst capacity, 10% safety margin on RPM)
        rpm = self.RATE_LIMITS.get(model, 1000)
        safe_rpm = int(rpm * 0.9)  # 10% safety margin
        self._bucket = TokenBucket(safe_rpm, burst_multiplier=0.1)

        self.max_retries = 5
        self.base_delay = 1.0

    def _rate_limit(self):
        """Acquire a token from the bucket."""
        self._bucket.acquire()

    def complete(self, prompt: str, system: str = "") -> str:
        """Send prompt to Gemini and return response with retry logic."""
        if system:
            full_prompt = f"{system}\n\n{prompt}"
        else:
            full_prompt = prompt

        last_exception = None
        delay = self.base_delay

        for attempt in range(self.max_retries + 1):
            try:
                self._rate_limit()
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt,
                )
                return response.text
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()

                # Retry on rate limit, resource exhausted, or transient errors
                if "429" in str(e) or "503" in str(e) or "resource_exhausted" in error_str or "rate" in error_str or "unavailable" in error_str:
                    if attempt < self.max_retries:
                        time.sleep(delay)
                        delay = min(delay * 2, 30.0)  # Cap at 30s
                        continue

                # For other errors, raise immediately
                raise

        raise last_exception

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def rpm(self) -> int:
        """Return the rate limit (requests per minute) for this model."""
        return self.RATE_LIMITS.get(self.model, 1000)

    @classmethod
    def get_default_workers(cls, model: str) -> int:
        """Calculate optimal worker count based on model's rate limit.

        Uses RPM / 30 as a heuristic (roughly 2 requests/sec per worker).

        Args:
            model: Model name

        Returns:
            Recommended number of parallel workers
        """
        rpm = cls.RATE_LIMITS.get(model, 1000)
        return max(1, rpm // 30)
