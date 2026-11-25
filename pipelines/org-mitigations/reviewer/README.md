# Organization Mitigations Reviewer

A web app where people judge whether a company meets the bar for a kind of
mitigation, using the evidence the pipeline found. It saves their judgements to
Airtable.

## Architecture

- **Frontend**: Vite + React 19 + Mantine, in `src/`
- **Backend**: a Cloudflare Worker, in `api/`
- **Shared**: request and response types the two have in common, in `shared/`
- **Data**: a JSON bundle of the mitigations, their quotes and the codes they're
  tagged with, served with the frontend. Judgements are read and saved through
  the Worker.

## Local development

From this folder, run these steps once to set up your development environment.

```bash
npm install
cp .env.example .env
# fill in .env
```

Then build the data bundle. From the repository root, run this:

```bash
uv run --package org-mitigations python -m org_mitigations.bundle \
  --export-dir /path/to/exports/ \
  --output-path pipelines/org-mitigations/reviewer/public/data/bundle.json
```

Then anytime you want to start the app, run this:

```bash
npm run dev
```

### Checks

The `check` script runs the formatter, linter and type checker.

```bash
npm run check
```

### Tests

```bash
npm run test        # run once
npm run test:watch  # re-run on change
```

## Deployment

The app deploys to Cloudflare as a single Worker, which serves the built
frontend and the data bundle, and handles `/api/*` itself. Who can open it is
set in `hosting/access/access.yaml` at the repository root.

The first time, give the Worker its Airtable token:

```bash
npx wrangler secret put AIRTABLE_PAT
```

Then build the data bundle as above, and deploy:

```bash
npm run deploy
```
