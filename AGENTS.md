# Coding Guidelines

## Comments

- No redundant comments that restate the code
- No historical comments describing past changes
- Avoid section-separator comments

## Design

Remember the Zen of Python:

- Explicit is better than implicit.
- In the face of ambiguity, refuse the temptation to guess.
- Example: make parameters required unless there's a very good reason to make them optional.

## Error Handling

Minimize try/except. They mask bugs. Add them reactively, not proactively. When necessary, scope narrowly and log.

## Assumptions

Be strict. Prefer `mydict["key"]` over `mydict.get("key")` unless the key is genuinely optional.

## Types

Use dedicated types over generic dicts or objects.

## Linting

Don't immediately silence linter errors. Understand the rule first and fix the root cause. Use automatic fixes when available. Tests must pass linting too.

## Imports

All imports at the top of the file. The linter disallows mid-file imports.

No barrel-export from `index.ts` or `__init__.py`. Toolbox is an exception: subpackages should re-export commonly-used public members.
