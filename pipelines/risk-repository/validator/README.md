# Risk Repository Validator

This is a web app for humans to validate the Risk Repository pipeline. Reviewers
independently make abstract-screening decisions (include / exclude / uncertain)
on a fixed list of documents pulled from Airtable; their decisions are written
back to Airtable for comparison against the LLM pipeline.

The plan is to add downstream stages of the pipeline (full-text screening, risk
extraction, risk classification) to the app in the future.

## Architecture

- **Frontend**: Vite + React 19 + Mantine
- **Backend**: Vercel serverless functions in `api/`
- **Storage**: Airtable

## Local development

Then from this folder:

```bash
npm install
cp .env.example .env
# fill in .env

npm run dev:vercel  # You may be asked to log into Vercel
```

For UI-only work without setting up Airtable credentials, set
`VITE_API_PROXY_TARGET` in `.env` to a deployed Vercel URL and run
`npm run dev`. Vite will serve the frontend locally and forward `/api/*` to the
deployed backend.

### Deployment

This app deploys to Vercel as a static site plus serverless functions.

#### One-time Setup

Install the [Vercel CLI](https://vercel.com/docs/cli):

```bash
npm install -g vercel
vercel login
vercel link
```

#### Deploy

Deploy to preview:

```bash
vercel deploy --target preview
```

Deploy to production:

```bash
vercel deploy --target production
```

### Checks

The `check` script runs the formatter, linter and type checker.

```bash
npm run check
```

- link to PDF
