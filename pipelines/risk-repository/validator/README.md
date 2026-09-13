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

##### Production

```bash
npm run deploy
```

##### Preview

You can upload a new version without altering the production deployment. This
gives you a way to share preliminary changes with a select group. From this
folder run,

```bash
npx wrangler versions upload
```

It'll create a unique URL for this version and print it for you. The URL will
have the form
`https://1234abcd-risk-repository-validator.mit-airi.workers.dev/`. You can
send that URL to others to share your changes.

You can also give your preview an alias like this:

```bash
npx wrangler versions upload --preview-alias staging
```

Now, in addition to the unique URL, you'll get a more friendly one:
`https://staging-risk-repository-validator.mit-airi.workers.dev/`.

If you later push more changes, you'll get a new unique URL (say like
`https://5678efab-risk-repository...`). The original unique URL won't get your
changes: it'll keep running the code you first pushed to it. But the alias URL
will change (assuming you reuse the same `--preview-alias`).

|     URL    | Code |
| ---------- | ---- |
| `1234abcd` | old  |
| `5678efab` | new  |
| `staging`  | new  |

So share the alias URL (`staging-risk-repository...`) if you want them to see
future changes you push. Share the unique URL (`1234abcd-risk-repository`) if
you want the version they see to remain fixed, even after you push more changes.
In git terms, sharing the unique URL is like sharing a commit (a fixed
snapshot), while sharing the alias URL is like sharing a branch (a reference
that can update).

###### Deploying from GitHub

If you don't want to deploy from the command line, you can deploy from GitHub
instead.

1. Push the branch with your changes.
2. Head to
<https://github.com/MIT-FutureTech/airi-pipelines/actions/workflows/validator-preview.yml>.
3. Click the button that says "Run workflow".
4. Select your branch.
5. Optionally, give it a preview alias.
6. Click the green "Run workflow" button.
7. After a few seconds, the run will appear. You can click on it to watch its
   progress. It'll output the unique URL as well as the alias one (if you gave
   it an alias).
8. You can also
   [view versions in Cloudflare](https://dash.cloudflare.com/dee3a047356fdb8bb892c9cf407d4554/workers/services/view/risk-repository-validator/production/deployments).
   Click on any version's ID to open that version of the app.

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
