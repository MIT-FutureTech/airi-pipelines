# Pipeline Explorer

This is a web app which provides an interactive overview of the AI Risk
Initiative's software pipelines.

## Development Instructions

### Dependencies

First, make sure you have
[`npm` installed](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm).

Then install the app's dependencies:

```bash
npm install
```

### Running the App

```bash
npm run dev
```

Then go to <http://localhost:3000>

### Automatic Formatting and Linting

Run these commands from the `pipeline-explorer/` directory.

```bash
# Automatically reformat all files
npm run format

# Run linter and apply fixes for issues
# that can be fixed automatically
npm run lint

# Run type checker
npm run typecheck

# Run all the checks together
npm run check
```

It is recommended to [configure your git hooks](/README.md#git-hooks) to run
these checks automatically before each commit.
