#!/usr/bin/env python3
"""
Validate SDK Pydantic models against Control Plane OpenAPI specification.

This script compares the SDK models with the Control Plane API schema to detect:
- Missing fields (field in API but not in SDK)
- Extra fields (field in SDK but not in API)
- Type mismatches between SDK and API
- Required vs optional field differences
- Deprecated fields in the API

Usage:
    # Fetch OpenAPI from running Control Plane
    python scripts/validate_models.py --url http://localhost:8000/api/v1/openapi.json

    # Use a saved OpenAPI spec file
    python scripts/validate_models.py --file openapi.json

    # CI mode: fail on any drift
    python scripts/validate_models.py --file openapi.json --strict

    # Generate OpenAPI spec from Control Plane (requires running instance)
    python scripts/validate_models.py --url http://localhost:8000/api/v1/openapi.json --save openapi.json
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, get_args, get_origin
from uuid import UUID

import httpx
from pydantic import BaseModel
from pydantic.fields import FieldInfo


# SDK model mapping: OpenAPI schema name -> SDK model import path
SDK_MODEL_MAPPING: dict[str, str] = {
    # Agent Definition
    "AgentDefinitionCreate": "atlas_sdk.models.AgentDefinitionCreate",
    "AgentDefinitionUpdate": "atlas_sdk.models.AgentDefinitionUpdate",
    "AgentDefinitionRead": "atlas_sdk.models.AgentDefinitionRead",
    # Agent Instance
    "AgentInstanceCreate": "atlas_sdk.models.AgentInstanceCreate",
    "AgentInstanceUpdate": "atlas_sdk.models.AgentInstanceUpdate",
    "AgentInstanceRead": "atlas_sdk.models.AgentInstanceRead",
    # Deployment
    "DeploymentCreate": "atlas_sdk.models.DeploymentCreate",
    "DeploymentUpdate": "atlas_sdk.models.DeploymentUpdate",
    "DeploymentRead": "atlas_sdk.models.DeploymentRead",
    # Plan
    "PlanCreate": "atlas_sdk.models.PlanCreate",
    "PlanUpdate": "atlas_sdk.models.PlanUpdate",
    "PlanRead": "atlas_sdk.models.PlanRead",
    "PlanReadWithTasks": "atlas_sdk.models.PlanReadWithTasks",
    "PlanCreateResponse": "atlas_sdk.models.PlanCreateResponse",
    # Task
    "PlanTaskCreate": "atlas_sdk.models.PlanTaskCreate",
    "PlanTaskUpdate": "atlas_sdk.models.PlanTaskUpdate",
    "PlanTaskRead": "atlas_sdk.models.PlanTaskRead",
    "PlanTaskReadEnriched": "atlas_sdk.models.PlanTaskReadEnriched",
    "TasksAppend": "atlas_sdk.models.TasksAppend",
    "TasksAppendResponse": "atlas_sdk.models.TasksAppendResponse",
    # Agent Class
    "AgentClassCreate": "atlas_sdk.models.AgentClassCreate",
    "AgentClassUpdate": "atlas_sdk.models.AgentClassUpdate",
    "AgentClassRead": "atlas_sdk.models.AgentClassRead",
    # Model Provider
    "ModelProviderCreate": "atlas_sdk.models.ModelProviderCreate",
    "ModelProviderUpdate": "atlas_sdk.models.ModelProviderUpdate",
    "ModelProviderRead": "atlas_sdk.models.ModelProviderRead",
    # System Prompt
    "SystemPromptCreate": "atlas_sdk.models.SystemPromptCreate",
    "SystemPromptUpdate": "atlas_sdk.models.SystemPromptUpdate",
    "SystemPromptRead": "atlas_sdk.models.SystemPromptRead",
    # Tool
    "ToolCreate": "atlas_sdk.models.ToolCreate",
    "ToolUpdate": "atlas_sdk.models.ToolUpdate",
    "ToolRead": "atlas_sdk.models.ToolRead",
    "ToolSyncRequest": "atlas_sdk.models.ToolSyncRequest",
    # GRASP
    "GraspAnalysisCreate": "atlas_sdk.models.GraspAnalysisCreate",
    "GraspAnalysisRead": "atlas_sdk.models.GraspAnalysisRead",
    "GraspAnalysisSummary": "atlas_sdk.models.GraspAnalysisSummary",
    # Blueprint
    "BlueprintCreate": "atlas_sdk.models.BlueprintCreate",
    "BlueprintUpdate": "atlas_sdk.models.BlueprintUpdate",
    "BlueprintRead": "atlas_sdk.models.BlueprintRead",
}

# OpenAPI type to Python type mapping
OPENAPI_TYPE_MAP: dict[str, type | str] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}

# OpenAPI format to Python type mapping
OPENAPI_FORMAT_MAP: dict[str, type] = {
    "uuid": UUID,
    "date-time": datetime,
    "date": datetime,
}


@dataclass
class FieldDiff:
    """Represents a difference in a field between SDK and API."""

    field_name: str
    diff_type: str  # "missing", "extra", "type_mismatch", "required_mismatch", "deprecated"
    sdk_value: Any = None
    api_value: Any = None
    message: str = ""


@dataclass
class ModelValidationResult:
    """Result of validating a single SDK model against API schema."""

    model_name: str
    sdk_model: str
    api_schema: str
    is_valid: bool = True
    differences: list[FieldDiff] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Complete validation report for all models."""

    results: list[ModelValidationResult] = field(default_factory=list)
    missing_in_sdk: list[str] = field(default_factory=list)  # API schemas without SDK models
    missing_in_api: list[str] = field(default_factory=list)  # SDK models without API schemas
    deprecated_fields: list[tuple[str, str]] = field(default_factory=list)  # (model, field)

    @property
    def has_errors(self) -> bool:
        return any(not r.is_valid for r in self.results) or bool(self.missing_in_sdk)

    @property
    def has_warnings(self) -> bool:
        return any(r.warnings for r in self.results) or bool(self.deprecated_fields)


def fetch_openapi_spec(url: str, timeout: float = 30.0) -> dict[str, Any]:
    """Fetch OpenAPI specification from a running Control Plane instance."""
    with httpx.Client(timeout=timeout) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def load_openapi_spec(file_path: Path) -> dict[str, Any]:
    """Load OpenAPI specification from a file."""
    with open(file_path) as f:
        return json.load(f)


def save_openapi_spec(spec: dict[str, Any], file_path: Path) -> None:
    """Save OpenAPI specification to a file."""
    with open(file_path, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"Saved OpenAPI spec to {file_path}")


def get_sdk_model(import_path: str) -> type[BaseModel] | None:
    """Import and return an SDK model class from its import path."""
    try:
        module_path, class_name = import_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        print(f"Warning: Could not import SDK model {import_path}: {e}")
        return None


def normalize_python_type(python_type: Any) -> str:
    """Normalize a Python type annotation to a comparable string representation."""
    origin = get_origin(python_type)

    if origin is None:
        # Simple type
        if python_type is type(None):
            return "null"
        if isinstance(python_type, type):
            if issubclass(python_type, Enum):
                return "string"  # Enums are strings in OpenAPI
            return python_type.__name__.lower()
        return str(python_type).lower()

    # Generic types
    args = get_args(python_type)
    if origin is list:
        if args:
            inner = normalize_python_type(args[0])
            return f"array[{inner}]"
        return "array"
    if origin is dict:
        return "object"
    if origin is type(None):
        return "null"

    # Union types (Optional, Union)
    type_name = getattr(origin, "__name__", str(origin))
    if type_name == "UnionType" or str(origin).startswith("typing.Union"):
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            return normalize_python_type(non_none_args[0])
        return f"union[{', '.join(normalize_python_type(a) for a in non_none_args)}]"

    return str(python_type).lower()


def openapi_type_to_string(schema: dict[str, Any], definitions: dict[str, Any] | None = None) -> str:
    """Convert an OpenAPI schema type to a comparable string representation."""
    # Handle $ref
    if "$ref" in schema:
        ref = schema["$ref"]
        ref_name = ref.split("/")[-1]
        return f"ref[{ref_name}]"

    # Handle anyOf/oneOf (nullable types)
    if "anyOf" in schema:
        types = []
        for sub in schema["anyOf"]:
            if sub.get("type") == "null":
                continue
            types.append(openapi_type_to_string(sub, definitions))
        if len(types) == 1:
            return types[0]
        return f"union[{', '.join(types)}]"

    if "oneOf" in schema:
        types = [openapi_type_to_string(sub, definitions) for sub in schema["oneOf"]]
        return f"union[{', '.join(types)}]"

    # Handle allOf (composition)
    if "allOf" in schema:
        types = [openapi_type_to_string(sub, definitions) for sub in schema["allOf"]]
        return f"allOf[{', '.join(types)}]"

    schema_type = schema.get("type")
    schema_format = schema.get("format")

    # Handle format
    if schema_format:
        if schema_format == "uuid":
            return "uuid"
        if schema_format in ("date-time", "date"):
            return "datetime"

    # Handle arrays
    if schema_type == "array":
        items = schema.get("items", {})
        inner = openapi_type_to_string(items, definitions)
        return f"array[{inner}]"

    # Handle objects with additionalProperties (dict-like)
    if schema_type == "object":
        if "additionalProperties" in schema:
            return "object"
        # Object with defined properties
        return "object"

    # Simple types
    if schema_type:
        return schema_type

    return "unknown"


def get_field_info_from_model(model: type[BaseModel]) -> dict[str, tuple[Any, FieldInfo]]:
    """Extract field information from a Pydantic model."""
    fields_info = {}
    for field_name, field_info in model.model_fields.items():
        annotation = model.__annotations__.get(field_name)
        fields_info[field_name] = (annotation, field_info)
    return fields_info


def is_field_optional(field_info: FieldInfo) -> bool:
    """Check if a Pydantic field is optional (has a default value)."""
    return field_info.default is not None or field_info.default_factory is not None


def compare_model_to_schema(
    model: type[BaseModel],
    schema: dict[str, Any],
    schema_name: str,
    definitions: dict[str, Any],
) -> ModelValidationResult:
    """Compare an SDK Pydantic model against an OpenAPI schema."""
    result = ModelValidationResult(
        model_name=schema_name,
        sdk_model=f"{model.__module__}.{model.__name__}",
        api_schema=schema_name,
    )

    sdk_fields = get_field_info_from_model(model)
    api_properties = schema.get("properties", {})
    api_required = set(schema.get("required", []))

    sdk_field_names = set(sdk_fields.keys())
    api_field_names = set(api_properties.keys())

    # Check for missing fields in SDK (present in API but not SDK)
    missing_in_sdk = api_field_names - sdk_field_names
    for field_name in missing_in_sdk:
        api_schema = api_properties[field_name]
        is_required = field_name in api_required
        result.differences.append(
            FieldDiff(
                field_name=field_name,
                diff_type="missing",
                api_value=openapi_type_to_string(api_schema, definitions),
                message=f"Field '{field_name}' exists in API but not in SDK (required={is_required})",
            )
        )
        result.is_valid = False

    # Check for extra fields in SDK (present in SDK but not API)
    extra_in_sdk = sdk_field_names - api_field_names
    for field_name in extra_in_sdk:
        annotation, field_info = sdk_fields[field_name]
        result.differences.append(
            FieldDiff(
                field_name=field_name,
                diff_type="extra",
                sdk_value=normalize_python_type(annotation),
                message=f"Field '{field_name}' exists in SDK but not in API",
            )
        )
        # Extra fields are warnings, not errors (SDK can have additional convenience fields)
        result.warnings.append(f"Extra SDK field: {field_name}")

    # Check for type mismatches on common fields
    common_fields = sdk_field_names & api_field_names
    for field_name in common_fields:
        annotation, field_info = sdk_fields[field_name]
        api_schema = api_properties[field_name]

        sdk_type = normalize_python_type(annotation)
        api_type = openapi_type_to_string(api_schema, definitions)

        # Check for deprecated fields
        if api_schema.get("deprecated", False):
            result.differences.append(
                FieldDiff(
                    field_name=field_name,
                    diff_type="deprecated",
                    message=f"Field '{field_name}' is deprecated in API",
                )
            )
            result.warnings.append(f"Deprecated field: {field_name}")

        # Type comparison (simplified - handles common cases)
        if not types_compatible(sdk_type, api_type):
            result.differences.append(
                FieldDiff(
                    field_name=field_name,
                    diff_type="type_mismatch",
                    sdk_value=sdk_type,
                    api_value=api_type,
                    message=f"Type mismatch for '{field_name}': SDK={sdk_type}, API={api_type}",
                )
            )
            result.is_valid = False

        # Required/optional comparison
        sdk_optional = is_field_optional(field_info)
        api_required_field = field_name in api_required

        # A field is a mismatch if API requires it but SDK makes it optional
        if api_required_field and sdk_optional:
            result.differences.append(
                FieldDiff(
                    field_name=field_name,
                    diff_type="required_mismatch",
                    sdk_value="optional",
                    api_value="required",
                    message=f"Field '{field_name}' is required in API but optional in SDK",
                )
            )
            result.warnings.append(f"Required mismatch: {field_name}")

    return result


def types_compatible(sdk_type: str, api_type: str) -> bool:
    """Check if SDK type is compatible with API type."""
    # Exact match
    if sdk_type == api_type:
        return True

    # Handle some common equivalences
    equivalences = [
        ({"str", "string"}, {"str", "string"}),
        ({"int", "integer"}, {"int", "integer"}),
        ({"float", "number"}, {"float", "number"}),
        ({"bool", "boolean"}, {"bool", "boolean"}),
        ({"dict", "object"}, {"dict", "object"}),
        ({"list", "array"}, {"list", "array"}),
    ]

    for sdk_set, api_set in equivalences:
        if sdk_type in sdk_set and api_type in api_set:
            return True

    # Handle array types
    if sdk_type.startswith("array[") and api_type.startswith("array["):
        sdk_inner = sdk_type[6:-1]
        api_inner = api_type[6:-1]
        return types_compatible(sdk_inner, api_inner)

    # Handle ref types (API uses refs, SDK has actual types)
    if api_type.startswith("ref["):
        # Just check if it's an object type
        return sdk_type in ("dict", "object") or not sdk_type.startswith(("str", "int", "bool", "float"))

    return False


def validate_all_models(spec: dict[str, Any]) -> ValidationReport:
    """Validate all SDK models against the OpenAPI specification."""
    report = ValidationReport()

    # Get all schema definitions
    components = spec.get("components", {})
    schemas = components.get("schemas", {})

    if not schemas:
        print("Warning: No schemas found in OpenAPI spec")
        return report

    # Validate each mapped model
    for schema_name, sdk_import_path in SDK_MODEL_MAPPING.items():
        if schema_name not in schemas:
            report.missing_in_api.append(schema_name)
            continue

        sdk_model = get_sdk_model(sdk_import_path)
        if sdk_model is None:
            print(f"Warning: Could not load SDK model for {schema_name}")
            continue

        schema = schemas[schema_name]
        result = compare_model_to_schema(sdk_model, schema, schema_name, schemas)
        report.results.append(result)

        # Track deprecated fields
        for diff in result.differences:
            if diff.diff_type == "deprecated":
                report.deprecated_fields.append((schema_name, diff.field_name))

    # Check for API schemas without SDK models
    all_sdk_schemas = set(SDK_MODEL_MAPPING.keys())
    all_api_schemas = set(schemas.keys())
    for schema_name in all_api_schemas - all_sdk_schemas:
        # Filter out internal/helper schemas
        if not schema_name.startswith("_") and not schema_name.endswith("Config"):
            report.missing_in_sdk.append(schema_name)

    return report


def print_report(report: ValidationReport, verbose: bool = False) -> None:
    """Print the validation report to stdout."""
    print("\n" + "=" * 60)
    print("SDK Model Validation Report")
    print("=" * 60)

    # Summary
    total = len(report.results)
    passed = sum(1 for r in report.results if r.is_valid)
    failed = total - passed

    print(f"\nModels Validated: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if report.missing_in_sdk:
        print(f"\nAPI schemas without SDK models ({len(report.missing_in_sdk)}):")
        for name in sorted(report.missing_in_sdk):
            print(f"  - {name}")

    if report.missing_in_api:
        print(f"\nSDK models without API schemas ({len(report.missing_in_api)}):")
        for name in sorted(report.missing_in_api):
            print(f"  - {name}")

    if report.deprecated_fields:
        print(f"\nDeprecated fields in use ({len(report.deprecated_fields)}):")
        for model, field in report.deprecated_fields:
            print(f"  - {model}.{field}")

    # Detailed results
    for result in report.results:
        if not result.is_valid or result.warnings or verbose:
            print(f"\n{'='*40}")
            status = "PASS" if result.is_valid else "FAIL"
            print(f"[{status}] {result.model_name}")
            print(f"  SDK: {result.sdk_model}")

            if result.differences:
                print("  Differences:")
                for diff in result.differences:
                    marker = "ERROR" if diff.diff_type in ("missing", "type_mismatch") else "WARN"
                    print(f"    [{marker}] {diff.message}")

            if result.warnings and verbose:
                print("  Warnings:")
                for warning in result.warnings:
                    print(f"    - {warning}")

    print("\n" + "=" * 60)
    if report.has_errors:
        print("VALIDATION FAILED - SDK models have drifted from API")
    elif report.has_warnings:
        print("VALIDATION PASSED with warnings")
    else:
        print("VALIDATION PASSED")
    print("=" * 60)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate SDK Pydantic models against Control Plane OpenAPI specification"
    )
    parser.add_argument(
        "--url",
        help="URL to fetch OpenAPI spec from (e.g., http://localhost:8000/api/v1/openapi.json)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Path to OpenAPI spec file",
    )
    parser.add_argument(
        "--save",
        type=Path,
        help="Save fetched OpenAPI spec to file",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any drift (including warnings)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output including passing models",
    )

    args = parser.parse_args()

    if not args.url and not args.file:
        parser.error("Either --url or --file must be specified")

    # Load OpenAPI spec
    try:
        if args.url:
            print(f"Fetching OpenAPI spec from {args.url}...")
            spec = fetch_openapi_spec(args.url)
            if args.save:
                save_openapi_spec(spec, args.save)
        else:
            print(f"Loading OpenAPI spec from {args.file}...")
            spec = load_openapi_spec(args.file)
    except Exception as e:
        print(f"Error loading OpenAPI spec: {e}")
        return 1

    # Validate models
    print("Validating SDK models...")
    report = validate_all_models(spec)

    # Print report
    print_report(report, verbose=args.verbose)

    # Determine exit code
    if report.has_errors:
        return 1
    if args.strict and report.has_warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
