# AIRI Pipelines

## Projects

### [Pipeline Explorer](/pipeline-explorer/README.md)

The pipeline explorer is an interactive web app for understanding the AI Risk
Initiative's software pipelines.

### [Toolbox Library](/toolbox-lib/README.md)

Toolbox is a Python library containing functionality which is shared across
multiple pipelines.

## Developer Notes

### Workflow

To simplify collaboration, committing and pushing to main are not allowed.
Instead, developers must work on branches and merge their changes into the main
branch using pull request.

If you are new to branches and pull requests,
[here is a good tutorial](https://github.blog/developer-skills/github/beginners-guide-to-github-creating-a-pull-request/).
Your friendly neighborhood AI assistant will also happily walk you through the
process.

### Git Hooks

Run this command once to configure git hooks to automatically run checks before
committing and pushing changes.

```bash
git config core.hooksPath hooks/
```
