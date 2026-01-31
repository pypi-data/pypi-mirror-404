# CLAUDE.md

This is the Python SDK for the Aither platform (https://aither.computer).

## Project Structure

```
aither-sdk/
├── src/aither/          # Main package
│   ├── __init__.py      # Public API exports
│   └── client.py        # Client implementation
├── pyproject.toml       # Package configuration
└── README.md            # User documentation
```

## Development Commands

```bash
# Install in development mode
uv pip install -e .

# Run tests
uv run pytest

# Build package
uv build

# Publish to PyPI
uv publish
```

## Architecture

The SDK provides a simple interface for logging ML model predictions to the Aither platform.

**Core Components:**
- `AitherClient`: Main client class handling HTTP communication
- Module-level functions (`init`, `log_prediction`): Convenience API using a global client instance

**Design Principles:**
- Minimal dependencies (only `httpx` for HTTP)
- Synchronous API for simplicity
- Thread-safe global client
- Configurable via environment variables or explicit init

## Backend Integration

The backend lives in `../aither`. Key endpoints:
- `POST /v1/predictions` - Log predictions
- `GET /health` - Health check

Authentication uses API keys via `X-API-Key` header.

## Environment Variables

- `AITHER_API_KEY`: API key for authentication
- `AITHER_ENDPOINT`: Backend URL (default: https://aither.computer)
