# Risk Repository Validator

This is a web app for humans to validate the Risk Repository pipeline. Reviewers
independently make abstract-screening decisions (include / exclude / uncertain)
on a fixed list of documents pulled from Airtable; their decisions are written
back to Airtable for comparison against the LLM pipeline.

The plan is to add downstream stages of the pipeline (full-text screening, risk
extraction, risk classification) to the app in the future.

## Architecture

- **Frontend**: Vite + React 19 + Mantine
- **Backend**: Cloudflare Worker in `api/`
- **Storage**: Airtable

## Local development

From this folder, run these steps once to set up your development environment.

```bash
# Do once
npm install
cp .env.example .env
# fill in .env
```

Then anytime you want to start the app, run this:

```bash
npm run dev
```

### Deployment

This app deploys to Cloudflare as a single Worker. The Worker serves the built
frontend from `dist/` and handles `/api/*` itself.

#### One-time Setup

```bash
npx wrangler login
```

Be sure that the following Developer Platform permissions are enabled:

- Workers Write
- Workers Scripts Write

#### Deploy

```bash
npm run deploy
```

### Checks

The `check` script runs the formatter, linter and type checker.

```bash
npm run check
```

### Tests

Here's how to run the tests.

```bash
npm run test        # run once
npm run test:watch  # re-run on change
```
