# Contributing to Argmax

Thank you for helping improve Argmax. Changes should keep research assumptions explicit,
preserve next-bar execution semantics, and include tests for behavioral changes.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Required checks

Run the same checks used by GitHub Actions before opening a pull request:

```bash
ruff check .
ruff format --check .
node --check public/landing.js
node --check public/app.js
pytest --cov=argmax --cov-report=term-missing
```

## Pull requests

- Keep changes focused and explain the research behavior they affect.
- Add or update tests for accounting, signal timing, metrics, API, or CLI changes.
- Include desktop and mobile screenshots for visible frontend changes.
- Do not commit local market-data caches, virtual environments, coverage output, or secrets.

By contributing, you agree that your work will be licensed under the MIT License.
