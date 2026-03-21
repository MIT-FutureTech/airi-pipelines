# Pipeline Visualization Tool — Design

## Goals

Provide an interactive internal tool for exploring the AIRI pipeline architecture. Serve as an onboarding aid, a discussion tool for planning changes, and a living reference that stays up to date.

See `PIPELINE_MAP.md` for the current inventory of pipelines and components. This design doc is intentionally decoupled from specific pipeline content — it describes the structure, not the data.

## Tech Stack

- **Framework**: Next.js + React
- **Diagrams**: React Flow (interactive node-graph library with zoom, pan, click)
- **Styling**: Tailwind CSS
- **Node details**: MDX (markdown with optional React components)
- **Hosting**: Vercel (already used for other AIRI projects)
- **Auth**: Password protection via Next.js middleware (`SITE_PASSWORD` env var, same pattern as airi-navigator)

No backend, database, or external API calls at runtime. All content is static and baked in at build time.

## File Organization

```
src/
  components/
    PipelineGraph.tsx       — shared React Flow renderer
    NodeDetailPanel.tsx     — slide-out panel that renders MDX
    Layout.tsx              — page shell (header, canvas area, panel)
  types/
    pipeline.ts             — TypeScript types for pipeline/node/edge data
  pipelines/
    index.ts                — registry that collects all pipelines
    <pipeline-group>/
      pipeline.ts           — exports: nodes[], edges[], metadata (name, description)
      <node-name>.mdx       — detail content for each node
      ...
    ...
  app/
    page.tsx                — main (and only) page
    layout.tsx              — Next.js root layout
```

### Pipeline data (`pipeline.ts`)

Each pipeline group exports a typed object:

```ts
export const pipeline: PipelineDefinition = {
  id: "grey-literature",
  name: "Grey Literature Pipeline",
  description: "Discovers, screens, and classifies corporate documents.",
  nodes: [
    { id: "greylitsearcher", label: "greylitsearcher", type: "repo", position: { x: 0, y: 0 } },
    { id: "airtable-greylit", label: "Airtable: Grey Literature", type: "datastore", position: { x: 0, y: 200 } },
    // ...
  ],
  edges: [
    { source: "greylitsearcher", target: "airtable-greylit" },
    // ...
  ],
};
```

Node types (e.g., `repo`, `datastore`, `external-service`, `manual-step`, `proposed`) determine visual styling (color, shape, icon). Positions are hand-tuned per pipeline.

### Node details (`<node-name>.mdx`)

Freeform MDX. Each file describes one node in whatever structure makes sense for that component. Example:

```mdx
# greylitsearcher

Streamlit web app that searches for grey literature via Google Custom Search API.

## Links

- [GitHub repo](https://github.com/MIT-FutureTech/greylitsearcher)

## Tech

Python, Streamlit, Google Custom Search API

## Inputs

- User-provided website domains and search queries (via web UI)

## Outputs

- Airtable Base 1, `raw_results` table (title, link, snippet, source_domain, priority, status)

## How it runs

Manual — user triggers searches through the Streamlit UI (password-protected).
```

There is no enforced schema for MDX files — authors can use whatever sections are appropriate for the node. Consistency comes from convention, not code.

### Pipeline registry (`index.ts`)

Collects all pipeline definitions into a single array so the main page can render them:

```ts
import { pipeline as greyLiterature } from "./grey-literature/pipeline";
import { pipeline as orgReview } from "./org-review/pipeline";
// ...

export const allPipelines = [greyLiterature, orgReview, /* ... */];
```

## UI

### Single view: all pipelines

The app has one page. It shows all pipeline groups side by side on a single React Flow canvas. Each pipeline group is a cluster of nodes. The user can zoom and pan freely across the full map.

Node styling communicates type at a glance:

| Node type | Visual treatment |
|-----------|-----------------|
| `repo` | Solid border, colored by pipeline group |
| `datastore` | Cylinder/database icon shape |
| `external-service` | Dashed border |
| `manual-step` | Dotted border, muted color |
| `proposed` | Ghost/faded styling |

Edges are arrows showing data flow direction.

### Slide-out detail panel

Clicking a node opens a slide-out panel on the right side of the screen. The panel renders the node's MDX content. Clicking outside the panel or pressing Escape closes it.

If a node has no MDX file (e.g., a simple Airtable base node), the panel shows a minimal auto-generated summary from the node's data fields (label, type).

### Header

Minimal top bar with the tool name and a brief description. No navigation needed since there's only one view.

## Keeping it up to date

Adding or modifying pipeline content requires no framework knowledge:

- **Add a node**: add an entry to the pipeline's `pipeline.ts` and create an `.mdx` file.
- **Add a pipeline**: create a new directory under `pipelines/`, add it to the registry.
- **Edit node details**: edit the `.mdx` file.
- **Rearrange layout**: adjust `position` values in `pipeline.ts`.

## Possible Future Work

- **Cross-cut view**: A horizontal view organized by concern (e.g., "all classifiers," "all Airtable bases," "all LLM usage") to spot duplication and unification opportunities.
- **Component catalog**: A flat searchable/filterable list of all components with status badges.
- **Filtering**: Filter nodes by status, tech stack, or external service.
- **Live data**: Pull metadata from GitHub (last commit, open PRs) or Airtable (record counts) to surface freshness info.
