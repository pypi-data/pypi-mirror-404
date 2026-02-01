# Input Validation and Type Coercion

This guide explains how the Atlas SDK validates input data and handles type coercion.

## Overview

The Atlas SDK uses Pydantic v2 for data validation. Input validation happens at two levels:

1. **Model Construction** (immediate): When you create a model instance, Pydantic validates the data immediately.
2. **Pre-HTTP Validation** (optional): You can explicitly validate data before making API calls using the `validate_model()` utility.

## Type Coercion Behavior

### UUID Fields

UUID fields accept both `uuid.UUID` objects and valid UUID strings:

```python
from uuid import UUID
from atlas_sdk import AgentDefinitionCreate

# Both of these are valid:
model1 = AgentDefinitionCreate(
    agent_class_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    name="my-agent"
)

model2 = AgentDefinitionCreate(
    agent_class_id="123e4567-e89b-12d3-a456-426614174000",  # String is coerced
    name="my-agent"
)
```

Invalid UUIDs raise `ValidationError` immediately:

```python
from pydantic import ValidationError

try:
    AgentDefinitionCreate(
        agent_class_id="not-a-uuid",  # Invalid!
        name="my-agent"
    )
except ValidationError as e:
    print(e)
    # Input should be a valid UUID, unable to parse string as a UUID
```

### Enum Fields

Enum fields accept both enum members and their string values:

```python
from atlas_sdk import AgentDefinitionCreate, ExecutionMode

# Both of these are valid:
model1 = AgentDefinitionCreate(
    agent_class_id="...",
    name="my-agent",
    execution_mode=ExecutionMode.STATEFUL  # Enum member
)

model2 = AgentDefinitionCreate(
    agent_class_id="...",
    name="my-agent",
    execution_mode="stateful"  # String is coerced
)
```

Invalid enum values raise `ValidationError`:

```python
try:
    AgentDefinitionCreate(
        agent_class_id="...",
        name="my-agent",
        execution_mode="invalid"  # Not a valid enum value!
    )
except ValidationError as e:
    print(e)
    # Input should be 'stateful' or 'ephemeral'
```

### Required vs Optional Fields

Required fields must be provided. Optional fields default to `None` or their specified default value:

```python
# Required: agent_class_id, name
# Optional: description, system_prompt_id, etc.

AgentDefinitionCreate(
    agent_class_id="...",
    name="my-agent"
    # description is optional, defaults to None
)

# Missing required field raises ValidationError
try:
    AgentDefinitionCreate(name="my-agent")  # Missing agent_class_id!
except ValidationError as e:
    print(e)
    # Field required
```

### Extra Fields

Create and Update models reject unknown fields (using `extra="forbid"`):

```python
try:
    AgentDefinitionCreate(
        agent_class_id="...",
        name="my-agent",
        unknown_field="value"  # Not a valid field!
    )
except ValidationError as e:
    print(e)
    # Extra inputs are not permitted
```

This catches typos early:

```python
try:
    AgentDefinitionCreate(
        agent_class_id="...",
        name="my-agent",
        descripton="typo"  # Typo in 'description'!
    )
except ValidationError as e:
    print(e)
    # Extra inputs are not permitted
```

## Explicit Validation with Enhanced Error Messages

For better error messages, use the `validate_model()` utility:

```python
from atlas_sdk import validate_model, AtlasInputValidationError
from atlas_sdk import AgentDefinitionCreate

try:
    model = validate_model(
        AgentDefinitionCreate,
        agent_class_id="not-a-uuid",
        name="my-agent"
    )
except AtlasInputValidationError as e:
    print(e.message)
    # Validation failed: agent_class_id: Invalid UUID format. Expected a UUID
    # like '123e4567-e89b-12d3-a456-426614174000', got 'not-a-uuid'.

    for detail in e.details:
        print(f"Field: {detail.loc}")
        print(f"Message: {detail.msg}")
        print(f"Type: {detail.type}")
```

## Validation Helper Functions

The SDK provides additional validation helpers:

### `validate_uuid()`

Validate and normalize a UUID value:

```python
from atlas_sdk import validate_uuid, AtlasInputValidationError

try:
    uuid_str = validate_uuid("123e4567-e89b-12d3-a456-426614174000")
    print(uuid_str)  # "123e4567-e89b-12d3-a456-426614174000"
except AtlasInputValidationError as e:
    print(e)
```

### `validate_enum()`

Validate an enum value with helpful error messages:

```python
from atlas_sdk import validate_enum, AtlasInputValidationError
from atlas_sdk import DeploymentStatus

try:
    status = validate_enum("invalid", DeploymentStatus, "status")
except AtlasInputValidationError as e:
    print(e.details[0].msg)
    # Invalid value 'invalid' for status. Valid options are:
    # 'spawning', 'active', 'completed', 'failed'.
```

### `validate_instance()`

Re-validate an existing model instance:

```python
from atlas_sdk import validate_instance, PlanCreate

plan = PlanCreate(goal="Build feature X")
# ... possibly modify the plan ...
validate_instance(plan)  # Re-validate before sending
```

## Best Practices

### 1. Validate Early

Validate data as early as possible to catch errors before making network calls:

```python
from atlas_sdk import validate_model, ControlPlaneClient, AgentClassCreate

# Validate before calling the API
try:
    model = validate_model(AgentClassCreate, name="", description="test")
except AtlasInputValidationError as e:
    # Handle validation error immediately
    print(f"Invalid input: {e}")
    return

# Now we know the model is valid
async with ControlPlaneClient(base_url="...") as client:
    result = await client.create_agent_class(model)
```

### 2. Use Type Hints

Always use type hints for better IDE support and documentation:

```python
from uuid import UUID
from atlas_sdk import AgentDefinitionCreate

def create_agent(
    agent_class_id: UUID,  # Type hint documents expected type
    name: str,
) -> AgentDefinitionCreate:
    return AgentDefinitionCreate(
        agent_class_id=agent_class_id,
        name=name,
    )
```

### 3. Handle Validation Errors Gracefully

Provide helpful feedback to users when validation fails:

```python
from atlas_sdk import validate_model, AtlasInputValidationError

try:
    model = validate_model(AgentClassCreate, **user_input)
except AtlasInputValidationError as e:
    # Build user-friendly error response
    errors = {}
    for detail in e.details:
        field_path = ".".join(str(p) for p in detail.loc)
        errors[field_path] = detail.msg
    return {"errors": errors}
```

## Field Constraints

Some fields have additional constraints beyond their type:

| Model | Field | Constraint |
|-------|-------|------------|
| `PlanTaskCreate` | `sequence` | `>= 0` |
| `GraspAnalysisRead` | `*_value` fields | `0 <= value <= 100` |
| `AgentClassCreate` | `name` | `min_length=1` |
| `ToolCreate` | `risk_level` | `"low"`, `"medium"`, or `"high"` |

These constraints are documented in the model docstrings and enforced at construction time.

## Type Coercion Summary Table

| Source Type | Target Type | Coerced? | Notes |
|-------------|-------------|----------|-------|
| `str` (valid UUID) | `UUID` | Yes | Parsed to UUID object |
| `str` (invalid) | `UUID` | No | Raises ValidationError |
| `UUID` | `UUID` | Yes | Passed through |
| `str` (enum value) | `Enum` | Yes | Matched to enum member |
| `Enum` member | `Enum` | Yes | Passed through |
| `str` (invalid) | `Enum` | No | Raises ValidationError |
| `dict` | `dict[str, Any]` | Yes | Passed through |
| `list` | `list[T]` | Yes | Elements validated |
| `None` | Optional field | Yes | Uses default value |
| Any | Non-matching type | No | Raises ValidationError |
