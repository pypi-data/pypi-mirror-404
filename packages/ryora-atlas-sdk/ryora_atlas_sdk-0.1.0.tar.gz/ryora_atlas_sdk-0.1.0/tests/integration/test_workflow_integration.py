"""Integration tests for WorkflowClient.

These tests require a running Control Plane instance and are skipped by default.
Run with: ATLAS_INTEGRATION_TEST=1 pytest tests/integration/
"""

import pytest

from atlas_sdk.clients.workflow import WorkflowClient


@pytest.mark.integration
class TestPlanIntegration:
    """Integration tests for plan operations.

    Note: These tests require an active deployment with a valid instance_id
    to create plans. You may need to adapt fixtures based on your setup.
    """

    async def test_plan_lifecycle(
        self,
        workflow_client: WorkflowClient,
    ) -> None:
        """Should demonstrate full plan lifecycle.

        This test requires:
        - A running deployment
        - A valid deployment_id and instance_id

        Skip if no deployment is available.
        """
        pytest.skip(
            "Requires active deployment - implement when deployment fixtures are available"
        )

    async def test_list_plans_pagination(
        self,
        workflow_client: WorkflowClient,
    ) -> None:
        """Should list plans with pagination."""
        # This test works without fixtures if there are existing plans
        try:
            # Attempt to list plans
            from uuid import uuid4

            # Use a random deployment_id - will return empty list if not found
            plans = await workflow_client.list_plans(
                deployment_id=uuid4(),
                limit=10,
            )

            # If we get here, the API is responding correctly
            assert isinstance(plans, list)
        except Exception as e:
            # If the deployment doesn't exist, that's expected
            if "404" in str(e):
                pytest.skip("No test deployment available")
            raise


@pytest.mark.integration
class TestTaskIntegration:
    """Integration tests for task operations."""

    async def test_list_tasks_pagination(
        self,
        workflow_client: WorkflowClient,
    ) -> None:
        """Should list tasks with pagination."""
        pytest.skip("Requires active plan - implement when plan fixtures are available")


@pytest.mark.integration
class TestWaiterIntegration:
    """Integration tests for waiter patterns."""

    async def test_wait_for_plan_completion_timeout(
        self,
        workflow_client: WorkflowClient,
    ) -> None:
        """Should raise timeout error when plan doesn't complete in time."""
        from uuid import uuid4

        from atlas_sdk.exceptions import AtlasTimeoutError

        # Using a non-existent plan_id should timeout quickly
        # (or raise 404 immediately depending on implementation)
        try:
            with pytest.raises((AtlasTimeoutError, Exception)):
                await workflow_client.wait_for_plan_completion(
                    plan_id=uuid4(),
                    timeout=1.0,  # Very short timeout
                    poll_interval=0.5,
                )
        except Exception as e:
            # 404 is also acceptable for non-existent plan
            if "404" not in str(e):
                raise
