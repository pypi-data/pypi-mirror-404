# Basic CRUD Operations

This example demonstrates the fundamental Create, Read, Update, and Delete operations for managing Atlas resources.

## Use Case: Setting Up a New Agent Class

You're a platform engineer setting up a new agent class for your security team. You need to:

1. Create a model provider for the LLM service
2. Create an agent class for the security scanner concept
3. Create system prompts for the agent
4. Create agent definitions that combine everything
5. Update and clean up resources as needed

## Prerequisites

- Running Control Plane instance at `http://localhost:8000`
- Atlas SDK installed

## Complete Example

```python
"""
Example: Basic CRUD Operations
Use Case: Setting up a new security scanner agent class

This example shows how to:
- Create model providers, agent classes, system prompts, and definitions
- Read and list resources
- Update existing resources
- Delete resources when no longer needed
"""

import asyncio
from atlas_sdk import ControlPlaneClient
from atlas_sdk.models import (
    AgentClassCreate,
    AgentClassUpdate,
    AgentDefinitionCreate,
    AgentDefinitionUpdate,
    ModelProviderCreate,
    SystemPromptCreate,
)


async def main():
    async with ControlPlaneClient(base_url="http://localhost:8000") as client:
        # ===== CREATE OPERATIONS =====

        # Step 1: Create a model provider
        print("Creating model provider...")
        provider = await client.create_model_provider(
            ModelProviderCreate(
                name="openai-production",
                api_base_url="https://api.openai.com/v1",
                config={"default_model": "gpt-4"},
            )
        )
        print(f"  Created provider: {provider.name} (ID: {provider.id})")

        # Step 2: Create an agent class
        print("\nCreating agent class...")
        agent_class = await client.create_agent_class(
            AgentClassCreate(
                name="SecurityScanner",
                description="Agent class for security vulnerability scanning",
            )
        )
        print(f"  Created class: {agent_class.name} (ID: {agent_class.id})")

        # Step 3: Create a system prompt for the class
        print("\nCreating system prompt...")
        system_prompt = await client.create_system_prompt(
            SystemPromptCreate(
                name="security-scanner-v1",
                content="""You are a security scanning agent. Your responsibilities:
1. Analyze code for common vulnerabilities (OWASP Top 10)
2. Identify potential security misconfigurations
3. Report findings with severity levels and remediation steps

Always be thorough but avoid false positives. When uncertain, explain your reasoning.""",
                agent_class_id=agent_class.id,
            )
        )
        print(f"  Created prompt: {system_prompt.name} (ID: {system_prompt.id})")

        # Step 4: Create an agent definition
        print("\nCreating agent definition...")
        definition = await client.create_agent_definition(
            AgentDefinitionCreate(
                name="security-scanner-gpt4",
                description="GPT-4 based security scanner",
                agent_class_id=agent_class.id,
                model_provider_id=provider.id,
                model_name="gpt-4",
                system_prompt_id=system_prompt.id,
                config={"temperature": 0.1, "max_tokens": 4096},
            )
        )
        print(f"  Created definition: {definition.name} (ID: {definition.id})")

        # ===== READ OPERATIONS =====

        print("\n--- Reading Resources ---")

        # Read single resources by ID
        fetched_class = await client.get_agent_class(agent_class.id)
        print(f"\nFetched class: {fetched_class.name}")
        print(f"  Description: {fetched_class.description}")

        fetched_definition = await client.get_agent_definition(definition.id)
        print(f"\nFetched definition: {fetched_definition.name}")
        print(f"  Model: {fetched_definition.model_name}")

        # List all resources
        print("\nListing all agent classes...")
        all_classes = await client.list_agent_classes(limit=100)
        print(f"  Found {len(all_classes)} agent classes:")
        for cls in all_classes[:5]:  # Show first 5
            print(f"    - {cls.name}")

        print("\nListing all definitions...")
        all_definitions = await client.list_agent_definitions(limit=100)
        print(f"  Found {len(all_definitions)} definitions:")
        for defn in all_definitions[:5]:
            print(f"    - {defn.name}")

        # ===== UPDATE OPERATIONS =====

        print("\n--- Updating Resources ---")

        # Update the agent class
        print("\nUpdating agent class description...")
        updated_class = await client.update_agent_class(
            agent_class.id,
            AgentClassUpdate(
                description="Agent class for comprehensive security vulnerability scanning and code analysis",
            ),
        )
        print(f"  Updated description: {updated_class.description}")

        # Update the agent definition
        print("\nUpdating agent definition config...")
        updated_definition = await client.update_agent_definition(
            definition.id,
            AgentDefinitionUpdate(
                config={"temperature": 0.0, "max_tokens": 8192},  # Stricter, more output
            ),
        )
        print(f"  Updated config: {updated_definition.config}")

        # ===== DELETE OPERATIONS =====

        print("\n--- Cleanup (Delete Operations) ---")

        # Delete in reverse dependency order
        print("\nDeleting agent definition...")
        await client.delete_agent_definition(definition.id)
        print("  Deleted.")

        print("Deleting system prompt...")
        await client.delete_system_prompt(system_prompt.id)
        print("  Deleted.")

        print("Deleting agent class...")
        await client.delete_agent_class(agent_class.id)
        print("  Deleted.")

        print("Deleting model provider...")
        await client.delete_model_provider(provider.id)
        print("  Deleted.")

        print("\nAll resources cleaned up successfully!")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Points

### Resource Dependencies

Resources have dependencies that affect creation and deletion order:

```
ModelProvider (independent)
      ↓
AgentClass (independent)
      ↓
SystemPrompt (requires AgentClass)
      ↓
AgentDefinition (requires AgentClass, ModelProvider, optionally SystemPrompt)
```

**Create**: Start with independent resources, then dependent ones.
**Delete**: Delete dependents first, then their dependencies.

### Context Manager Usage

Always use the client as an async context manager to ensure proper cleanup:

```python
async with ControlPlaneClient(base_url="...") as client:
    # Client is properly initialized and will be closed automatically
    ...
```

### Partial Updates

Update methods accept partial data - only include fields you want to change:

```python
# Only update the description, leave other fields unchanged
await client.update_agent_class(
    class_id,
    AgentClassUpdate(description="New description only")
)
```

## Error Handling

See [Robust Error Recovery](03_error_recovery.md) for handling errors in CRUD operations.

## Next Steps

- [Deployment Workflow](02_deployment_workflow.md) - Deploy your agent definitions
- [Custom Retry Configuration](04_custom_retry.md) - Handle transient failures
