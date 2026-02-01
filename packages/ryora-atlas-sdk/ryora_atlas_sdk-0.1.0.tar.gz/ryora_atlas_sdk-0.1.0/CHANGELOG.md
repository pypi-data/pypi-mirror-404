# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Breaking Changes

_None in this release._

### Deprecated

- `AtlasHTTPStatusError` is deprecated in favor of `AtlasAPIError`. It will be removed in version 0.4.0. See [migration guide](docs/migrations/client-separation.md) for details.

### Added

- Deprecation utilities module (`atlas_sdk.deprecation`) for marking features as deprecated
  - `deprecated()` decorator for deprecated functions/methods
  - `deprecated_parameter()` decorator for deprecated function parameters
  - `deprecated_class()` decorator for deprecated classes
  - `warn_deprecated()` function for programmatic deprecation warnings
- Backward compatibility guide documenting deprecation policy and timeline

### Changed

_None in this release._

### Fixed

_None in this release._

### Removed

_None in this release._

---

## [0.1.0] - 2025-01-30

### Breaking Changes

_Initial release - no breaking changes._

### Added

- Initial release of Atlas SDK
- `ControlPlaneClient` for interacting with the Atlas Control Plane API
  - Plan management (create, list, get)
  - Execution management (create, list, get, cancel)
  - Agent definition management
- `DispatchClient` for agent lifecycle management
  - Agent spawning and stopping
  - A2A communication
  - Agent directory
- `WorkflowClient` for workflow orchestration
  - Plan and task management
  - Waiter patterns for async operations
- Resilient HTTP client with automatic retries using tenacity
- Rate limiting (429) handling with Retry-After header support
- Comprehensive error handling with semantic exception hierarchy:
  - `AtlasAPIError` (base for all HTTP errors)
  - `AtlasNotFoundError` (404)
  - `AtlasValidationError` (400, 422) with structured field details
  - `AtlasConflictError` (409)
  - `AtlasAuthenticationError` (401)
  - `AtlasAuthorizationError` (403)
  - `AtlasRateLimitError` (429) with retry_after support
  - `AtlasServerError` (5xx)
  - `AtlasDomainError` for business logic errors
  - `AtlasTimeoutError` with last state tracking
  - `AtlasConnectionError` for network failures
- Pagination support with `Paginator` class and `paginate()` helper
- Resource abstractions (high-level API) with `Deployment`, `Plan`, `Task`, `AgentInstance`
- Waiter patterns for deployments, plans, tasks, and agent instances
- Idempotency key support for create operations
- OpenTelemetry integration (optional)
- Custom metrics hooks
- Connection pool configuration
- Full type annotations (PEP 561 compliant)
- Async/await support throughout

### Infrastructure

- Dynamic versioning with hatch-vcs (monorepo tag pattern: `atlas-sdk-v*`)
- CI/CD pipeline with GitHub Actions
  - Lint (ruff + mypy strict mode)
  - Security scanning (bandit + pip-audit)
  - Test with coverage (80% threshold)
  - API model validation against OpenAPI spec
  - Automated PyPI publishing via OIDC trusted publishing
- PEP 561 type marker (`py.typed`)

---

## Version Policy

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backward-compatible manner
- **PATCH** version for backward-compatible bug fixes

### Deprecation Policy

- Deprecated features emit `DeprecationWarning` when used
- Deprecated features are documented in this CHANGELOG under the "Deprecated" section
- Deprecated features are removed **no sooner than 2 minor versions** after deprecation
- Migration guides are provided in `docs/migrations/` for all breaking changes

### Pre-release Versions (0.x.x)

During pre-release development, minor version changes may contain breaking changes. Check the "Breaking Changes" section of each release carefully.

---

[Unreleased]: https://github.com/ryora/atlas/compare/atlas-sdk-v0.1.0...HEAD
[0.1.0]: https://github.com/ryora/atlas/releases/tag/atlas-sdk-v0.1.0
