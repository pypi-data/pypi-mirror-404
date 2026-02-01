"""Resource abstractions for Atlas SDK.

This module provides a high-level, resource-oriented API for interacting
with Atlas entities. Instead of calling methods directly on clients, you
can use the fluent resource pattern:

    # Instead of:
    deployment = await client.create_deployment(DeploymentCreate(...))

    # You can use:
    deployment = await client.deployments.create(...)

Resource objects returned from these methods support:
- `await resource.refresh()` - Re-fetch the resource from the server
- `await resource.save()` - Persist local changes to the server
- `await resource.delete()` - Delete the resource from the server

Resources also expose related entities:
- `plan.tasks` - Returns list of Task resources
- `deployment.plans` - Access plans within a deployment
"""

from atlas_sdk.resources.base import HTTPClientProtocol, Resource, ResourceManager
from atlas_sdk.resources.deployments import Deployment, DeploymentsResource
from atlas_sdk.resources.plans import Plan, PlansResource
from atlas_sdk.resources.tasks import Task, TasksResource
from atlas_sdk.resources.agent_instances import AgentInstance, AgentInstancesResource

__all__ = [
    # Base
    "HTTPClientProtocol",
    "Resource",
    "ResourceManager",
    # Deployments
    "Deployment",
    "DeploymentsResource",
    # Plans
    "Plan",
    "PlansResource",
    # Tasks
    "Task",
    "TasksResource",
    # Agent Instances
    "AgentInstance",
    "AgentInstancesResource",
]
