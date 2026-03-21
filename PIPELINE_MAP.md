# AIRI Pipeline Map

> Generated 2026-03-21 by surveying all repos in the MIT-FutureTech GitHub org.
> This is a shallow survey — details of inner workings are deferred to step 4.

## Overview

The AI Risk Initiative (AIRI) operates several data pipelines that discover, screen, classify, and visualize information about AI risks, mitigations, governance, incidents, and organizations. **Airtable is the central data hub** — nearly every component reads from and/or writes to shared Airtable bases.

There are **6 classification pipelines** organized by the domain of information they produce, plus visualization tools and shared infrastructure:

1. **Actors** — classify organizations by their AI ecosystem role
2. **Risks** — classify AI risk mentions in corporate documents
3. **Mitigations** — classify mitigation actions from research papers and corporate documents
4. **Governance** — classify governance documents (proposed)
5. **Incidents** — classify AI incidents (proposed)
6. **Document Processing** — shared input layer: discover, extract, screen, and type-classify documents (feeds into Actors, Risks, Mitigations)

## Unified Graph

The diagram below shows all components and their data flows. Pipeline membership is annotated per node. Some nodes (notably `airi-orgrev-orglist`) participate in multiple pipelines.

```
 ╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
 ║                                        DOCUMENT PROCESSING (shared input layer)                            ║
 ║                                                                                                            ║
 ║   Google Custom Search          companiesmarketcap.com                                                     ║
 ║          │                              │                                                                  ║
 ║          ▼                              ▼                                                                  ║
 ║   greylitsearcher               airi-orgrev-orglist ─────────────────────┐                                 ║
 ║   (Streamlit, manual)           (scrapes top 1000 companies)             │                                 ║
 ║          │                              │                                │                                 ║
 ║          ▼                              ▼                                │                                 ║
 ║   Airtable Base 1 ◄────────── Airtable Base 3              downloads     │                                 ║
 ║   Grey Literature               Companies                  corporate     │                                 ║
 ║   raw_results                   (names, metadata)           PDFs         │                                 ║
 ║   (status=pending)                      │                                │                                 ║
 ║          │                              │                                │                                 ║
 ║          ▼                              │                                │                                 ║
 ║   airi-orgreview-fulltext               │                                │                                 ║
 ║   (extracts text from URLs)             │                                │                                 ║
 ║          │                              │                                │                                 ║
 ║          ▼                              │                                │                                 ║
 ║   airi-llm-screening-                   │                                │                                 ║
 ║     orchestrator ◄──────────────────────┘ (actor data provides           │                                 ║
 ║   (Prefect, production)                    screening context)            │                                 ║
 ║          │                                                               │                                 ║
 ║          │  [agentic-framework: prototype replacement                    │                                 ║
 ║          │   for the orchestrator, LangGraph + RAG]                      │                                 ║
 ║          │                                                               │                                 ║
 ║          ▼                                                               │                                 ║
 ║   Airtable Base 1                                                        │                                 ║
 ║   screening_results                                                      │                                 ║
 ║   (approved / rejected)                                                  │                                 ║
 ║          │                                                               │                                 ║
 ║          │ approved only                                                 │                                 ║
 ║          ▼                                                               │                                 ║
 ║   org-doc-classifier                                                     │                                 ║
 ║   (12+ document categories)                                              │                                 ║
 ║          │                                                               │                                 ║
 ║          ▼                                                               │                                 ║
 ║   Airtable Base 1                                                        │                                 ║
 ║   raw_results.doc_type                                                   │                                 ║
 ║   (populated)                                                            │                                 ║
 ╚══════════════════════╤═════════════════════════════════════════════════╤═╝                                 ║
                        │                                                 │                                   ║
 ╔══════════════════════╧══╗  ╔════════════════════════════╗  ╔═══════════╧══════════════════════════════════╗║
 ║      ACTORS             ║  ║       RISKS                ║  ║           MITIGATIONS                        ║║
 ║                         ║  ║                            ║  ║                                              ║║
 ║  Company List           ║  ║  classified docs           ║  ║   classified docs    Research Papers         ║║
 ║      │                  ║  ║      │                     ║  ║       │              (ArXiv, CrossRef,       ║║
 ║      ▼                  ║  ║      ▼                     ║  ║       │               SSRN, Scopus)          ║║
 ║  ai-actor-classifier    ║  ║  airi-orgrev-orglist       ║  ║       │                    │                 ║║
 ║  (GPT-5.2 + web search  ║  ║  (PDF keyword extraction   ║  ║       │                    ▼                 ║║
 ║   classifies Developer, ║  ║   + LLM risk classif.      ║  ║       │          mitigations_review          ║║
 ║   Deployer, Infra, etc.)║  ║   24-code taxonomy,        ║  ║       │          (systematic lit review,     ║║
 ║      │                  ║  ║   7 risk domains)          ║  ║       │           screens with Gemini)       ║║
 ║      ▼                  ║  ║      │                     ║  ║       │                    │                 ║║
 ║  Airtable Base 3        ║  ║      ▼                     ║  ║       ▼                    ▼                 ║║
 ║  Companies              ║  ║  risk classification       ║  ║  airi-orgrev-orglist  Airtable Base 2        ║║
 ║  (actor roles)          ║  ║  output (CSV)              ║  ║  (PDF keyword extr.  Mitigations V2          ║║
 ║      │                  ║  ║                            ║  ║   + LLM mitig.       (llm_todo)              ║║
 ║      ▼                  ║  ╚════════════════════════════╝  ║   classif. 44-code)       │                  ║║
 ║  airi-orgreview-        ║                                  ║       │                    ▼                 ║║
 ║    logoprocessing       ║                                  ║       │          airi-mitrev-classifier      ║║
 ║  (logo processing)      ║                                  ║       │          (3-level taxonomy,          ║║
 ║      │                  ║                                  ║       │           44 codes, OpenRouter)      ║║
 ║      ▼                  ║                                  ║       │                    │                 ║║
 ║  Airtable Base 3        ║                                  ║       ▼                    ▼                 ║║
 ║  Companies (logos)      ║                                  ║  mitigation classif.  Airtable Base 2        ║║
 ║                         ║                                  ║  output (CSV)         Mitigations V2         ║║
 ╚═════════════════════════╝                                  ║                       (llm_classified)       ║║
                                                              ╚══════════════════════════════════════════════╝║
                                                                                                              ║
 ╔═══════════════════════════════╗  ╔═══════════════════════════════════╗                                     ║
 ║   GOVERNANCE (proposed)       ║  ║   INCIDENTS (proposed)            ║                                     ║
 ║                               ║  ║                                   ║                                     ║
 ║  Government Sources           ║  ║  AIID (incidentdatabase.ai)       ║                                     ║
 ║      │                        ║  ║      │                            ║                                     ║
 ║      ▼                        ║  ║      ▼                            ║                                     ║
 ║  governance-scraper           ║  ║  incident-scraper                 ║                                     ║
 ║  (NOT BUILT)                  ║  ║  (NOT BUILT)                      ║                                     ║
 ║      │                        ║  ║      │                            ║                                     ║
 ║      ▼                        ║  ║      ▼                            ║                                     ║
 ║  Airtable Base 4              ║  ║  Airtable Base 5                  ║                                     ║
 ║  Governance                   ║  ║  Incidents                        ║                                     ║
 ║  (currently manual)           ║  ║  (currently manual)               ║                                     ║
 ║      │                        ║  ║      │                            ║                                     ║
 ║      ▼                        ║  ║      ▼                            ║                                     ║
 ║  governance-classifier        ║  ║  incident-classifier              ║                                     ║
 ║  (NOT BUILT)                  ║  ║  (NOT BUILT)                      ║                                     ║
 ╚═══════════════════════════════╝  ╚═══════════════════════════════════╝                                     ║
                                                                                                              ║
 ╔═══════════════════════════════════════════════════════════════════════════════════════════════════════════╗║
 ║                                         VISUALIZATION                                                     ║║
 ║                                                                                                           ║║
 ║   airi-navigator                    governance-visualizations           airi-chatbot-nov                  ║║
 ║   (Next.js, Vercel)                 (Next.js + ECharts, Vercel)         (Flask + Gemini, Railway)         ║║
 ║   airisk.mit.edu                    embeds into Webflow                 PAUSED (March 2026)               ║║
 ║   5 datasets: risks, mitigations,   2 datasets: governance,                                               ║║
 ║   governance, incidents, Delphi      incidents                                                            ║║
 ║   32 embeddable visualizations       6+ chart types, Redis cache                                          ║║
 ╚═══════════════════════════════════════════════════════════════════════════════════════════════════════════╝║
                                                                                                              ║
 ╔═══════════════════════════════════════════════════════════════════════════════════════════════════════════╗║
 ║                                     INFRASTRUCTURE                                                        ║║
 ║                                                                                                           ║║
 ║   revelio-cloner ──▶ GCS bucket ──▶ BigQuery (optional)                                                   ║║
 ║   (WRDS → GCS,        (Parquet)        │                                                                  ║║
 ║    monthly cron)                        ▼                                                                 ║║
 ║                                   airi-revelio                   bigquery-gcs-utils                       ║║
 ║                                   (job posting analysis          (utility library)                        ║║
 ║                                    for AI risk mgmt roles)                                                ║║
 ╚═══════════════════════════════════════════════════════════════════════════════════════════════════════════╝║
```

Note: `airi-orgrev-orglist` appears in three pipelines (Actors via company scraping, Risks via risk classification, Mitigations via mitigation classification). It is one repo that does PDF analysis, keyword extraction, and LLM classification for both risks and mitigations, while also building the company list that feeds actor classification.

## Pipelines

### Actors

Classifies organizations by their role in the AI ecosystem (Developer, Deployer, User, Infrastructure Provider, etc.).

| Repo | Role | Language | Trigger | Status |
|------|------|----------|---------|--------|
| [ai-actor-classifier](https://github.com/MIT-FutureTech/ai-actor-classifier) | AI ecosystem role classification per company | Python + OpenRouter (GPT-5.2) | Batch scripts | Active |
| [airi-orgrev-orglist](https://github.com/MIT-FutureTech/airi-orgrev-orglist) | Company scraping from companiesmarketcap | Python + Playwright | CLI scripts | Active |
| [airi-orgreview-logoprocessing](https://github.com/MIT-FutureTech/airi-orgreview-logoprocessing) | Logo download + white-background processing | Python + Pillow | CLI | Active |

### Risks

Classifies AI risk mentions from corporate documents into a 24-code taxonomy across 7 risk domains: Discrimination & Toxicity, Privacy & Security, Misinformation, Malicious Actors, Human-Computer Interaction, Socioeconomic & Environmental, and AI System Safety.

Two-step process: PDF keyword extraction finds AI-related mentions with surrounding context, then LLM classification applies a risk gate and assigns taxonomy codes.

| Repo | Role | Language | Trigger | Status |
|------|------|----------|---------|--------|
| [airi-orgrev-orglist](https://github.com/MIT-FutureTech/airi-orgrev-orglist) (`pdf_analysis/`) | PDF keyword extraction — searches corporate PDFs for AI-related keywords, captures 2000-char context paragraphs | Python | CLI scripts | Active |
| [airi-orgrev-orglist](https://github.com/MIT-FutureTech/airi-orgrev-orglist) (`llm_classification/`) | LLM risk classification — two-stage gate + subdomain classifier into 24-code taxonomy | Python + OpenRouter (Gemini 2.5 Flash Lite) | CLI scripts | Active |

### Mitigations

Classifies AI risk mitigation actions into a 3-level, 44-code hierarchical taxonomy. Two independent input paths: corporate documents and research papers.

| Repo | Role | Language | Trigger | Status |
|------|------|----------|---------|--------|
| [airi-orgrev-orglist](https://github.com/MIT-FutureTech/airi-orgrev-orglist) | PDF keyword extraction + LLM mitigation classification (from corporate docs) | Python + OpenRouter | CLI scripts | Active |
| [mitigations_review](https://github.com/MIT-FutureTech/mitigations_review) | Systematic literature search + abstract screening (from research papers) | Python + Gemini | CLI pipeline scripts | Active |
| [airi-mitrev-classifier](https://github.com/MIT-FutureTech/airi-mitrev-classifier) | LLM classification into 3-level mitigation taxonomy (from research papers) | Python + OpenRouter | CLI (`run_local.py`), supports continuous mode | Active |

### Governance (proposed)

Would classify governance documents (regulations, policies, frameworks) into risk subdomains, lifecycle stages, actor types, and sectors. Currently data is manually entered and classified in Airtable.

**No automated scraper or classifier repos exist yet.**

### Incidents (proposed)

Would classify AI incidents from AIID into subdomains, causal factors, severity, and purpose. Currently data is manually entered and classified in Airtable.

**No automated scraper or classifier repos exist yet.**

### Document Processing (shared input layer)

Discovers, extracts, screens, and type-classifies documents. Feeds into Actors, Risks, and Mitigations pipelines.

| Repo | Role | Language | Trigger | Status |
|------|------|----------|---------|--------|
| [greylitsearcher](https://github.com/MIT-FutureTech/greylitsearcher) | Document discovery via Google Custom Search | Python + Streamlit | Manual (web UI) | Active |
| [airi-orgreview-fulltext](https://github.com/MIT-FutureTech/airi-orgreview-fulltext) | Full-text extraction from URLs (HTML + PDF) | Python | CLI | Active |
| [airi-llm-screening-orchestrator](https://github.com/MIT-FutureTech/airi-llm-screening-orchestrator) | Production screening — relevance classification | Python + Prefect | systemd service, continuous polling (60s) | Active, production |
| [agentic-framework](https://github.com/MIT-FutureTech/agentic-framework) | Next-gen screening prototype with RAG (intended to replace orchestrator) | Python + LangGraph + ChromaDB | Manual (dev only) | Active, prototype |
| [org-doc-classifier](https://github.com/MIT-FutureTech/org-doc-classifier) | Document type classification (12+ categories) | Python + Streamlit | CLI or Streamlit dashboard | Active |

## Visualization

| Repo | Role | Language | Trigger | Status |
|------|------|----------|---------|--------|
| [airi-navigator](https://github.com/MIT-FutureTech/airi-navigator) | Primary data explorer — 5 datasets, 32 embeddable visualizations, airisk.mit.edu | TypeScript + Next.js 16 + React 19 | Manual sync scripts; auto-deploy on push to Vercel | Active, production |
| [governance-visualizations](https://github.com/MIT-FutureTech/governance-visualizations) | Governance/incident charts embedded in Webflow | TypeScript + Next.js + ECharts + Preact | Vercel cron (daily) | Active, production |
| [airi-chatbot-nov](https://github.com/MIT-FutureTech/airi-chatbot-nov) | RAG chatbot over AIRI data | Python (Flask) + Gemini + React | Railway deployment | **Paused** (March 2026) |

## Infrastructure

| Repo | Role | Language | Trigger | Status |
|------|------|----------|---------|--------|
| [revelio-cloner](https://github.com/MIT-FutureTech/revelio-cloner) | Export Revelio data from WRDS to GCS (Parquet) | Python | Monthly cron (OpenStack VM) | Active, production |
| [airi-revelio](https://github.com/MIT-FutureTech/airi-revelio) | Analyze job postings for AI risk management keywords | Python + WRDS/GCS/BigQuery | CLI with checkpointing | Active |
| [bigquery-gcs-utils](https://github.com/MIT-FutureTech/bigquery-gcs-utils) | Utility library for GCS ↔ BigQuery operations | Python | Imported as library | Active |

## Airtable Bases

| Base | ID | Primary Tables | Used By |
|------|----|---------------|---------|
| **Base 1: Grey Literature** | `appHrhJQHkZz4c82U` | `raw_results`, `screening_results`, `Companies`, `vector_db_sync` | greylitsearcher, airi-orgreview-fulltext, airi-llm-screening-orchestrator, agentic-framework, org-doc-classifier |
| **Base 2: Mitigations V2** | `appUJl8KRAUMeIVXs` | `SysRev_MitigationDatabase`, `MitTax_02`, `SysRev_Documents`, `llm_prompts` | airi-mitrev-classifier, airi-navigator |
| **Base 3: Companies** | (varies) | `Companies`, `actor_reflections` | ai-actor-classifier, agentic-framework, airi-orgrev-orglist, airi-orgreview-logoprocessing |
| **Base 4: Governance** | `AIRTABLE_GOVERNANCE_BASE_ID` | `Unique Upload` | governance-visualizations, airi-navigator |
| **Base 5: Incidents** | `appNS59jePODVZwd9` | `Classifications` | governance-visualizations, airi-navigator |

## External Services

| Service | Purpose | Used By |
|---------|---------|---------|
| **Airtable** | Central data hub | Nearly all repos |
| **OpenRouter** | Multi-model LLM gateway | airi-llm-screening-orchestrator, agentic-framework, org-doc-classifier, ai-actor-classifier, airi-mitrev-classifier, airi-orgrev-orglist |
| **Google Gemini** | LLM for screening / chatbot | mitigations_review, airi-chatbot-nov |
| **Anthropic Claude** | LLM (classification) | org-doc-classifier, agentic-framework |
| **OpenAI** | LLM (classification) | org-doc-classifier, airi-llm-screening-orchestrator |
| **Google Custom Search** | Document discovery | greylitsearcher |
| **Google Cloud (GCS/BigQuery)** | Data storage + analytics | revelio-cloner, airi-revelio, bigquery-gcs-utils |
| **WRDS** | Revelio Labs data access | revelio-cloner, airi-revelio |
| **Vercel** | Web app hosting | airi-navigator, governance-visualizations |
| **Railway** | Chatbot hosting | airi-chatbot-nov (paused) |
| **Upstash Redis** | Cache layer | governance-visualizations |
| **ChromaDB** | Vector database for RAG | agentic-framework |
| **Prefect** | Workflow orchestration | airi-llm-screening-orchestrator |

## Repos NOT Part of the AIRI Pipeline

The MIT-FutureTech org contains many repos unrelated to the AIRI pipeline:

- **Delphi project**: Delphi-Dashboard, Delphi-R2/R3 graphs, Delphi-harms-taxonomy, Delphi-Prototype-Dashboard (expert survey on AI risks — data feeds into airi-navigator but has its own workflow)
- **Algorithm/Processor projects**: Algorithm-Wiki-API, AlgorithmWiki, processordb-api, processordb-e2e, processordb-website, computerprogress.com
- **Quantum**: quantum-framework, Quantum-Nextjs
- **LLM Survey**: llm-survey-backend, llm-survey-frontend, MIT-IBM-LLM-Job-Tasks-Survey
- **Other research**: ai-efficiency, ai-future-of-work, ai-labor-economic-navigator, ai-winter-risk-playground, ia-enabled-scientific-frontier, llm_citation_intention, sdg-in-ai, TheComputationalLimitsOfDeepLearning, TransferLearning, MachineLearningLandscape
- **Internal**: airi-brand, airi-interview-process, airi-onboarding, ft-budget-helper, AIRI-test-repository, demo-repository, sanity-cms-demo, futuretech-site
- **Archived**: airisk-website

## Key Discrepancies with Prior Art

| Topic | Prior Art Says | Reality |
|-------|---------------|---------|
| AnnualReportSearcher | Separate ingestion component | No standalone repo found |
| agentic-framework | Primary screener | Prototype only; `airi-llm-screening-orchestrator` is production |
| governance-scraper | Proposed component | Does not exist |
| governance-classifier | Proposed component | Does not exist |
| incident-scraper | Proposed component | Does not exist |
| incident-classifier | Proposed component | Does not exist |
| airi-orgreview-fulltext | Not mentioned | Active production component |
| airi-llm-screening-orchestrator | Not mentioned | Active production component |
| mitigations_review | Not mentioned | Active — feeds the mitigation classifier |
| airi-orgrev-orglist | Simple list generator | Full pipeline: company scraping + PDF analysis + risk/mitigation classification |
| airi-orgrev-companylist | Company list generator | Empty repo (absorbed into airi-orgrev-orglist) |
| airi-orgrev-orglist scope | Not in prior art classification diagram | Classifies both risks (24-code) AND mitigations (44-code) from corporate docs |
