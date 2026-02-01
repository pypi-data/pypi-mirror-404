# Idempotency

The Atlas SDK supports idempotency keys for safe retries of create operations. This guide explains how to use idempotency keys to ensure operations are only performed once, even if retried.

## What is Idempotency?

Idempotency ensures that an operation can be safely retried without causing unintended side effects. When you provide an idempotency key, the server remembers the result of the first request with that key and returns the same result for subsequent requests with the same key.

This is useful when:

- Network issues cause client-side timeouts (server may have processed the request)
- Retry logic re-sends a request that already succeeded
- You need to safely retry create operations after transient failures

## Using Idempotency Keys

All create operations accept an optional `idempotency_key` parameter:

```python
from atlas_sdk.clients import ControlPlaneClient
from atlas_sdk.models import DeploymentCreate

async with ControlPlaneClient(base_url="http://control-plane:8000") as client:
    deployment = await client.create_deployment(
        DeploymentCreate(
            agent_definition_id=definition_id,
            name="my-deployment",
            environment="production",
        ),
        idempotency_key="deploy-my-deployment-2024-01-15",
    )
```

### Supported Operations

| Client | Method | Idempotency Supported |
|--------|--------|----------------------|
| ControlPlaneClient | `create_agent_class()` | Yes |
| ControlPlaneClient | `create_agent_definition()` | Yes |
| ControlPlaneClient | `create_model_provider()` | Yes |
| ControlPlaneClient | `create_system_prompt()` | Yes |
| ControlPlaneClient | `create_deployment()` | Yes |
| ControlPlaneClient | `create_grasp_analysis()` | Yes |
| DispatchClient | `spawn_agent()` | Yes |
| WorkflowClient | `create_plan()` | Yes |
| WorkflowClient | `append_tasks()` | Yes |

Resource managers also support idempotency keys:

```python
# Using resource pattern
deployment = await client.deployments.create(
    agent_definition_id=definition_id,
    name="my-deployment",
    idempotency_key="deploy-v1",
)

plan = await client.plans.create(
    deployment_id=deployment_id,
    goal="Process data",
    idempotency_key="plan-batch-123",
)
```

## Auto-Generated Keys

Use the special value `"auto"` to generate a UUID-based key automatically:

```python
# Auto-generate a unique idempotency key
deployment = await client.create_deployment(
    DeploymentCreate(...),
    idempotency_key="auto",
)
```

This is useful when you want idempotency protection but don't have a natural key for the operation. The auto-generated key is a UUID v4.

**Note:** Auto-generated keys are created fresh for each call, so they don't provide cross-session protection. Use explicit keys when you need to safely retry operations across different code executions.

## Key Format Requirements

Idempotency keys should:

- Be unique per logical operation
- Be stable across retries of the same operation
- Be a string of reasonable length (recommended: 1-255 characters)

Good key patterns:

```python
# Include operation type and unique identifiers
idempotency_key = f"deploy-{agent_name}-{version}-{timestamp}"

# Use request-specific data
idempotency_key = f"plan-{deployment_id}-{batch_id}"

# Include session/request ID
idempotency_key = f"create-provider-{request_id}"
```

## Key Preservation Across Retries

When the SDK retries a request (due to transient errors like 502, 503, 504, or connection issues), the same idempotency key is preserved across all retry attempts:

```python
# Same key is sent on initial request and all retries
await client.create_deployment(
    DeploymentCreate(...),
    idempotency_key="deploy-v1",  # Preserved across retries
)
```

This ensures that even if a request is retried multiple times, the server only processes it once.

## Best Practices

### 1. Use Meaningful Keys

Create keys that reflect the business operation:

```python
# Good: reflects what's being created
idempotency_key = f"deploy-bughunter-prod-v2"

# Avoid: generic or random (defeats the purpose)
idempotency_key = str(uuid.uuid4())  # Use "auto" instead
```

### 2. Include Timestamps for Time-Sensitive Operations

For operations that might be legitimately repeated, include a time component:

```python
# Daily deployment key
date = datetime.now().strftime("%Y-%m-%d")
idempotency_key = f"deploy-bughunter-prod-{date}"
```

### 3. Store Keys for Manual Retry Scenarios

When you need to retry operations across different code executions:

```python
# Store the key before the operation
idempotency_key = f"deploy-{deployment_name}-{uuid.uuid4()}"
save_key_to_database(idempotency_key)

try:
    deployment = await client.create_deployment(
        DeploymentCreate(...),
        idempotency_key=idempotency_key,
    )
except AtlasTimeoutError:
    # Key is saved - can be used to safely retry later
    print(f"Retry later with key: {idempotency_key}")
```

### 4. Use "auto" for Fire-and-Forget Operations

When you just want protection within a single request lifecycle:

```python
# Good for automated pipelines where natural keys don't exist
deployment = await client.create_deployment(
    DeploymentCreate(...),
    idempotency_key="auto",
)
```

## Debugging

Idempotency keys are included in SDK debug logs:

```python
import logging
logging.getLogger("atlas_sdk.clients.base").setLevel(logging.DEBUG)

# Log output includes:
# Request: POST /api/v1/deployments request_id=abc123 idempotency_key=deploy-v1
```

## Server-Side Behavior

The Atlas Control Plane stores idempotency keys with their results for a configurable retention period (typically 24-48 hours). After this period, the same key can be reused for a new operation.

If a request with a previously used key is received while the original request is still processing, the server will wait for the original to complete and return its result.
