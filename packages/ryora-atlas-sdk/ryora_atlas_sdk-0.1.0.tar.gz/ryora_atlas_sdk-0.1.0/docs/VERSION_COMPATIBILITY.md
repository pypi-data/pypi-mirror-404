# Version Compatibility

This document describes the version alignment strategy between the Atlas SDK and the Control Plane API.

## Versioning Scheme

### Semantic Versioning

Both the Atlas SDK and Control Plane API follow [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., `1.2.3`)
- **MAJOR**: Breaking changes to the API contract
- **MINOR**: New features, backward-compatible additions
- **PATCH**: Bug fixes, backward-compatible improvements

### SDK Version Tags

SDK releases are tagged with the pattern `atlas-sdk-v{VERSION}` (e.g., `atlas-sdk-v1.2.0`).

## Version Alignment Policy

### Compatibility Matrix

| SDK Version | API Version | Compatibility |
|-------------|-------------|---------------|
| 0.1.x       | 0.1.x       | Full support  |
| 1.0.x       | 1.0.x       | Full support  |
| 1.1.x       | 1.1.x       | Full support  |
| 1.2.x       | 1.1.x       | Backward compatible (SDK may have additional features) |
| 1.2.x       | 1.2.x       | Full support  |

### Rules

1. **MAJOR versions must match**: SDK 1.x.x works with API 1.x.x, SDK 2.x.x works with API 2.x.x
2. **SDK MINOR can be >= API MINOR**: The SDK may add convenience features ahead of API updates
3. **PATCH versions are independent**: Bug fixes on either side don't require alignment

### Pre-release Versions (0.x.x)

During pre-release development (0.x.x), minor version changes may contain breaking changes. Ensure SDK and API minor versions match during this phase.

## How Version Alignment Works

### During Development

1. **Feature Development**: When adding a new API endpoint or model field:
   - Update Control Plane schemas and routers
   - Run `python scripts/export_openapi.py` to regenerate OpenAPI spec
   - Update SDK models to match
   - Run `python scripts/validate_models.py` to verify alignment

2. **CI Validation**: Every PR to the SDK runs model validation against the Control Plane OpenAPI spec. The build fails if:
   - SDK models are missing fields present in the API
   - SDK model types don't match API types
   - Required fields don't align

3. **Release Coordination**: When releasing a new SDK version:
   - Verify compatibility with the target API version
   - Update this compatibility matrix
   - Tag the release with `atlas-sdk-v{VERSION}`

### Checking Compatibility

```bash
# Generate the current Control Plane OpenAPI spec
cd control_plane
python scripts/export_openapi.py --output ../atlas-sdk/openapi.json

# Validate SDK models against the spec
cd ../atlas-sdk
python scripts/validate_models.py --file openapi.json
```

## Deprecation Policy

### API Deprecation Timeline

1. **Announcement**: Deprecated fields are marked with `deprecated: true` in OpenAPI
2. **Warning Period**: At least 2 minor versions before removal
3. **Removal**: Deprecated fields removed in next major version

### SDK Handling of Deprecated Fields

- SDK validation script warns when using deprecated API fields
- SDK code should migrate away from deprecated fields before next major release
- Breaking changes are documented in CHANGELOG.md

## Breaking Change Examples

### Major Version Bump Required

- Removing a required API endpoint
- Removing a required field from a response model
- Changing the type of an existing field
- Changing authentication mechanism

### Minor Version Bump Required

- Adding a new optional endpoint
- Adding new optional fields to request/response models
- Adding new enum values
- Adding new optional query parameters

### Patch Version Bump Required

- Bug fixes that don't change API contracts
- Documentation updates
- Performance improvements
- Internal refactoring

## Migration Guides

When a major version is released, migration guides will be published at:
`docs/migrations/v{OLD}-to-v{NEW}.md`

These guides will include:
- Summary of breaking changes
- Code examples for migrating
- Deprecation timeline for removed features
