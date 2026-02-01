"""Integration tests for Atlas SDK.

These tests require a running Control Plane instance. They are skipped by default
unless the ATLAS_INTEGRATION_TEST environment variable is set.

To run integration tests:
    ATLAS_INTEGRATION_TEST=1 ATLAS_BASE_URL=http://localhost:8000 pytest tests/integration/
"""
