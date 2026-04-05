---
paths:
  - "**/*.py"
---

# Python Guidelines

This repository uses Python 3.12 or later. Take advantage of newer features. Compatibility with older Python versions is not required.

## Invocation

Prefer `uv` for all Python and package commands over the system Python and `pip`.

## Imports

No `from __future__ import annotations`.

## Data Modeling

Prefer Pydantic over dicts, TypedDicts, and dataclasses.

## Concurrency

Use asyncio.

## Test Organization

Mirror source layout: `src/mypackage/mymodule.py` maps to `tests/mypackage/test_mymodule.py`. Group related test cases into a test class.

## Automated Checks

Run from the repository root:

```bash
uv run ruff format && uv run ruff check --fix && uv run basedpyright && uv run pytest -x
```
