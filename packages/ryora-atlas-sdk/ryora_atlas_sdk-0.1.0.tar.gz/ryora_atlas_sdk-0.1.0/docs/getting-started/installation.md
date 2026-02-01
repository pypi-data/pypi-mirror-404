# Installation

## Requirements

- Python 3.13 or higher

## Basic Installation

Install the Atlas SDK from PyPI:

```bash
pip install ryora-atlas-sdk
```

Or using uv:

```bash
uv add ryora-atlas-sdk
```

## Optional Dependencies

### OpenTelemetry Integration

For distributed tracing support, install with the `otel` extra:

```bash
pip install ryora-atlas-sdk[otel]
```

This adds the `opentelemetry-api` package for automatic span creation during HTTP requests.

## Development Installation

For contributing to the SDK:

```bash
# Clone the repository
git clone https://github.com/ryora/atlas.git
cd atlas/atlas-sdk

# Install with all development dependencies
uv sync --extra dev --extra test --extra docs

# Or with pip
pip install -e ".[dev,test,docs]"
```

## Verifying Installation

```python
import atlas_sdk
print(atlas_sdk.__version__)
```

## Next Steps

- [Quick Start](quickstart.md) - Get up and running in minutes
