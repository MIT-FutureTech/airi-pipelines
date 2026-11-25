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

Then download the latest data bundle:

```bash
npm run download-data
```

Or build it yourself, as in [Updating the data](#updating-the-data).

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

## Updating the data

The latest data bundle is kept in the `org-mitigations-reviewer-data` R2
bucket, so that deploys can use it without it being committed.

To update it, build the bundle from an export. From the repository root, run
this:

```bash
uv run --package org-mitigations python -m org_mitigations.bundle \
  --export-dir /path/to/exports/ \
  --output-path pipelines/org-mitigations/reviewer/public/data/bundle.json
```

Then, from this folder, upload it:

```bash
npm run upload-data
```

The app shows the new data after its next deploy. To deploy without a code
change, run the CI workflow on main:

```bash
gh workflow run reviewer-ci.yml --ref main
```

## Deployment

The app deploys to Cloudflare as a single Worker, which serves the built
frontend and the data bundle, and handles `/api/*` itself. Who can open it is
set in `hosting/access/access.yaml` at the repository root.

The first time, create the bucket, upload the data as above, and give the
Worker its Airtable token:

```bash
npx wrangler r2 bucket create org-mitigations-reviewer-data
npx wrangler secret put AIRTABLE_PAT
```

After that, the CI workflow deploys the app whenever a change to it reaches
main.

To try a branch before merging it, upload a preview version from it, with an
optional alias for its URL:

```bash
gh workflow run reviewer-preview.yml --ref my-branch -f alias=my-alias
```

The run's summary lists the preview URLs. Previews save judgements to the same
Airtable table as the deployed app.
