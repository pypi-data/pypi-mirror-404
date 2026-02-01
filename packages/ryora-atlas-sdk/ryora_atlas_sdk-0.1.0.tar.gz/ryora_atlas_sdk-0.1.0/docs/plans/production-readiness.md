# Plan: Atlas SDK Production Readiness

This plan outlines the necessary enhancements to bring the `atlas-sdk` to a production-grade state, focusing on observability, resilience, scalability, and developer experience.

## Current Status (Updated 2025-01-30)

**Core Foundation: Production Ready** ✅
- Logging, timeouts, retry logic, error handling all implemented and tested
- Client separation complete (ControlPlaneClient, DispatchClient, WorkflowClient)
- Rate limiting (429) handling with Retry-After header support
- 200+ unit tests covering success paths, error handling, retry, and rate limiting

**Remaining Gaps:**
- Pagination inconsistent across list methods
- Error taxonomy minimal (AtlasHTTPStatusError, AtlasRateLimitError, AtlasTimeoutError)
- No integration tests
- Advanced patterns (async iterators, resource abstractions, idempotency) not started

## Goal
Improve the reliability, debuggability, and performance of the Atlas SDK for high-scale production environments while delivering an exceptional developer experience comparable to best-in-class SDKs (Stripe, AWS).

## Design Principles

The SDK should embody these qualities:
- **Strongly modeled resources** that mirror the API cleanly
- **Transparent handling** of idempotency, retries, and pagination
- **Clear error taxonomy** with semantic exception types and precise field paths
- **Backward compatibility** treated as a first-class constraint
- **Layered abstractions** with low-level (client) and high-level (resource) APIs
- **Excellent patterns** for pagination (stateful, pausable) and async waiters
- **Models as validators** that double as runtime validators and documentation
- **Type hints that drive behavior** (runtime constraints), not just documentation
- **Clean separation** of parsing (structural) vs validation (logical)
- **Dependency injection** that is explicit and testable
- **Intuitive naming** that reads like prose
- **API definitions** that generate/align with OpenAPI automatically

## Tasks

### 1. Observability: Logging & Tracing
- [x] Integrate standard Python `logging` into `ControlPlaneClient`.
- [x] Log request details (method, URL) at `DEBUG` level.
- [x] Log response status codes and durations at `DEBUG` level.
- [x] Ensure sensitive data (like API keys if added later) is masked in logs.
  - Implemented `_mask_sensitive()` function with denylist approach
  - Masks common sensitive keys: `api_key`, `apikey`, `api-key`, `x-api-key`, `authorization`, `token`, `secret`, `password`, `credential`, `cookie`, `session`, `bearer`
  - Case-insensitive matching for robustness
  - Applied to query params logging; ready for headers when needed
- [x] **Enhancement:** Implement structured logging to include safe request parameters and body details for better debugging.
  - Added query parameters logging (`params=...`)
  - Added request body size logging (`body_size=...`)
  - Added response content type logging (`content_type=...`)
  - Added response content length logging (`content_length=...`)
- [x] **Enhancement:** Add Request ID propagation (inject `X-Request-ID` header) to enable distributed tracing across Control Plane and Agents.
  - Auto-generates UUID if not provided via `request_id` parameter
  - Includes `X-Request-ID` header in all requests
  - Logs `request_id=` in both request and response log lines
  - Same request ID preserved across retries

### 2. Resilience: Timeouts & Retries
- [x] Implement a default timeout (e.g., 30 seconds) in `ControlPlaneClient` if none is provided.
- [x] Add support for configurable retry logic for transient errors (HTTP 502, 503, 504 and connection timeouts).
- [x] Propose whether to use an external dependency (like `tenacity`) or native `httpx` transport for retries. (Adopted `tenacity`)

### 3. Scalability: Pagination
- [x] **Research:** Analyze current Control Plane list endpoints and determine the best pagination strategy (Cursor vs. Limit/Offset).
- [x] **Interface:** Update SDK list methods to support pagination parameters (e.g., `limit`, `offset`, or `cursor`).
- [x] **Implementation:** (Blocker: requires Control Plane API updates) Update `ControlPlaneClient` to parse paginated responses.
- [x] **Gap:** Implement pagination for `list_agent_classes`, `list_agent_definitions`, `list_model_providers`, `list_system_prompts`, `list_tools`, `list_plans`, and `list_tasks` (currently missing). Only `list_deployments`, `query_grasp_analyses`, `logs`, and `list_agent_instances` have pagination support.
  - Control Plane API: Added `limit` (1-1000, default 100) and `offset` (>=0, default 0) parameters to all 7 endpoints.
  - SDK: Updated `ControlPlaneClient` and `WorkflowClient` with matching pagination parameters.
- [x] **DX:** Add async iterator pattern for transparent pagination (`async for deployment in client.deployments.list()`).
  - Implemented `paginate()` function in `atlas_sdk.pagination` module for simple one-shot pagination.
- [x] **Advanced Pattern:** Implement a dedicated `Paginator` class that manages state, allowing users to pause/resume iteration (serializing cursors) and transparently handles different strategies (Cursor vs Offset).
  - Implemented `Paginator` class with `PaginationState` for serializable pause/resume support.

### 4. Error Handling
- [x] Enhance `httpx.HTTPStatusError` handling.
- [x] Extract and include server-side error messages (JSON bodies) in exception details to provide more context to users.

### 5. Resilience: Rate Limiting
- [x] **Client-side backoff:** Handle HTTP 429 (Too Many Requests) responses with automatic backoff and retry.
  - Added 429 to retryable status codes (alongside 502, 503, 504)
  - Implemented custom wait strategy `_wait_with_retry_after()` for tenacity
  - Retries respect Retry-After header when present (capped at 60s)
  - Falls back to exponential backoff (2^attempt seconds, max 10s) otherwise
- [x] **Retry-After header:** Respect `Retry-After` header when present in 429 responses.
  - Added `_get_retry_after_from_response()` helper to parse header
  - Supports both numeric seconds (e.g., "120") and HTTP date formats
  - Past dates are handled gracefully (returns 0.0)
  - Added `AtlasRateLimitError` exception with `retry_after` property
  - After retries exhausted, raises `AtlasRateLimitError` with parsed retry_after value

### 6. Scalability: Connection Management
- [x] **Connection pool configuration:** Expose httpx connection pool settings (`max_connections`, `max_keepalive_connections`) for high-throughput scenarios.
  - Added `max_connections`, `max_keepalive_connections`, and `keepalive_expiry` parameters to `BaseClient.__init__()`.
  - All three clients (ControlPlaneClient, DispatchClient, WorkflowClient) inherit these settings.
  - Defaults match httpx defaults: 100/20/5.0 seconds for backward compatibility.
  - Settings are passed via `httpx.Limits` object when creating internal clients.
- [x] **Keep-alive tuning:** Document recommended settings for different deployment patterns.
  - Documented in `BaseClient` class docstring with recommendations for:
    - Single-threaded scripts: Use defaults (100/20/5.0)
    - High-throughput services: 200/50/30.0
    - Serverless/Lambda: 50/10/5.0
    - Long-running background workers: 100/30/120.0

### 7. Observability: Instrumentation
- [x] **OpenTelemetry integration:** Add optional spans for request/response cycles to integrate with observability platforms (Datadog, Jaeger, etc.).
  - Created `atlas_sdk.instrumentation` module with `TracingContext` for automatic span creation
  - Supports OpenTelemetry semantic conventions for HTTP client spans
  - Optional dependency: install `opentelemetry-api` via `pip install ryora-atlas-sdk[otel]`
  - Pass `enable_tracing=True` to client or use `InstrumentationConfig` for full control
  - Spans include: `http.request.method`, `url.path`, `http.response.status_code`, `atlas.request_id`
- [x] **Metrics hooks:** Expose hooks for custom metrics collection (request count, latency histograms, error rates).
  - Implemented `MetricsHandler` protocol with three hooks:
    - `on_request_start(method, url, request_id)` - called before request
    - `on_request_end(metrics: RequestMetrics)` - called on successful completion
    - `on_request_error(method, url, request_id, error)` - called on exception
  - `RequestMetrics` dataclass includes: method, url, request_id, status_code, duration_seconds, body sizes
  - Pass custom `metrics_handler` to client or via `InstrumentationConfig`
  - `NoOpMetricsHandler` provided as default (zero overhead when not using metrics)

### 8. Documentation
- [x] **Docstrings:** All public methods in ControlPlaneClient, DispatchClient, and WorkflowClient have docstrings with Args/Returns/Raises sections.
- [x] **API Reference:** Generate API reference documentation using Sphinx or MkDocs with autodoc.
  - Configured MkDocs with Material theme and mkdocstrings plugin
  - Created docs structure: getting-started/, guides/, examples/, api/
  - API reference pages auto-generate from docstrings
- [x] **Examples directory:** Create `examples/` with 10+ real-world usage patterns.
  - **Requirement:** Examples must be full "Use Case" narratives (e.g., "Robust Agent Deployment with Rollback"), not just code snippets.
  - [x] Basic CRUD workflows (01_basic_crud.md)
  - [x] Deployment workflow (02_deployment_workflow.md)
  - [x] Error handling and recovery (03_error_recovery.md)
  - [x] Custom retry configuration (04_custom_retry.md)
  - [x] Pagination (05_pagination.md)
  - [x] Resumable processing (06_resumable_processing.md)
  - [x] Waiters for async operations (07_waiters.md)
  - [x] Connection pool tuning (08_connection_pool.md)
  - [x] Concurrent operations (09_concurrent_operations.md)
  - [x] OpenTelemetry integration (10_opentelemetry.md)
  - [x] Custom metrics (11_custom_metrics.md)
  - [x] Testing with mocked clients (12_testing.md)
- [x] **Error handling guide:** Document all exception types, when they're raised, and recommended handling patterns.
  - Created docs/guides/error-handling.md with exception hierarchy, handling patterns, and examples
- [x] **Retry behavior docs:** Document retry logic, which errors trigger retries, and how to customize.
  - Created docs/guides/retry-behavior.md covering retry triggers, backoff strategy, and customization

### 9. Maintainability & Code Quality
- [x] **Refactor:** `ControlPlaneClient` is becoming monolithic. Split into domain-specific clients for better maintainability.
  - **Resolution:** See [client-separation.md](./client-separation.md) for the comprehensive plan to split into `ControlPlaneClient`, `DispatchClient`, and `WorkflowClient`.
- [x] **Security:** Verify `assert` statements are not used for runtime control flow.
  - Refactored `_ensure_client()` to return the `httpx.AsyncClient` instead of using `assert` for type narrowing.
  - No `assert` statements remain in SDK source code.

### 10. Testing
- [x] **Unit tests (success paths):** Comprehensive tests added for all three clients after client separation.
  - `test_control_plane.py`: 42+ test methods covering CRUD for all ControlPlaneClient methods
  - `test_dispatch.py`: 18+ test methods for DispatchClient
  - `test_workflow.py`: 25+ test methods for WorkflowClient
  - Total: 110+ test methods verifying request formation and response parsing
- [x] **Unit tests (validation):** Test Pydantic model validation for edge cases and malformed responses.
  - Created `tests/models/` directory with comprehensive validation tests:
    - `test_enums.py`: 24 tests for all enum types (AgentDefinitionStatus, ExecutionMode, DeploymentStatus, etc.)
    - `test_core_models.py`: 50+ tests for AgentDefinition, AgentInstance, Deployment, Plan models
    - `test_control_plane_models.py`: 41 tests for AgentClass, SystemPrompt, ModelProvider, Tool, GRASP, Blueprint
    - `test_dispatch_models.py`: 25 tests for SpawnRequest/Response, A2A models, AgentDirectory
  - Tests cover: required fields, optional fields, UUID validation, enum validation, Field constraints (ge/le), serialization
- [x] **Unit tests (pagination):** Test pagination parameter handling, response parsing, and state resumption.
  - Added `tests/test_pagination.py` with comprehensive tests for `PaginationState`, `Paginator`, and `paginate()`.
  - Added pagination parameter tests to `test_control_plane.py` and `test_workflow.py`.
- [x] **Unit tests (retry logic):** Comprehensive retry tests in `test_base.py` covering 502/503/504, ConnectError, ReadTimeout, and ConnectTimeout scenarios.
- [x] **Integration tests:** Create integration test suite that runs against a real Control Plane instance (staging environment).
  - Created `tests/integration/` directory with conftest.py providing fixtures and markers
  - Tests are skipped by default; enable with `ATLAS_INTEGRATION_TEST=1`
  - Environment variables: `ATLAS_BASE_URL`, `ATLAS_DISPATCH_URL` for endpoint configuration
  - Integration tests for: AgentClass, ModelProvider, SystemPrompt, Tool CRUD operations
  - Fixtures for test resource creation and cleanup
- [x] **Coverage threshold:** Achieve and maintain 80%+ code coverage.
  - Updated `pyproject.toml` coverage threshold from 70% to 80%
  - Current coverage: 95.57% (well above threshold)

### 11. Error Taxonomy
- [x] **Base hierarchy:** Create semantic exception hierarchy including domain-specific errors:
  ```
  AtlasError (base)
  ├── AtlasAPIError (all HTTP errors)
  │   ├── AtlasNotFoundError (404)
  │   ├── AtlasValidationError (400, 422)
  │   ├── AtlasConflictError (409)
  │   ├── AtlasAuthenticationError (401)
  │   ├── AtlasAuthorizationError (403)
  │   ├── AtlasRateLimitError (429)
  │   └── AtlasServerError (500-599)
  ├── AtlasDomainError (business logic)
  │   ├── InvalidBlueprintError
  │   ├── AgentExecutionError
  │   └── StateTransitionError
  ├── AtlasTimeoutError (request timeout)
  └── AtlasConnectionError (network failures)
  ```
  - Implemented complete exception hierarchy in `atlas_sdk/exceptions.py`
  - `AtlasAPIError.from_response()` factory method auto-selects appropriate subclass
  - `AtlasHTTPStatusError` kept as alias to `AtlasAPIError` for backward compatibility
- [x] **Detailed Validation:** `ValidationError` must expose a standard `details` list with `loc` (field path), `msg`, and `type`.
  - `AtlasValidationError.details` returns `list[ValidationErrorDetail]`
  - `ValidationErrorDetail` dataclass with `loc: tuple[str | int, ...]`, `msg: str`, `type: str`
  - Parses FastAPI/Pydantic validation error format automatically
- [x] **Request context:** All `AtlasAPIError` instances include `request_method`, `request_url`, and `request_id`.
  - `RequestContext` dataclass with `method`, `url`, `request_id` fields
  - All API errors expose `request_method`, `request_url`, `request_id` properties
  - Request ID extracted from `X-Request-ID` header
- [x] **Retry info:** `RateLimitError` exposes `retry_after` property when header is present.
  - Already implemented in previous work, verified working with new hierarchy

### 12. Resource Abstractions (High-Level API)
- [x] **Resource pattern:** Implement resource-oriented access pattern:
  ```python
  # Instead of: client.create_deployment(DeploymentCreate(...))
  # Offer:      client.deployments.create(...)
  ```
  - Implemented `DeploymentsResource`, `PlansResource`, `TasksResource`, `AgentInstancesResource` manager classes.
  - Clients expose resources via properties: `client.deployments`, `client.plans`, etc.
- [x] **Dependency Injection:** Resource classes (e.g., `Deployments`) must accept dependencies (HTTP Client) in their constructor, ensuring they are isolated and testable.
  - Defined `HTTPClientProtocol` for dependency injection.
  - All resource managers accept `HTTPClientProtocol` in constructor.
- [x] **Resource classes:** Create `Deployment`, `Plan`, `AgentInstance`, `Task` resource classes with bound methods.
  - Created `Deployment`, `Plan`, `Task`, `AgentInstance` wrapper classes.
  - Each exposes model fields as read-only properties.
- [x] **Relationship traversal:** Resources expose related resources (e.g., `plan.tasks` returns `list[Task]`).
  - `Plan.tasks` returns `list[Task]` resource objects.
- [x] **Refresh pattern:** Resources support `await resource.refresh()` to re-fetch from server.
  - All resources implement `refresh()` method.
- [x] **Save pattern:** Resources support `await resource.save()` to persist local changes.
  - `Deployment`, `Plan`, `Task` implement `save()`.
  - `AgentInstance` raises `NotImplementedError` (read-only).
- [x] **Backward compatibility:** Keep existing `client.create_deployment()` methods as aliases.
  - All existing client methods remain unchanged.

### 13. Waiter Patterns
- [x] **Deployment waiters:** `await client.deployments.wait_until_active(id, timeout=300)`.
  - Implemented `Deployment.wait_until_active()` method on resource class.
  - Implemented `DeploymentsResource.wait_until_active(deployment_id)` convenience method.
  - Supports `poll_interval`, `timeout`, and `on_progress` callback parameters.
- [x] **Plan completion:** `WorkflowClient.wait_for_plan_completion(plan_id, timeout, poll_interval)` implemented.
  - Enhanced with `on_progress` callback parameter.
  - Enhanced timeout error includes `last_state`, `timeout_seconds`, and `operation`.
- [x] **Task completion:** `WorkflowClient.wait_for_task_completion(task_id, timeout, poll_interval)` implemented.
  - Enhanced with `on_progress` callback parameter.
  - Enhanced timeout error includes `last_state`, `timeout_seconds`, and `operation`.
- [x] **Agent instance:** `await client.agent_instances.wait_until_active(id)`.
  - Implemented `AgentInstance.wait_until_active()` and `wait_for_completion()` methods.
  - Implemented `AgentInstancesResource.wait_until_active(id)` and `wait_for_completion(id)` convenience methods.
  - Supports `poll_interval`, `timeout`, and `on_progress` callback parameters.
- [x] **Configurable polling:** Expose `poll_interval` (default 2s for plans, 1s for tasks/instances) and `timeout` parameters.
  - All waiter methods accept `poll_interval` (seconds between polls) and `timeout` (max wait time).
  - Timeout defaults: 300s for deployments/instances (5 min), None (indefinite) for plans/tasks.
- [x] **Progress callbacks:** Support optional callback for progress updates during long waits.
  - All waiter methods accept `on_progress` callback (`Callable[[StateModel], Awaitable[None] | None]`).
  - Callbacks can be sync or async functions.
  - Called after each poll with current resource state.
- [x] **Timeout behavior:** Raise `AtlasTimeoutError` with last known state on timeout.
  - `AtlasTimeoutError.operation` - description of operation that timed out.
  - `AtlasTimeoutError.timeout_seconds` - the timeout value that was exceeded.
  - `AtlasTimeoutError.last_state` - last known resource state before timeout.

### 14. Idempotency
- [x] **Idempotency keys:** Accept optional `idempotency_key: str` parameter on all create operations.
  - Added `idempotency_key` parameter to `BaseClient._request()`.
  - All create methods in ControlPlaneClient, DispatchClient, and WorkflowClient support idempotency keys.
  - Resource managers (DeploymentsResource, PlansResource) also support idempotency keys.
- [x] **Header injection:** Send `Idempotency-Key` header when key is provided.
  - `Idempotency-Key` header is injected when `idempotency_key` parameter is not None.
  - Key is preserved across retries.
- [x] **Auto-generation option:** Offer `idempotency_key="auto"` to generate UUID-based keys automatically.
  - Special value "auto" generates a UUID v4 for the key.
- [x] **Documentation:** Document idempotency guarantees and key format requirements.
  - Created `docs/guides/idempotency.md` with usage examples and best practices.

### 15. SDK-API Synchronization
- [x] **OpenAPI validation:** Establish a CI pipeline where SDK models are **strictly verified** against the Control Plane OpenAPI spec to ensure zero drift.
  - Control Plane exposes OpenAPI at `/api/v1/openapi.json` (configured in `main.py`)
  - Created `control_plane/scripts/export_openapi.py` to generate spec without running server
  - Created `atlas-sdk/scripts/validate_models.py` for model validation
  - Added `api-validation` job to `.github/workflows/atlas-sdk.yml` that:
    1. Generates OpenAPI spec from Control Plane
    2. Validates SDK models against the spec
    3. Fails CI on drift (missing fields, type mismatches)
    4. Uploads OpenAPI spec as artifact for debugging
- [x] **Model generation:** Evaluate generating model stubs from OpenAPI (datamodel-code-generator) as the "first consumer" test.
  - Evaluated `datamodel-code-generator` but decided against full adoption:
    - SDK models have convenience methods and Pydantic configurations not expressible in OpenAPI
    - Instead, validation script compares hand-written models against OpenAPI schemas
    - This preserves SDK ergonomics while ensuring API alignment
- [x] **Version alignment:** SDK version tracks Control Plane API version (e.g., SDK 1.2.x works with API v1.2).
  - Created `docs/VERSION_COMPATIBILITY.md` with:
    - Semantic versioning policy
    - Compatibility matrix (MAJOR must match, MINOR flexible)
    - Version detection and validation approach
    - Migration guide structure
- [x] **Deprecation detection:** CI warns when SDK uses deprecated API fields.
  - `validate_models.py` checks for `deprecated: true` in OpenAPI field schemas
  - Deprecated fields reported as warnings in CI output
  - `--strict` flag fails CI on any warnings including deprecations

### 16. Backward Compatibility Policy
- [x] **Deprecation warnings:** Use `warnings.warn(DeprecationWarning)` for deprecated methods/parameters.
  - Created `atlas_sdk/deprecation.py` module with comprehensive deprecation utilities:
    - `deprecated()` decorator for deprecated functions/methods
    - `deprecated_parameter()` decorator for deprecated function parameters
    - `deprecated_class()` decorator for deprecated classes
    - `deprecated_alias()` for creating deprecated class aliases with proper inheritance
    - `warn_deprecated()` function for programmatic deprecation warnings
  - Updated `AtlasHTTPStatusError` to emit `DeprecationWarning` when instantiated
  - 18 unit tests covering all deprecation utilities
- [x] **Sunset timeline:** Deprecated features removed no sooner than 2 minor versions after deprecation.
  - Documented in CHANGELOG.md Version Policy section
  - Documented in backward-compatibility guide
  - `AtlasHTTPStatusError` deprecated in 0.2.0, will be removed in 0.4.0
- [x] **CHANGELOG:** Maintain `CHANGELOG.md` with "Breaking Changes" section prominently featured.
  - Added "Breaking Changes" section template at top of each release
  - Added "Deprecated" section for tracking deprecations
  - Added "Version Policy" section with deprecation policy
  - Added links to migration guides
- [x] **Version policy:** Document and follow semantic versioning strictly.
  - Documented in CHANGELOG.md
  - Documented in VERSION_COMPATIBILITY.md
  - Documented in backward-compatibility guide
- [x] **Migration guides:** Provide migration guides for any breaking changes.
  - Created `docs/migrations/` directory with index
  - Moved existing migration-guide.md to `docs/migrations/client-separation.md`
  - Created `docs/guides/backward-compatibility.md` guide
  - Updated mkdocs.yml navigation to include new structure

### 17. Input Validation (Fail Fast)
- [x] **Strict Typing:** Adopt **Pydantic V2** with strict type enforcement (e.g., `strict=True`) so type hints act as runtime constraints.
  - Created `InputModel` base class with `extra="forbid"` to reject unknown fields
  - Created `ResponseModel` base class with `from_attributes=True` for ORM support
  - All Create/Update models now inherit from `InputModel`
  - All Read models now inherit from `ResponseModel`
  - Field constraints added: `min_length=1` for required strings, `ge=0` for sequences
- [x] **Separation of Concerns:** Ensure clean separation between **Parsing** (structural validity via Pydantic) and **Validation** (logical business rules via explicit validators).
  - Created `atlas_sdk.validation` module with explicit validation utilities
  - `validate_model()` for constructing models with enhanced error messages
  - `validate_instance()` for re-validating existing model instances
  - `validate_uuid()` and `validate_enum()` for standalone validation
  - Pydantic handles structural validation; helpers provide enhanced error context
- [x] **Pre-flight validation:** Validate Pydantic models before making HTTP calls.
  - Models are validated at construction time (Pydantic's default behavior)
  - `InputModel.extra="forbid"` catches unknown fields immediately
  - `BaseClient._validate_model()` helper for explicit validation
  - `AtlasInputValidationError` raised for client-side validation failures
- [x] **UUID format check:** Validate UUID format client-side with clear error message.
  - `validate_uuid()` function provides enhanced error messages
  - Error includes example of valid UUID format
  - Error includes the actual invalid value for debugging
- [x] **Required field check:** Surface missing required fields immediately, not after network round-trip.
  - Pydantic's built-in validation handles required fields
  - Enhanced error message: "This field is required."
  - Field path (`loc`) included in `InputValidationErrorDetail`
- [x] **Enum validation:** Reject invalid enum values with message listing valid options.
  - `validate_enum()` function provides enhanced error messages
  - Error lists all valid options for the enum
  - Example: "Invalid value 'x' for status. Valid options are: 'spawning', 'active', 'completed', 'failed'."
- [x] **Type coercion transparency:** Document which fields are auto-coerced (e.g., str → UUID).
  - Created `docs/guides/input-validation.md` guide
  - Documents UUID coercion (str → UUID accepted)
  - Documents enum coercion (str value → Enum member accepted)
  - Documents `extra="forbid"` behavior
  - Includes type coercion summary table

### 18. Dependency Injection & Testability
- [x] **HTTP client interface:** Define `HTTPClient` protocol for easy mocking.
  - `HTTPClientProtocol` already defined in `atlas_sdk.resources.base`
  - Protocol defines `_request()` and `_raise_for_status()` methods
  - Used for dependency injection in all resource classes
- [x] **Constructor injection:** All clients accept optional `http_client` parameter.
  - `BaseClient` accepts `client: httpx.AsyncClient | None` parameter
  - All clients (ControlPlaneClient, DispatchClient, WorkflowClient) inherit this
  - `MockHTTPClient` can be injected for testing
- [x] **Test fixtures:** Provide `pytest` fixtures for common mocking scenarios.
  - Created `atlas_sdk.testing.fixtures` module with pytest fixtures
  - Fixtures: `mock_http_client`, `fake_control_plane`, `fake_dispatch`, `fake_workflow`
  - Async variants: `async_mock_http_client`, `async_fake_control_plane`, etc.
  - Helper fixtures: `reset_factory_counters`, `test_uuid`, `test_deployment_id`
- [x] **Fake client:** Offer `FakeControlPlaneClient` for unit testing without HTTP mocking.
  - Created `FakeControlPlaneClient` with in-memory storage for all entities
  - Created `FakeDispatchClient` for agent lifecycle testing
  - Created `FakeWorkflowClient` for workflow orchestration testing
  - All fake clients support CRUD operations without network calls
  - `FakeNotFoundError` raised for missing resources
- [x] **Response factories:** Provide factory functions to create valid response objects for tests.
  - Created `atlas_sdk.testing.factories` module with 20+ factory functions
  - Agent Class: `factory_agent_class()`, `factory_agent_class_create()`
  - Agent Definition: `factory_agent_definition()`, `factory_agent_definition_config()`
  - Deployment: `factory_deployment()`, `factory_deployment_create()`
  - Plan: `factory_plan()`, `factory_plan_with_tasks()`, `factory_task()`
  - Model Provider: `factory_model_provider()`, `factory_system_prompt()`, `factory_tool()`
  - All factories accept keyword overrides for customization
  - `reset_factories()` for deterministic test data

## Acceptance Criteria

### Observability
- `ControlPlaneClient` emits logs that can be captured by a standard logger.
- Logs include enough context to trace a request-response cycle without leaking secrets.
- Request IDs are propagated via `X-Request-ID` header for distributed tracing.
- OpenTelemetry spans are emitted when instrumentation is enabled.

### Resilience
- SDK calls no longer hang indefinitely due to missing timeouts.
- Transient network blips are handled automatically via retries without failing the top-level request.
- Rate limiting (429) responses trigger automatic backoff and retry.
- Idempotency keys enable safe retries of create operations.

### Scalability
- List methods (e.g., `list_deployments`) can handle thousands of records via pagination without timing out or consuming excessive memory.
- All list methods support consistent pagination parameters.
- Async iterators allow memory-efficient iteration over large result sets.
- Connection pool settings can be tuned for high-throughput scenarios.

### Error Handling
- When a 4xx or 5xx occurs, the resulting exception is a semantic type (e.g., `NotFoundError`, `RateLimitError`) or a domain-specific error.
- All API errors include request context: method, URL, and request_id.
- Validation errors include precise field paths (`loc`) pointing to the problematic data.
- Errors surface client-side before network calls when possible.

### Developer Experience
- High-level resource pattern available (`client.deployments.create()`) with proper dependency injection.
- Waiters available for all async operations with configurable timeouts.
- Method names read like prose and are consistent across resources.
- 10+ robust examples (narratives) cover common workflows.
- Type hints provide IDE autocompletion and act as runtime constraints.

### Documentation
- All public classes and methods have docstrings.
- API reference is generated and published.
- Examples cover common usage patterns.
- Error handling and retry behavior are documented.
- Migration guides exist for any breaking changes.

### Testing
- Unit test coverage is at least 80%.
- All client methods have success path tests.
- Integration tests validate against real Control Plane.
- Retry, pagination, and waiter logic are explicitly tested.
- Test fixtures and fakes are provided for downstream users.

### Backward Compatibility
- Deprecation warnings are emitted for deprecated features.
- Breaking changes are documented in CHANGELOG.
- Semantic versioning is followed strictly.
- Migration path is clear for any breaking changes.

### SDK-API Alignment
- SDK models are generated or strictly verified against OpenAPI spec in CI.
- SDK version is aligned with Control Plane API version.