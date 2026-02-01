# Exceptions

The Atlas SDK provides a hierarchy of exceptions for handling different error conditions.

## Exception Hierarchy

```
AtlasError (base)
├── AtlasAPIError (all HTTP errors)
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

## Quick Reference

| Exception | Trigger | When to Catch |
|-----------|---------|---------------|
| `AtlasAPIError` | Any 4xx/5xx HTTP response | General HTTP error handling |
| `AtlasNotFoundError` | HTTP 404 (resource not found) | Handle missing resources |
| `AtlasValidationError` | HTTP 400/422 (validation failed) | Handle input errors |
| `AtlasRateLimitError` | HTTP 429 (rate limited) | Implement custom backoff logic |
| `AtlasTimeoutError` | Polling timeout (wait_for_*) | Handle long-running operations |
| `AtlasConnectionError` | Network failure | Handle connectivity issues |

## API Reference

::: atlas_sdk.exceptions
    options:
      show_root_heading: false
      members_order: source
