# Plan: Pre-Release Actions for v0.1.0

This document captures action items from a comprehensive review of the atlas-sdk prior to the first public release.

## Review Date
2025-01-30

## Executive Summary

The SDK is **ready for release** with minor fixes. The architecture is clean, testing is strong (833 tests), and documentation is comprehensive. Two issues require attention before release.

| Area | Status | Priority |
|------|--------|----------|
| Exception Documentation | **Outdated** | Must fix before release |
| Dispatch/Workflow Tests | **Minimal** | Should fix before release |
| Testing Module Size | **Observation** | Consider for future |

---

## 1. Must Fix Before Release

### 1.1 Update Exception Documentation (HIGH)

The exception hierarchy documentation references deprecated exception names.

#### Findings

**docs/api/exceptions.md**
- Shows `AtlasHTTPStatusError` as the base for HTTP errors
- Actual code uses `AtlasAPIError` (old name works via deprecation wrapper)

**docs/guides/error-handling.md**
- Code examples use `AtlasHTTPStatusError` instead of preferred `AtlasAPIError`

#### Actual Exception Hierarchy (from code)

```
AtlasError (base)
├── AtlasAPIError (all HTTP errors) ← renamed from AtlasHTTPStatusError
│   ├── AtlasNotFoundError (404)
│   ├── AtlasValidationError (400, 422)
│   ├── AtlasConflictError (409)
│   ├── AtlasAuthenticationError (401)
│   ├── AtlasAuthorizationError (403)
│   ├── AtlasRateLimitError (429)
│   └── AtlasServerError (5xx)
├── AtlasDomainError (business logic errors)
├── AtlasTimeoutError (request/polling timeout)
├── AtlasConnectionError (network failures)
└── AtlasInputValidationError (client-side validation)
```

#### Actions

- [x] **Update docs/api/exceptions.md** - Replace `AtlasHTTPStatusError` with `AtlasAPIError` in hierarchy diagram and descriptions
- [x] **Update docs/guides/error-handling.md** - Replace exception names in all code examples
- [x] **Search for other occurrences** - `grep -r "AtlasHTTPStatusError" docs/` and update any remaining references

---

### 1.2 Add Dispatch/Workflow Client Tests (HIGH)

ControlPlaneClient has extensive test coverage. DispatchClient and WorkflowClient have minimal tests by comparison.

#### Current State

| Client | Test Coverage | Assessment |
|--------|--------------|------------|
| ControlPlaneClient | Extensive | 40+ methods tested with multiple scenarios |
| DispatchClient | Minimal | Basic happy path only |
| WorkflowClient | Moderate | Some tests but gaps in error handling |

#### Actions

- [ ] **Add DispatchClient tests** - Cover spawn, stop, status, A2A communication methods
- [ ] **Add WorkflowClient error tests** - Cover polling failures, timeout scenarios, callback edge cases
- [ ] **Verify test parity** - Ensure same test patterns (request construction, response parsing, error handling) applied to all clients

---

## 2. Should Fix Before Release

### 2.1 Integration Test Coverage

The integration tests exist but require external services and are minimal.

#### Actions

- [ ] **Document integration test setup** - Add instructions for running integration tests locally
- [ ] **Add integration test markers** - Ensure `@pytest.mark.integration` is consistently applied

---

## 3. Observations (Not Blockers)

### 3.1 Testing Module Size

The testing utilities are extensive (2,961 lines total):

| File | Lines | Purpose |
|------|-------|---------|
| `fake_clients.py` | 1,192 | Full in-memory client implementations |
| `factories.py` | 935 | Test data factories |
| `mock_client.py` | 490 | HTTP mocking utilities |
| `fixtures.py` | 344 | pytest fixtures |

This is comprehensive but may be scope creep for an SDK. Most users just want to mock HTTP.

#### Future Consideration

- [ ] **Consider separate package** - `atlas-sdk-testing` for extensive testing utilities
- [ ] **Document testing approach** - Add TESTING.md explaining when to use MockHTTPClient vs FakeClients

---

### 3.2 Large File Sizes

Some files are large and could be split for maintainability:

| File | Lines | Suggested Split |
|------|-------|-----------------|
| `base.py` | 732 | HTTP handling, retry logic, instrumentation |
| `control_plane.py` | 1,002 | Could split by resource type |
| `exceptions.py` | 888 | Already well-organized, acceptable |

#### Future Consideration

- [ ] **Split base.py** - Extract retry logic to `_internal/retry.py`, instrumentation to separate module
- [ ] **Consider resource-based client organization** - Group methods by resource type in separate files

---

### 3.3 Type Coercion Ambiguity

Three ways to validate input currently exist:
1. `InputModel` - allows coercion (current default, deprecated)
2. `StrictModel` - no coercion
3. `validate_model()` - explicit strict validation

#### Future Consideration

- [ ] **Clarify recommended approach** - Document when to use each validation style
- [ ] **Consider deprecation timeline** - Plan removal of coercion in future major version

---

## 4. Review Summary

### Strengths

- Clean separation of concerns (clients, models, resources, internal)
- Async-first design with proper patterns
- Comprehensive exception hierarchy with semantic meaning
- Strong unit test coverage (833 tests, ~20:1 test:source ratio)
- Well-documented with 35+ doc pages and 12 working examples
- Good retry logic with Retry-After header support
- OpenTelemetry instrumentation (optional)

### Grade: A-

Ship it after fixing the exception documentation and adding Dispatch/Workflow tests.

---

## 5. Acceptance Criteria

### For v0.1.0 Public Release

- [x] All `AtlasHTTPStatusError` references in docs replaced with `AtlasAPIError`
- [x] DispatchClient has at least 10 meaningful tests (15 tests covering all methods)
- [x] WorkflowClient error handling tests added (48 tests including timeout, callback, and error handling)
- [x] All existing tests pass
- [ ] No reduction in code coverage

---

## 6. Files Reference

### Documentation to Update

| File | Issue |
|------|-------|
| `docs/api/exceptions.md` | Uses deprecated exception name |
| `docs/guides/error-handling.md` | Code examples use deprecated names |

### Tests to Add

| File | Gap |
|------|-----|
| `tests/clients/test_dispatch.py` | Needs comprehensive coverage |
| `tests/clients/test_workflow.py` | Needs error scenario tests |
