# Risk Repository Validator

This is a web app for humans to validate the Risk Repository pipeline. As of
September 2026, it supports the abstract screening and risk classification
stages. In the future, it may eventually grow to support full-text screening and
risk extraction stages.

## Architecture

- **Frontend**: Vite + React 19 + Mantine
- **Backend**: Cloudflare Worker in `api/`
- **Storage**: Airtable

## Local development

From this folder, run these steps once to set up your development environment.

```bash
npm install
cp .env.example .env
# fill in .env
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

Here's how to run the tests.

```bash
npm run test        # run once
npm run test:watch  # re-run on change
```

## Deployment

This app deploys to Cloudflare as a single Worker. The Worker serves the built
frontend from `dist/` and handles `/api/*` itself.

### Production

There's a GitHub Action which deploys changes automatically once they're merged
to main.

### Preview

You can upload a new version without altering the production deployment. This
gives you a way to share preliminary changes with a select group.
[See here](https://docs.google.com/document/d/1jGKhionTICH3eD3pEIe0X0_nZ2X9W6k4IpTNg5d4Xlg)
for more information.

Here are the instructions for deploying a branch using GitHub Actions.

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

