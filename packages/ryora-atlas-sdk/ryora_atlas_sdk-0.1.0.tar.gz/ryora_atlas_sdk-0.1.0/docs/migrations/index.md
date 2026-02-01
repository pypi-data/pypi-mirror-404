# Migration Guides

This directory contains migration guides for upgrading between Atlas SDK versions.

## Available Guides

| From Version | To Version | Guide | Description |
|--------------|------------|-------|-------------|
| 0.0.x | 0.1.0 | [Client Separation](client-separation.md) | Monolithic client split into ControlPlaneClient, DispatchClient, WorkflowClient |

## How to Use Migration Guides

1. **Identify your current version**: Check your `pyproject.toml` or `requirements.txt`
2. **Find the relevant guide**: Look for guides covering your upgrade path
3. **Read the breaking changes**: Each guide starts with a summary of breaking changes
4. **Follow the migration steps**: Step-by-step instructions with code examples
5. **Run tests**: Verify your code works after migration

## Upgrade Strategy

### Recommended Approach

1. **Upgrade one minor version at a time**: Don't skip versions
2. **Enable deprecation warnings**: Run tests with `-W default::DeprecationWarning`
3. **Fix deprecation warnings before upgrading**: Address deprecated usage before moving to the next version
4. **Read the CHANGELOG**: Check for any additional changes not covered in migration guides

### Example Upgrade Path

If upgrading from 0.0.1 to 0.2.0:

```bash
# Step 1: Upgrade to 0.1.0
pip install atlas-sdk==0.1.0
# Run tests, fix issues
pytest -W default::DeprecationWarning

# Step 2: Upgrade to 0.2.0
pip install atlas-sdk==0.2.0
# Run tests, fix deprecation warnings
pytest -W default::DeprecationWarning
```

## Creating Migration Guides

When making breaking changes to the SDK, create a migration guide with:

1. **Summary of changes**: What's changing and why
2. **Breaking changes list**: Bullet points of all breaking changes
3. **Code examples**: Before/after code snippets
4. **Common patterns**: Address common use cases
5. **Troubleshooting**: Common issues and solutions

Save guides as `docs/migrations/vX.Y-to-vX.Z.md`.

## Related Resources

- [CHANGELOG](../../CHANGELOG.md) - Complete version history
- [Backward Compatibility Guide](../guides/backward-compatibility.md) - Deprecation policy
- [VERSION_COMPATIBILITY.md](../VERSION_COMPATIBILITY.md) - SDK/API version alignment
