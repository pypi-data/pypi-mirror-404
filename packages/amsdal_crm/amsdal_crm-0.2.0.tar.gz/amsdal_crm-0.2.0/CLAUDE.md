# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

amsdal-crm is a CRM plugin for the AMSDAL Framework that provides CRM models similar to Salesforce ones. It supports both synchronous and asynchronous modes, with primary focus on async operations.

## Development Commands

### Environment Setup
```bash
# Install dependencies using hatch/uv
pip install --upgrade uv hatch==1.14.2
hatch env create
hatch run sync
```

### Testing
```bash
# Run all tests with coverage
hatch run cov

# Run specific test file
hatch run test tests/unit/models/test_activity.py

# Run tests with pytest directly (after env setup)
pytest tests/
pytest tests/unit/models/  # Run unit tests for models

```

### Code Quality
```bash
# Run all checks (style + typing)
hatch run all

# Style checks only
hatch run style

# Format code (fix style issues)
hatch run fmt

# Type checking
hatch run typing
```

### Dependency Management
```bash
# Sync dependencies
hatch run sync

# Update lock file
hatch run lock

# Upgrade all dependencies
hatch run lock-upgrade
```

### AMSDAL CLI Commands
```bash
# Generate new model
amsdal generate model ModelName --format py

# Generate property for model
amsdal generate property --model ModelName property_name

# Generate transaction
amsdal generate transaction TransactionName

# Generate hook
amsdal generate hook --model ModelName on_create
```

## Architecture

## Code Style

- Python 3.11+ required
- Uses Ruff for linting and formatting with 120-char line length
- Single quotes enforced (`quote-style = "single"`)
- Import ordering: force-single-line with order-by-type
- Type checking via mypy with strict settings (disallow_any_generics, check_untyped_defs)
- Excludes migrations directory from linting

## Testing

- Uses pytest with pytest-asyncio for async tests
- Test fixtures in `tests/conftest.py` provide mocked OpenAI clients
- Coverage tracking with coverage.py

## CI/CD

The project uses self-hosted runners with two jobs:
1. **license-check**: Validates third-party licenses using `license_check.py`
2. **test-lint**: Runs on Python 3.11 and 3.12, executes `hatch run all` (style+typing) and `hatch run cov`

## Key Patterns

1. **Async-First**: Most components prioritize async methods; sync methods often raise NotImplementedError
2. **Abstract Base Classes**: Heavy use of ABCs to define interfaces for models, retrievers, ingesters, and agents
3. **Configuration via Pydantic**: Settings loaded from environment with type validation
4. **AMSDAL Integration**: Uses AMSDAL's model system, manager, and connection framework
5. **Chunking Strategy**: Text split into chunks with metadata preservation for better embedding quality
6. **Tag-Based Filtering**: Embeddings tagged for fine-grained retrieval control
