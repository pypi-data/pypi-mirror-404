# High-Throughput Configuration

This example demonstrates how to configure connection pools for high-concurrency scenarios.

## Use Case: Batch Processing Service

You're building a service that:

- Processes thousands of requests per minute
- Makes many concurrent API calls
- Needs to maximize throughput while avoiding resource exhaustion

## Prerequisites

- Atlas SDK installed
- Understanding of connection pooling concepts

## Complete Example

```python
"""
Example: High-Throughput Connection Configuration
Use Case: Build a high-performance batch processing service

This example shows how to:
- Configure connection pool settings for high throughput
- Tune keepalive settings for different deployment patterns
- Monitor connection usage
- Handle connection limits gracefully
"""

import asyncio
import time
from dataclasses import dataclass, field

from atlas_sdk import ControlPlaneClient
from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics


# =============================================================================
# Connection Pool Configurations
# =============================================================================


@dataclass
class PoolConfig:
    """Connection pool configuration."""

    max_connections: int
    max_keepalive_connections: int
    keepalive_expiry: float
    description: str


# Recommended configurations for different scenarios
CONFIGS = {
    "default": PoolConfig(
        max_connections=100,
        max_keepalive_connections=20,
        keepalive_expiry=5.0,
        description="Default - good for most use cases",
    ),
    "high_throughput": PoolConfig(
        max_connections=200,
        max_keepalive_connections=50,
        keepalive_expiry=30.0,
        description="High throughput - many concurrent requests",
    ),
    "serverless": PoolConfig(
        max_connections=50,
        max_keepalive_connections=10,
        keepalive_expiry=5.0,
        description="Serverless - short-lived, bursty workloads",
    ),
    "background_worker": PoolConfig(
        max_connections=100,
        max_keepalive_connections=30,
        keepalive_expiry=120.0,
        description="Background worker - long-running processes",
    ),
}


def create_client(base_url: str, config_name: str = "default") -> ControlPlaneClient:
    """Create a client with the specified pool configuration."""
    config = CONFIGS[config_name]
    print(f"Using pool config: {config.description}")
    print(f"  max_connections={config.max_connections}")
    print(f"  max_keepalive_connections={config.max_keepalive_connections}")
    print(f"  keepalive_expiry={config.keepalive_expiry}s")

    return ControlPlaneClient(
        base_url=base_url,
        max_connections=config.max_connections,
        max_keepalive_connections=config.max_keepalive_connections,
        keepalive_expiry=config.keepalive_expiry,
    )


# =============================================================================
# Connection Monitoring
# =============================================================================


@dataclass
class ConnectionMetrics(MetricsHandler):
    """Track connection pool usage."""

    active_requests: int = 0
    peak_concurrent: int = 0
    total_requests: int = 0
    total_duration: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        self.active_requests += 1
        self.peak_concurrent = max(self.peak_concurrent, self.active_requests)

    def on_request_end(self, metrics: RequestMetrics) -> None:
        self.active_requests -= 1
        self.total_requests += 1
        self.total_duration += metrics.duration_seconds

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        self.active_requests -= 1

    @property
    def avg_duration(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_duration / self.total_requests

    def print_stats(self) -> None:
        print(f"\nConnection Stats:")
        print(f"  Peak concurrent: {self.peak_concurrent}")
        print(f"  Total requests: {self.total_requests}")
        print(f"  Avg duration: {self.avg_duration:.3f}s")


# =============================================================================
# High-Throughput Patterns
# =============================================================================


async def process_batch_concurrent(
    client: ControlPlaneClient,
    items: list,
    max_concurrency: int = 50,
) -> list:
    """
    Process items with controlled concurrency.

    Uses a semaphore to limit concurrent requests, preventing
    connection pool exhaustion.
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    results = []

    async def process_one(item):
        async with semaphore:
            # Your processing logic here
            result = await client.health()
            return result

    # Process all items with controlled concurrency
    tasks = [process_one(item) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return results


async def process_with_rate_limit(
    client: ControlPlaneClient,
    items: list,
    requests_per_second: float = 100.0,
) -> list:
    """
    Process items with rate limiting.

    Prevents overwhelming the server even with available connections.
    """
    interval = 1.0 / requests_per_second
    results = []
    last_request = 0.0

    for item in items:
        # Enforce rate limit
        now = time.time()
        if now - last_request < interval:
            await asyncio.sleep(interval - (now - last_request))

        result = await client.health()
        results.append(result)
        last_request = time.time()

    return results


async def process_with_backpressure(
    client: ControlPlaneClient,
    items: list,
    max_in_flight: int = 100,
) -> list:
    """
    Process items with backpressure handling.

    Slows down when too many requests are in flight.
    """
    in_flight = 0
    results = []
    pending = asyncio.Queue()
    done = asyncio.Queue()

    async def worker():
        nonlocal in_flight
        while True:
            item = await pending.get()
            if item is None:
                break

            try:
                result = await client.health()
                await done.put((item, result, None))
            except Exception as e:
                await done.put((item, None, e))
            finally:
                in_flight -= 1
                pending.task_done()

    # Start workers
    workers = [asyncio.create_task(worker()) for _ in range(max_in_flight)]

    # Feed items with backpressure
    for item in items:
        while in_flight >= max_in_flight:
            await asyncio.sleep(0.01)  # Wait for slots
        in_flight += 1
        await pending.put(item)

    # Wait for completion
    await pending.join()

    # Stop workers
    for _ in workers:
        await pending.put(None)
    await asyncio.gather(*workers)

    # Collect results
    while not done.empty():
        item, result, error = await done.get()
        results.append(result if not error else error)

    return results


# =============================================================================
# Benchmarking
# =============================================================================


async def benchmark_throughput(
    base_url: str,
    config_name: str,
    num_requests: int = 1000,
    concurrency: int = 50,
) -> dict:
    """
    Benchmark throughput with a specific configuration.
    """
    metrics = ConnectionMetrics()

    async with ControlPlaneClient(
        base_url=base_url,
        metrics_handler=metrics,
        **CONFIGS[config_name].__dict__,
    ) as client:
        start = time.time()

        # Run concurrent requests
        semaphore = asyncio.Semaphore(concurrency)

        async def make_request():
            async with semaphore:
                return await client.health()

        await asyncio.gather(*[make_request() for _ in range(num_requests)])

        elapsed = time.time() - start

    return {
        "config": config_name,
        "requests": num_requests,
        "concurrency": concurrency,
        "elapsed_seconds": elapsed,
        "requests_per_second": num_requests / elapsed,
        "peak_concurrent": metrics.peak_concurrent,
        "avg_latency": metrics.avg_duration,
    }


# =============================================================================
# Main
# =============================================================================


async def main():
    """Demonstrate connection pool configurations."""
    base_url = "http://localhost:8000"

    # Example 1: Different configurations
    print("=== Connection Pool Configurations ===\n")
    for name, config in CONFIGS.items():
        print(f"{name}:")
        print(f"  {config.description}")
        print(f"  connections: {config.max_connections}/{config.max_keepalive_connections}")
        print()

    # Example 2: High-throughput client
    print("=== High-Throughput Processing ===\n")
    metrics = ConnectionMetrics()

    async with ControlPlaneClient(
        base_url=base_url,
        max_connections=200,
        max_keepalive_connections=50,
        keepalive_expiry=30.0,
        metrics_handler=metrics,
    ) as client:
        # Process 500 items with concurrency of 50
        items = list(range(500))
        start = time.time()

        results = await process_batch_concurrent(client, items, max_concurrency=50)

        elapsed = time.time() - start
        print(f"Processed {len(results)} items in {elapsed:.2f}s")
        print(f"Throughput: {len(results) / elapsed:.1f} req/s")
        metrics.print_stats()

    # Example 3: Benchmark different configs
    print("\n=== Benchmark Comparison ===\n")
    for config_name in ["default", "high_throughput"]:
        result = await benchmark_throughput(
            base_url, config_name, num_requests=100, concurrency=20
        )
        print(f"{config_name}: {result['requests_per_second']:.1f} req/s")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Points

### Connection Pool Parameters

| Parameter | Purpose | Impact |
|-----------|---------|--------|
| `max_connections` | Total connections allowed | Higher = more concurrency |
| `max_keepalive_connections` | Idle connections to keep | Higher = faster reconnect |
| `keepalive_expiry` | How long to keep idle connections | Higher = less reconnection overhead |

### Recommended Settings

| Scenario | max_connections | max_keepalive | keepalive_expiry |
|----------|-----------------|---------------|------------------|
| Default | 100 | 20 | 5s |
| High throughput | 200 | 50 | 30s |
| Serverless | 50 | 10 | 5s |
| Background worker | 100 | 30 | 120s |

### Controlling Concurrency

Use semaphores to prevent connection exhaustion:

```python
semaphore = asyncio.Semaphore(50)  # Max 50 concurrent

async def process(item):
    async with semaphore:
        return await client.operation()

await asyncio.gather(*[process(i) for i in items])
```

### Monitoring

Track connection usage with metrics handlers:

```python
class ConnectionMetrics(MetricsHandler):
    def on_request_start(self, ...):
        self.active += 1
        self.peak = max(self.peak, self.active)

    def on_request_end(self, ...):
        self.active -= 1
```

## Best Practices

1. **Match pool size to workload** - Don't over-provision connections
2. **Use semaphores** - Control concurrency independent of pool size
3. **Monitor peak concurrent** - Adjust pool if consistently hitting limits
4. **Set appropriate keepalive** - Longer for steady traffic, shorter for bursty
5. **Consider server limits** - Your pool can't exceed server connection limits

## Next Steps

- [Concurrent Operations](09_concurrent_operations.md) - More concurrency patterns
- [OpenTelemetry Integration](10_opentelemetry.md) - Monitor at scale
