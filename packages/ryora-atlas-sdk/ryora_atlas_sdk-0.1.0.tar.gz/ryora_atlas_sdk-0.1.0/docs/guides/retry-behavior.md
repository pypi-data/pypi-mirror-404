# Retry Behavior

The Atlas SDK includes automatic retry logic for transient errors. This guide explains which errors trigger retries, the backoff strategy, and how to customize behavior.

## Default Behavior

By default, the SDK retries requests up to **5 times** on transient errors:

| Error Type | Retry? | Notes |
|------------|--------|-------|
| HTTP 429 (Rate Limited) | Yes | Respects Retry-After header |
| HTTP 502 (Bad Gateway) | Yes | Server-side load balancer issue |
| HTTP 503 (Service Unavailable) | Yes | Server temporarily unavailable |
| HTTP 504 (Gateway Timeout) | Yes | Server-side timeout |
| Connection Error | Yes | Network connectivity issues |
| Read Timeout | Yes | Server slow to respond |
| Connect Timeout | Yes | Server slow to accept connection |
| HTTP 4xx (Client Error) | No | Client-side issue, won't retry |
| HTTP 500 (Server Error) | No | Server bug, unlikely to recover |

## Backoff Strategy

### For HTTP 429 (Rate Limited)

1. Check the `Retry-After` header
2. If present, wait that many seconds (capped at 60 seconds)
3. If absent, fall back to exponential backoff

### For Other Retryable Errors

Exponential backoff: `min(2^attempt, 10)` seconds

| Attempt | Wait Time |
|---------|-----------|
| 1 | 2 seconds |
| 2 | 4 seconds |
| 3 | 8 seconds |
| 4 | 10 seconds |
| 5 | 10 seconds |

## Request ID Preservation

The same `X-Request-ID` is preserved across all retry attempts for a single logical request. This enables distributed tracing across retries.

```python
# Same request_id used for initial request and all retries
await client.health(request_id="my-trace-id")
```

## What Happens After Retries Exhaust

| Error Type | Raised Exception |
|------------|------------------|
| HTTP 429 | `AtlasRateLimitError` (with `retry_after` property) |
| HTTP 502/503/504 | `AtlasServerError` |
| Connection Error | `httpx.ConnectError` |
| Read Timeout | `httpx.ReadTimeout` |
| Connect Timeout | `httpx.ConnectTimeout` |

## Logging

Retry attempts are logged at DEBUG level. Enable debug logging to see retry behavior:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("atlas_sdk").setLevel(logging.DEBUG)
```

Example log output:

```
DEBUG:atlas_sdk.clients.base:Request: GET /health request_id=abc-123
DEBUG:atlas_sdk.clients.base:Response: 503 GET /health request_id=abc-123 duration=0.050s
DEBUG:atlas_sdk.clients.base:Request: GET /health request_id=abc-123
DEBUG:atlas_sdk.clients.base:Response: 200 GET /health request_id=abc-123 duration=0.045s
```

## Timeout Configuration

The default request timeout is **30 seconds**. Configure it per-client:

```python
from atlas_sdk import ControlPlaneClient

# Increase timeout for slow operations
async with ControlPlaneClient(
    base_url="http://control-plane:8000",
    timeout=60.0,  # 60 second timeout
) as client:
    await client.health()
```

!!! warning "Timeout vs Retry"
    The timeout applies to each individual request attempt, not the total
    time including retries. With 5 retry attempts and a 30-second timeout,
    a request could theoretically take up to 150+ seconds (including backoff
    wait times).

## Disabling Retries

To disable automatic retries, provide a pre-configured httpx client:

```python
import httpx
from atlas_sdk import ControlPlaneClient

# Create client without retry transport
http_client = httpx.AsyncClient(
    base_url="http://control-plane:8000",
    timeout=30.0,
)

async with ControlPlaneClient(
    base_url="http://control-plane:8000",
    client=http_client,
) as client:
    # This client won't retry - errors propagate immediately
    await client.health()
```

## Custom Retry Logic

For custom retry behavior beyond what the SDK provides, implement your own retry loop:

```python
import asyncio
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from atlas_sdk.exceptions import AtlasAPIError

@retry(
    retry=retry_if_exception_type(AtlasAPIError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
)
async def create_with_custom_retry(client, data):
    return await client.create_deployment(data)
```

Or with a simple loop:

```python
async def create_with_manual_retry(client, data, max_attempts=3):
    last_error = None
    for attempt in range(max_attempts):
        try:
            return await client.create_deployment(data)
        except AtlasAPIError as e:
            last_error = e
            if e.response.status_code >= 500:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
                continue
            raise
    raise last_error
```

## Circuit Breaker Pattern

For high-availability systems, consider implementing a circuit breaker:

```python
import time
from dataclasses import dataclass, field

@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    reset_timeout: float = 60.0
    failures: int = field(default=0, init=False)
    last_failure_time: float = field(default=0.0, init=False)
    state: str = field(default="closed", init=False)

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        if time.time() - self.last_failure_time > self.reset_timeout:
            self.state = "half-open"
            return True
        return False

# Usage
breaker = CircuitBreaker()

async def call_with_breaker(client, operation):
    if not breaker.can_execute():
        raise RuntimeError("Circuit breaker is open")

    try:
        result = await operation()
        breaker.record_success()
        return result
    except Exception as e:
        breaker.record_failure()
        raise
```

## Best Practices

1. **Don't disable retries** unless you have a specific reason - transient errors are common in distributed systems

2. **Set appropriate timeouts** - balance between allowing slow operations and failing fast

3. **Use request IDs** - they help trace requests across retries and services

4. **Monitor retry rates** - high retry rates may indicate infrastructure issues

5. **Implement idempotency** - ensure your operations are safe to retry (the SDK preserves request IDs to help with this)

## See Also

- [Error Handling](error-handling.md) - Exception types and handling patterns
- [Observability](observability.md) - Tracing and metrics for monitoring retries
