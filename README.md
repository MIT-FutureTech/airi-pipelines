# AIRI Pipelines

## Projects

### [Toolbox Library](/toolbox-lib/README.md)

Toolbox is a Python library containing functionality which is shared across
multiple pipelines.

### [Risk Repository Pipeline](/pipelines/risk-repository/README.md)

This pipeline collects risks from AI and classifies them according to a
taxonomy. It also includes functionality for evaluating the pipeline against
ground-truth, as well as web apps for reviewing the pipeline's output.

## Developer Notes

### Setup

#### Python Dependencies

For Python dependencies, make sure you have
[`uv` installed](https://docs.astral.sh/uv/getting-started/installation/). Then
run this command from the root of the repository:

```bash
uv sync --all-packages
```

#### `.env` File

Make a copy of the example file:

```bash
cp -n .env.example .env
```

Then fill in the required environment variables in the new `.env` file.

#### Git Hooks

Run this command once to configure git hooks to automatically run checks before
committing and pushing changes.

```bash
git config core.hooksPath hooks/
```

### Workflow

To simplify collaboration, committing and pushing to main are not allowed.
Instead, developers must work on branches and merge their changes into the main
branch using pull request.

If you are new to branches and pull requests,
[here is a good tutorial](https://github.blog/developer-skills/github/beginners-guide-to-github-creating-a-pull-request/).
Your friendly neighborhood AI assistant will also happily walk you through the
process.

### Automated Checks

There are several tools for helping to promote code correctness and consistency.
The pre-commit hook runs some of these automatically during each commit.

#### Python

Run these commands from the root directory of the repository.

```bash
# Automatically reformat all files
uv run ruff format

# Run linter, fixing issues that can be fixed automatically
uv run ruff check --fix

# Run type checker
uv run basedpyright

# Run unit tests
uv run pytest

# Run all the checks together
uv run ruff format && uv run ruff check --fix && uv run basedpyright && uv run pytest
```

#### Web apps

See each app's README for details on its particular checks.

### Conventions

Here are general guidelines for new projects.

#### Python

- `uv` for dependency management, using a single workspace for all projects
- `ruff` for formatting and linting
- `basedpyright` for type checking
- `pytest` for tests

#### Web apps

- TypeScript in strict mode
- `npm` for package managemnt and scripts
- `biome` for formatting and linting
- `vitest` for tests
- [Cloudflare for hosting](https://docs.google.com/document/d/1jGKhionTICH3eD3pEIe0X0_nZ2X9W6k4IpTNg5d4Xlg)
