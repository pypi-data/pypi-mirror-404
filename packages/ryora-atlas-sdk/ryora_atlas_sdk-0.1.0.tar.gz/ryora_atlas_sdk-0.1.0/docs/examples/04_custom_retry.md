# Custom Retry Configuration

This example demonstrates how to customize retry behavior beyond the SDK defaults.

## Use Case: Mission-Critical Operations

You're running a mission-critical batch job that needs:

- More aggressive retries for important operations
- Custom backoff strategies
- Circuit breaker patterns for degraded services

## Prerequisites

- Atlas SDK installed
- Optional: `tenacity` library (already included with SDK)

## Complete Example

```python
"""
Example: Custom Retry Configuration
Use Case: Mission-critical batch processing with custom retry strategies

This example shows how to:
- Configure custom retry counts and backoff
- Implement circuit breaker patterns
- Create operation-specific retry policies
"""

import asyncio
import time
from dataclasses import dataclass, field
from functools import wraps

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    wait_fixed,
    wait_random_exponential,
)

from atlas_sdk import ControlPlaneClient
from atlas_sdk.exceptions import AtlasAPIError


# =============================================================================
# Pattern 1: Using tenacity directly
# =============================================================================


async def create_with_aggressive_retry(client: ControlPlaneClient, data):
    """
    Create a resource with aggressive retry for critical operations.
    More retries, longer total wait time.
    """
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type((AtlasAPIError,)),
        stop=stop_after_attempt(10),  # Up to 10 retries
        wait=wait_exponential(multiplier=1, min=1, max=60),  # 1s to 60s
        reraise=True,
    ):
        with attempt:
            return await client.create_agent_class(data)


async def create_with_time_limit(client: ControlPlaneClient, data):
    """
    Create a resource with a total time limit for all retries.
    Useful when you have a deadline.
    """
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type((AtlasAPIError,)),
        stop=stop_after_delay(120),  # Give up after 2 minutes total
        wait=wait_exponential(multiplier=2, min=2, max=30),
        reraise=True,
    ):
        with attempt:
            return await client.create_agent_class(data)


async def create_with_jitter(client: ControlPlaneClient, data):
    """
    Create a resource with randomized exponential backoff.
    Prevents thundering herd when many clients retry simultaneously.
    """
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type((AtlasAPIError,)),
        stop=stop_after_attempt(5),
        wait=wait_random_exponential(multiplier=1, max=30),  # Random jitter
        reraise=True,
    ):
        with attempt:
            return await client.create_agent_class(data)


# =============================================================================
# Pattern 2: Retry decorator
# =============================================================================


def with_retry(
    max_attempts: int = 5,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
):
    """
    Decorator for adding retry logic to async functions.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type((AtlasAPIError,)),
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
                reraise=True,
            ):
                with attempt:
                    return await func(*args, **kwargs)
        return wrapper
    return decorator


@with_retry(max_attempts=10, min_wait=2.0, max_wait=60.0)
async def critical_operation(client: ControlPlaneClient):
    """A critical operation with custom retry behavior."""
    return await client.health()


# =============================================================================
# Pattern 3: Circuit Breaker
# =============================================================================


@dataclass
class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    States:
    - CLOSED: Normal operation, requests go through
    - OPEN: Too many failures, requests rejected immediately
    - HALF_OPEN: Testing if service recovered

    Usage:
        breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60.0)

        async with breaker:
            result = await client.health()
    """

    failure_threshold: int = 5
    reset_timeout: float = 60.0

    # Internal state
    failures: int = field(default=0, init=False)
    last_failure_time: float = field(default=0.0, init=False)
    state: str = field(default="CLOSED", init=False)

    def _should_allow_request(self) -> bool:
        """Check if a request should be allowed."""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            # Check if reset timeout has passed
            if time.time() - self.last_failure_time >= self.reset_timeout:
                self.state = "HALF_OPEN"
                return True
            return False

        # HALF_OPEN: allow one test request
        return True

    def _record_success(self) -> None:
        """Record a successful request."""
        self.failures = 0
        self.state = "CLOSED"

    def _record_failure(self) -> None:
        """Record a failed request."""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"

    async def __aenter__(self):
        if not self._should_allow_request():
            raise CircuitBreakerOpen(
                f"Circuit breaker is OPEN. Reset in "
                f"{self.reset_timeout - (time.time() - self.last_failure_time):.1f}s"
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._record_success()
        else:
            self._record_failure()
        return False  # Don't suppress exceptions


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""

    pass


async def call_with_circuit_breaker(
    breaker: CircuitBreaker,
    operation,
):
    """Execute an operation with circuit breaker protection."""
    try:
        async with breaker:
            return await operation()
    except CircuitBreakerOpen:
        # Circuit is open - handle gracefully
        raise
    except Exception:
        # Operation failed - circuit breaker recorded it
        raise


# =============================================================================
# Pattern 4: Retry with fallback
# =============================================================================


async def get_with_fallback(
    primary_client: ControlPlaneClient,
    fallback_client: ControlPlaneClient,
    resource_id,
):
    """
    Try primary client first, fall back to secondary on failure.
    Useful for multi-region deployments.
    """
    try:
        return await primary_client.get_agent_class(resource_id)
    except (AtlasAPIError, Exception) as primary_error:
        print(f"Primary failed: {primary_error}, trying fallback...")
        try:
            return await fallback_client.get_agent_class(resource_id)
        except Exception as fallback_error:
            # Both failed - raise the original error
            raise primary_error from fallback_error


# =============================================================================
# Pattern 5: Retry budget
# =============================================================================


@dataclass
class RetryBudget:
    """
    Track retry budget across multiple operations.
    Prevents excessive retries from overwhelming the service.
    """

    max_retries_per_minute: int = 100
    _retry_timestamps: list = field(default_factory=list)

    def can_retry(self) -> bool:
        """Check if we have retry budget remaining."""
        now = time.time()
        # Remove timestamps older than 1 minute
        self._retry_timestamps = [
            ts for ts in self._retry_timestamps if now - ts < 60
        ]
        return len(self._retry_timestamps) < self.max_retries_per_minute

    def record_retry(self) -> None:
        """Record a retry attempt."""
        self._retry_timestamps.append(time.time())


async def operation_with_budget(
    client: ControlPlaneClient,
    budget: RetryBudget,
    max_attempts: int = 3,
):
    """Execute operation respecting global retry budget."""
    last_error = None

    for attempt in range(max_attempts):
        try:
            return await client.health()
        except AtlasAPIError as e:
            last_error = e
            if e.response.status_code >= 500 and attempt < max_attempts - 1:
                if not budget.can_retry():
                    raise RuntimeError("Retry budget exhausted")
                budget.record_retry()
                await asyncio.sleep(2**attempt)
            else:
                raise

    raise last_error


# =============================================================================
# Main demo
# =============================================================================


async def main():
    """Demonstrate custom retry patterns."""

    async with ControlPlaneClient(base_url="http://localhost:8000") as client:
        # Pattern 1: Tenacity direct usage
        print("=== Pattern 1: Aggressive Retry ===")
        try:
            # This would retry up to 10 times
            # result = await create_with_aggressive_retry(client, data)
            print("Would retry aggressively on failure")
        except RetryError:
            print("All retries exhausted")

        # Pattern 2: Decorator
        print("\n=== Pattern 2: Decorator ===")
        result = await critical_operation(client)
        print(f"Critical operation result: {result}")

        # Pattern 3: Circuit Breaker
        print("\n=== Pattern 3: Circuit Breaker ===")
        breaker = CircuitBreaker(failure_threshold=3, reset_timeout=30.0)

        for i in range(5):
            try:
                async with breaker:
                    result = await client.health()
                    print(f"Request {i + 1}: Success ({breaker.state})")
            except CircuitBreakerOpen as e:
                print(f"Request {i + 1}: {e}")
            except Exception as e:
                print(f"Request {i + 1}: Failed - {e} ({breaker.state})")

        # Pattern 5: Retry Budget
        print("\n=== Pattern 5: Retry Budget ===")
        budget = RetryBudget(max_retries_per_minute=10)
        result = await operation_with_budget(client, budget)
        print(f"Budget-aware operation: {result}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Patterns

### Tenacity Retry Strategies

| Strategy | Use Case |
|----------|----------|
| `stop_after_attempt(n)` | Fixed number of retries |
| `stop_after_delay(s)` | Total time budget |
| `wait_exponential()` | Standard backoff |
| `wait_random_exponential()` | Backoff with jitter (prevents thundering herd) |
| `wait_fixed(s)` | Constant delay between retries |

### Circuit Breaker States

```
CLOSED → [failures >= threshold] → OPEN
                                     ↓
                        [reset_timeout elapsed]
                                     ↓
                               HALF_OPEN
                                  ↓  ↑
                        [success]    [failure]
                                  ↓  ↑
                               CLOSED
```

### When to Use Each Pattern

| Pattern | Use Case |
|---------|----------|
| Aggressive retry | Critical operations that must succeed |
| Time-limited retry | Operations with deadlines |
| Jittered retry | Multiple clients retrying simultaneously |
| Circuit breaker | Protect against cascading failures |
| Fallback | Multi-region or redundant services |
| Retry budget | Prevent overwhelming a degraded service |

## Next Steps

- [Robust Error Recovery](03_error_recovery.md) - Comprehensive error handling
- [High-Throughput Configuration](08_connection_pool.md) - Scale your retries
