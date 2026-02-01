# Backward Compatibility Guide

This guide explains how the Atlas SDK maintains backward compatibility and how to prepare for breaking changes.

## Version Policy

The Atlas SDK follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** version (e.g., 1.0.0 → 2.0.0): Incompatible API changes
- **MINOR** version (e.g., 1.0.0 → 1.1.0): New features, backward-compatible
- **PATCH** version (e.g., 1.0.0 → 1.0.1): Bug fixes, backward-compatible

### Pre-release Versions (0.x.x)

During pre-release development (versions 0.x.x), minor version changes may contain breaking changes. Always check the [CHANGELOG](../../CHANGELOG.md) when upgrading.

## Deprecation Policy

### Timeline

Deprecated features follow a strict timeline:

1. **Deprecation Announcement**: Feature is marked deprecated, warning emitted
2. **Warning Period**: At least **2 minor versions** before removal
3. **Removal**: Feature removed in a subsequent release

For example:
- Feature deprecated in 1.2.0
- Warning emitted in 1.2.0, 1.3.0
- Earliest removal: 1.4.0

### Deprecation Warnings

When you use a deprecated feature, you'll see a `DeprecationWarning`:

```
DeprecationWarning: 'AtlasHTTPStatusError' is deprecated since version 0.2.0
and will be removed in version 0.4.0. Use 'AtlasAPIError' instead.
```

#### Viewing Deprecation Warnings

By default, Python suppresses `DeprecationWarning`. To see them:

**Option 1: Python flag**
```bash
python -W default::DeprecationWarning your_script.py
```

**Option 2: Environment variable**
```bash
export PYTHONWARNINGS="default::DeprecationWarning"
python your_script.py
```

**Option 3: In code**
```python
import warnings
warnings.filterwarnings("default", category=DeprecationWarning)
```

**Option 4: pytest (recommended for tests)**
```python
# In pytest.ini or pyproject.toml
[tool.pytest.ini_options]
filterwarnings = ["default::DeprecationWarning"]
```

#### CI Integration

Add deprecation checks to your CI pipeline:

```yaml
# GitHub Actions example
- name: Check for deprecation warnings
  run: python -W error::DeprecationWarning -c "import atlas_sdk"
```

This will fail the build if your code uses any deprecated features.

## Handling Deprecated Features

### 1. Check for Warnings

Run your test suite with deprecation warnings enabled:

```bash
pytest -W default::DeprecationWarning
```

### 2. Read the Warning Message

Each warning tells you:
- Which feature is deprecated
- When it was deprecated
- When it will be removed
- What to use instead

### 3. Update Your Code

Replace deprecated features with their recommended alternatives:

```python
# Before (deprecated)
from atlas_sdk import AtlasHTTPStatusError

try:
    await client.get_deployment(deployment_id)
except AtlasHTTPStatusError as e:
    print(f"HTTP error: {e.status_code}")

# After (recommended)
from atlas_sdk import AtlasAPIError

try:
    await client.get_deployment(deployment_id)
except AtlasAPIError as e:
    print(f"HTTP error: {e.status_code}")
```

### 4. Check Migration Guides

For complex changes, consult the [migration guides](../migrations/index.md).

## What Triggers Breaking Changes

### MAJOR Version Bump Required

- Removing a public class, function, or method
- Changing a method signature (required parameters)
- Changing return types
- Removing a model field
- Changing exception behavior

### MINOR Version Bump (Backward Compatible)

- Adding new optional parameters
- Adding new methods or classes
- Adding new model fields (optional)
- Adding new enum values
- Performance improvements

### PATCH Version Bump (Backward Compatible)

- Bug fixes
- Documentation updates
- Internal refactoring
- Test improvements

## Migration Resources

- [CHANGELOG](../../CHANGELOG.md) - All version changes with deprecation notices
- [Migration Guides](../migrations/index.md) - Step-by-step upgrade instructions
- [VERSION_COMPATIBILITY.md](../VERSION_COMPATIBILITY.md) - SDK/API version alignment

## Using Deprecation Utilities

If you're building on top of the Atlas SDK, you can use our deprecation utilities:

```python
from atlas_sdk import deprecated, deprecated_parameter, warn_deprecated

# Deprecate a function
@deprecated("1.0.0", "2.0.0", alternative="new_function")
def old_function():
    pass

# Deprecate a parameter
@deprecated_parameter("old_param", "1.0.0", alternative="new_param")
def my_function(new_param=None, old_param=None):
    if old_param is not None:
        new_param = old_param
    # ... rest of function

# Programmatic warning
def some_function():
    if using_deprecated_behavior:
        warn_deprecated(
            "deprecated_behavior",
            "1.0.0",
            alternative="new_behavior"
        )
```

## Best Practices

### For SDK Users

1. **Enable warnings in development**: Add `-W default::DeprecationWarning` to your development workflow
2. **Check warnings in CI**: Fail builds on deprecation warnings to catch issues early
3. **Upgrade incrementally**: Don't skip minor versions; upgrade one at a time
4. **Read the CHANGELOG**: Before upgrading, check for deprecations and breaking changes
5. **Pin versions in production**: Use version pinning (`atlas-sdk==1.2.3`) for stability

### For Library Authors Building on Atlas SDK

1. **Re-export deprecation utilities**: If wrapping SDK classes, use our deprecation decorators
2. **Follow the same timeline**: Maintain the 2 minor version deprecation period
3. **Document your own deprecations**: Keep your own CHANGELOG updated
4. **Test with warnings**: Include deprecation warning checks in your test suite
