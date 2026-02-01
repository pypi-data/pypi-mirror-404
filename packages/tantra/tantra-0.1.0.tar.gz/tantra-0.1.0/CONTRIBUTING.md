# Contributing to Tantra

Thanks for your interest in contributing to Tantra. This guide covers how to set up a development environment, run tests, and submit changes.

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/tantra-run/tantra-py.git
cd tantra
```

2. Create a virtual environment and install in dev mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[all]"
```

3. Install pre-commit hooks:

```bash
pre-commit install
```

## Running Tests

```bash
pytest
```

Tests run with coverage enabled by default. The minimum coverage threshold is 70%.

To run a specific test file:

```bash
pytest tests/test_agent.py
```

## Code Style

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check .
ruff format .
```

Pre-commit hooks run these automatically on each commit. The configuration is in `pyproject.toml`:

- Line length: 100
- Target: Python 3.11+
- Rules: E, F, I, N, W, UP

## Submitting Changes

1. Fork the repository and create a branch from `main`.
2. Make your changes. Add tests for new functionality.
3. Ensure all tests pass and linting is clean.
4. Submit a pull request against `main`.

Keep pull requests focused on a single change. Write a clear description of what the PR does and why.

## Project Structure

```
tantra/              # Package source
tests/              # Test suite
examples/           # Example scripts
public-docs/        # Documentation (mkdocs)
```

See `CLAUDE.md` for detailed architecture documentation (available in the development environment).

## Reporting Issues

Use [GitHub Issues](https://github.com/tantra-run/tantra-py/issues) to report bugs or request features. Include:

- Python version
- Tantra version (`tantra.__version__`)
- Minimal reproduction steps
- Expected vs actual behavior
