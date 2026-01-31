# Development

## Setup

Install dependencies using uv:

```bash
# Install the package with dev dependencies
uv sync --dev
```

## Running Tests

```bash
uv run pytest
```

With coverage:

```bash
uv run pytest --cov=. --cov-report=html
```

## Linting

```bash
# Check code
uv run ruff check .

# Format code
uv run ruff format .
```

## Type Checking

```bash
uv run mypy .
```

## Making Changes

1. Make your changes
2. Run linting: `uv run ruff check . && uv run ruff format .`
3. Run type checking: `uv run mypy .`
4. Run tests: `uv run pytest`
5. Test the demo: `uv run python demo.py`

## Building

```bash
uv build
```

## Versioning
To update to an exact version, provide it as a positional argument:
```bash
uv version 1.0.0
```

To increase the version of your package semantics, use the --bump option:
```bash
uv version --bump dev
```

## Publishing

```bash
uv publish
```