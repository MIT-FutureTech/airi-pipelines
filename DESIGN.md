# Pipeline Visualization Tool — Design

## Goals

Provide an interactive internal tool for exploring the AIRI pipeline architecture. Serve as an onboarding aid, a discussion tool for planning changes, and a living reference that stays up to date.

See `PIPELINE_MAP.md` for the current inventory of pipelines and components. This design doc is intentionally decoupled from specific pipeline content — it describes the structure, not the data.

## Tech Stack

- **Framework**: Next.js + React
- **Diagrams**: React Flow (interactive node-graph library with zoom, pan, click)
- **Graph layout**: dagre (automatic directed-graph layout — no manual coordinates)
- **Styling**: Tailwind CSS
- **Node details**: MDX (markdown with optional React components)
- **Hosting**: Vercel (already used for other AIRI projects)
- **Auth**: Password protection via Next.js middleware (`SITE_PASSWORD` env var, same pattern as airi-navigator)

No backend, database, or external API calls at runtime. All content is static and baked in at build time.

## Data Model

Nodes represent **functions in the data flow**, not repos. A single repo may contribute multiple nodes (e.g., `airi-orgrev-orglist` has separate nodes for company scraping, risk classification, and mitigation classification).

### Node types

| Node type | Meaning | Visual treatment |
|-----------|---------|-----------------|
| `processor` | Transforms or enriches data | Solid blue border |
| `datastore` | Stores data (Airtable bases, CSV outputs) | Amber border, rounded |
| `external-service` | External data source | Dashed gray border |
| `manual-step` | Human-performed action | Dotted gray border, muted |
| `proposed` | Not yet built or prototype | Faded/ghost styling |

### Owned vs shared nodes

Nodes are either **owned** by a single pipeline or **shared** across pipelines:

- **Owned nodes** are defined in a pipeline's `pipeline.ts` and displayed inside that pipeline's group box. This includes processors, pipeline-specific datastores, and external services used by only one pipeline.
- **Shared nodes** are defined in `pipelines/shared/nodes.ts` and imported by each pipeline that references them. They are displayed outside any group box, positioned by dagre between the pipelines that use them.

The organizing principle: **a node lives where it's owned; sharing is explicit.** If a datastore is used by only one pipeline, it stays in that pipeline's directory. When a second pipeline needs it, it moves to `shared/`.

Each enrichment stage of a datastore is its own node (no cycles in the graph).

## File Organization

```
src/
  lib/
    layout.ts               — dagre layout, graph building, node lookup, URL sync
  components/
    PipelineGraph.tsx        — React Flow canvas (state, handlers, rendering)
    PipelineNode.tsx         — custom node component with type-based styling
    PipelineGroupNode.tsx    — group box component (pipeline label + border)
    NodeDetailPanel.tsx      — slide-out panel that renders MDX
    NodeLink.tsx             — cross-reference component for use in MDX
    NodeSelectionContext.tsx  — React context for node selection
    ClientShell.tsx          — client wrapper (header + dynamic import of PipelineGraph)
  types/
    pipeline.ts              — TypeScript types for node/edge/pipeline data
  pipelines/
    shared/
      nodes.ts               — shared node definitions (datastores used by multiple pipelines)
      <node-name>.mdx         — detail content for shared nodes
    <pipeline-group>/
      pipeline.ts             — exports: nodes[], shared[], edges[], metadata
      <node-name>.mdx          — detail content for each owned node
      ...
    index.ts                  — registry: collects all pipelines, deduplicates shared nodes
    node-content.ts           — maps node IDs to their MDX components
  app/
    page.tsx                  — main (and only) page
    layout.tsx                — Next.js root layout
mdx-components.tsx            — registers custom MDX components (NodeLink)
```

### Pipeline data (`pipeline.ts`)

Each pipeline group exports a typed object. Nodes define the pipeline's processors and any pipeline-specific datastores. Shared nodes are imported from `shared/nodes.ts`. Edges can reference both owned and shared node IDs.

```ts
import { airtableCompanies } from "../shared/nodes";

export const pipeline: PipelineDefinition = {
  id: "actors",
  name: "Actors",
  description: "Classifies organizations by their AI ecosystem role.",
  nodes: [
    { id: "actors-classifier", label: "ai-actor-classifier", type: "processor" },
    { id: "actors-output", label: "Airtable: Companies (enriched)", type: "datastore" },
  ],
  shared: [airtableCompanies],
  edges: [
    { source: "airtable-companies", target: "actors-classifier" },
    { source: "actors-classifier", target: "actors-output" },
  ],
};
```

No position coordinates — dagre computes the layout automatically from the graph structure.

### Node details (`<node-name>.mdx`)

Freeform MDX. Each file describes one node in whatever structure makes sense. Consistency comes from convention, not code. Cross-references use the `<NodeLink>` component:

```mdx
See also <NodeLink id="screening-orchestrator">the screening orchestrator</NodeLink>.
```

Clicking a NodeLink opens that node's detail panel. The link also works as a URL (`?node=<id>`) for sharing.

### Pipeline registry (`index.ts`)

Collects all pipeline definitions and deduplicates shared nodes:

```ts
import { pipeline as documentProcessing } from "./document-processing/pipeline";
import { pipeline as actors } from "./actors/pipeline";

export const allPipelines = [documentProcessing, actors];
export const allSharedNodes = /* deduplicated from allPipelines[].shared */;
```

## UI

### Single view: all pipelines

The app has one page. It shows all pipelines on a single React Flow canvas. dagre lays out the full graph — pipeline group boxes are computed from each pipeline's owned-node positions, and shared nodes float between the pipelines that reference them.

The user can zoom and pan freely across the full map.

### Deep-linking

The URL query parameter `?node=<id>` selects a node and opens its detail panel. This enables:
- Shareable links to specific nodes
- Cross-references between MDX files via `<NodeLink>`

### Slide-out detail panel

Clicking a node opens a slide-out panel on the right side of the screen. The panel renders the node's MDX content. Clicking outside the panel or pressing Escape closes it.

If a node has no MDX file (e.g., a simple Airtable base node), the panel shows a minimal auto-generated summary from the node's data fields (label, type).

### Header

Minimal top bar with the tool name and a brief description. No navigation needed since there's only one view.

## Keeping it up to date

Adding or modifying pipeline content requires no framework knowledge:

- **Add a node**: add an entry to the pipeline's `pipeline.ts` and create an `.mdx` file.
- **Add a pipeline**: create a new directory under `pipelines/`, add it to the registry in `index.ts` and `node-content.ts`.
- **Share a node**: move its definition to `shared/nodes.ts` and import it in each pipeline that uses it.
- **Edit node details**: edit the `.mdx` file.

Layout is automatic — no coordinates to adjust.

## Possible Future Work

- **Cross-cut view**: A horizontal view organized by concern (e.g., "all classifiers," "all Airtable bases," "all LLM usage") to spot duplication and unification opportunities.
- **Component catalog**: A flat searchable/filterable list of all components with status badges.
- **Filtering**: Filter nodes by status, tech stack, or external service.
- **Live data**: Pull metadata from GitHub (last commit, open PRs) or Airtable (record counts) to surface freshness info.
- **More granular node types**: Split `processor` into subtypes like `scraper`, `classifier`, `extractor` if the visual distinction becomes useful.
