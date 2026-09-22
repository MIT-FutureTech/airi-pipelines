# AGORA scope assessment — methodology and results

**Corpus:** OECD.AI Policy Observatory policy initiatives
**Assessed:** 730 documents · **Model:** `google/gemini-3.5-flash-lite` via OpenRouter
**Run:** 2026-07-28 13:01 UTC · **Cost:** $2.61 · **Failures:** 0

---

## 1. What this does

Every document in the OECD.AI export is scored **0–100** for how well it falls
within the scope of the CSET **AGORA** database, with a short written rationale for
each score. The purpose is triage: identifying which of the OECD's ~2,300 catalogued
AI policy initiatives are candidates for AGORA ingestion, without a human reading
each one.

The score is a *confidence that an AGORA analyst would include the document*, not a
measure of the document's importance.

---

## 2. Source data and what was assessable

The input is `oecd_policy_initiatives_extracted_results.csv` (99 MB, 2,305 rows ×
26 columns, single aggregator: OECD.AI Policy Observatory). Every row is an AI
policy initiative with OECD-supplied metadata; some rows also carry text extracted
from an attached PDF.

| | Rows | Note |
|---|---:|---|
| Total initiatives | 2,305 | |
| **With usable extracted text** | **730** | assessed here |
| No text — no PDF ever fetched | 1,568 | `TextSource=skipped`, `WhyEmpty=empty_directory_path` |
| No text — all extractors returned empty | 3 | |
| Text present but junk (<200 chars) | 4 | excluded by `--min-chars 200` |

**Only the 730 with usable full text were assessed.** This was a deliberate choice
(full-text-only) over the alternative of also scoring the remaining 1,575 from their
OECD summaries alone. Every row does carry a human-written OECD abstract (mean 293
characters), so a summary-tier pass over the whole 2,305 remains available.

Corpus characteristics: 86 distinct jurisdictions; ~541 documents in English and
~179 in other languages (Korean, Chinese/Japanese, Arabic, Cyrillic, Hebrew, Thai
and accented Latin scripts all present); document lengths from 935 characters to
4.56 million.

---

## 3. Files

### Prompt and schema (the tuning surface)

| File | Role |
|---|---|
| **`agora_scope.md`** | AGORA's scoping definition, transcribed from CSET's published scoping and screening guidance, plus the 0–100 banded rubric. **Injected wholesale into the system prompt.** Scoring behaviour is tuned by editing this file, not the code. |
| **`scope_schema.json`** | JSON Schema for the structured output — the four fields the model must return, with the field-level instructions that govern each. |

The system prompt itself is the `SYSTEM_PROMPT` constant in `assess_scope.py`. It
wraps `agora_scope.md` and adds the title-extraction rule (§6).

### Code

| File | Role |
|---|---|
| `assess_scope.py` | The runner — selects rows, builds prompts, calls OpenRouter, writes results |
| `match_agora.py` | Matches results against the AGORA dataset, adds `AGORA link`, prints banded coverage |
| `summarise_run.py` | Score distribution, band breakdown, outliers for any results file |
| `make_charts.py` | Renders the six PNGs in `charts/` (reads both the results CSV and the source CSV — the coverage chart needs all 2,305 rows) |

### Outputs

`results/agora_scope_rows{range}_{model}_{timestamp}.csv` plus a
`_summary.json` sidecar per run, and `_agora.csv` after AGORA matching. Filenames
encode the row range, model and UTC timestamp so runs never overwrite each other.

---

## 4. The scoring rubric

Documents are scored against seven bands defined in `agora_scope.md` §4:

| Band | Meaning |
|---|---|
| 90–100 | Unambiguously in scope — central subject is AI, substantially operative text |
| 75–89 | Clearly in scope — AI significant or pervasive, possibly lighter-touch |
| 60–74 | Probably in scope — meets the definition with a real weakness |
| 40–59 | Genuinely borderline — an analyst could decide either way |
| 25–39 | Probably out of scope — AI small and isolated, or largely descriptive |
| 10–24 | Clearly out of scope — entirely non-operative, or AI merely contextual |
| 0–9 | Definitively out of scope — not about AI, or no AI-specific tailoring |

The load-bearing distinction throughout is AGORA's **operative vs non-operative**
test: text meant to shape behaviour is in scope even without legal force, while a
document consisting entirely of description or announcement is out.

**One deliberate departure from the source material.** CSET's documentation includes
a "Current coverage" section stating that AGORA currently skews to US federal and
state law. That describes what AGORA *has collected*, not what is *in scope*. The
rubric flags this explicitly and instructs that jurisdiction must **not** reduce a
score — otherwise the US skew would contaminate the scoring of a global corpus.

---

## 5. Run configuration

| Parameter | Value | Rationale |
|---|---|---|
| Model | `google/gemini-3.5-flash-lite` | Chosen over `gemini-3.6-flash` on a 5-document A/B: mean absolute score difference 3.6 points, identical rank ordering, but 6.4× cheaper ($0.0036 vs $0.0217/doc) and 5× faster |
| `--max-chars` | 40,000 | Head 75% + tail 25%, with the elision marked in the prompt. 420 of 730 documents were truncated |
| `--max-tokens` | 2,500 | Ample — Flash Lite averaged 171 completion tokens per document |
| `--temperature` | 0.0 | |
| `--workers` | 8 | |
| `--max-cost` | $5.00 | Hard ceiling; not reached |

Truncation keeps the head because scope clauses, preambles and tables of contents
live at the front, and samples the tail to catch annexes and schedules.

**Cost and throughput:** 7,653,665 input tokens, 125,169 output tokens,
**$2.609027 total** ($0.003574/document), 351.9 seconds, **730/730 succeeded**.

---

## 6. Output fields

Per document: `ID`, `OECD slug`, `Link`, `AGORA ID`, `AGORA link`,
`AGORA match method`, `AGORA match confidence`, `AGORA matched name`,
`Name (original language)`, `Name (original language) ISO code`,
`Name (original language) found in text`, `Name (English translation)`,
`Jurisdiction`, `Date introduced`, `Most recent activity`,
`Most recent activity date`, `Scope score`, `Scope score rationale`,
`LLM model used`, `LLM query status`, `LLM API cost`, plus provenance columns
(`csv_row`, `text_row`, `OECD name`, `chars_sent`, `truncated`, token counts,
`attempts`).

**Identifiers.** Two source columns are unique across all 2,305 rows: `ID`
(`ID_0001`…`ID_2305`) and `OECD slug` (the OECD.AI URL segment). Prefer the slug as
a join key — `ID` is positional and shifts if the export is regenerated. **`Link` is
not unique** (511 rows share a Link with another row) and must never be used as a key.

**Cost** is the actual figure charged by OpenRouter (`usage.include`), not an
estimate.

**Status** is `success` or `failed: <reason>` — `content moderation`,
`token length limit`, `rate limited`, `insufficient credits`, `auth error`,
`provider error (HTTP n)`, `timeout`, `unparseable model output`, `network error`,
or `not attempted: cost cap reached`.

### The title-verification column

`Name (original language) found in text` is computed **in code, not by the model**:
it tests whether the returned title actually occurs in the text that was sent
(`yes` / `partial` / `no` / `n/a`), folding whitespace, case and typographic
punctuation. `partial` means ≥80% of title words are present but not contiguously —
the signature of a title split across PDF lines.

This exists because it caught a real failure. An earlier prompt revision asked the
model to prefer native-language titles; Flash Lite responded by **inventing an
Arabic title** for Egypt's *Guide to Egypt's National AI Governance Framework* — a
document containing no Arabic characters at all — and produced a *different*
fabricated title on each run, one of which mistranslated "artificial intelligence"
as "artificial prudence". Pressing a model for a native title it cannot see invites
confabulation. The prompt now frames the field as transcription rather than recall
and states that English is the correct answer for documents published in English.

Full-run result: **669 verbatim, 45 partial, 3 not found, 13 blank.**

---

## 7. Results

### 7.1 Score distribution

![Score distribution with AGORA coverage](charts/01_score_distribution.png)

Mean 53.9, median 75, range 0–100. The distribution is strongly **bimodal** — the
model is decisive, with only 3.6% of documents landing in the genuinely borderline
40–59 range.

| Band | Documents | % | Already in AGORA | % of band |
|---|---:|---:|---:|---:|
| 0–10 | 138 | 18.9% | 0 | 0.0% |
| 11–20 | 128 | 17.5% | 0 | 0.0% |
| 21–30 | 6 | 0.8% | 0 | 0.0% |
| 31–40 | 15 | 2.1% | 0 | 0.0% |
| 41–50 | 17 | 2.3% | 0 | 0.0% |
| 51–60 | 14 | 1.9% | 0 | 0.0% |
| 61–70 | 41 | 5.6% | 0 | 0.0% |
| 71–80 | 99 | 13.6% | 0 | 0.0% |
| 81–90 | 198 | 27.1% | 9 | 4.5% |
| 91–100 | 74 | 10.1% | 12 | 16.2% |
| **Total** | **730** | | **21** | **2.9%** |

Aggregated: **57.1% in scope** (≥60), **3.6% borderline** (40–59), **39.3% out of
scope** (<40).

### 7.2 External validation against AGORA

`match_agora.py` matched the 730 assessed documents against
`data/agora/documents.csv` (1,084 AGORA documents) by three methods, each recorded
per row so any match can be audited: **URL** (OECD `Link` equals AGORA
`Link to document`), **exact** (normalised title equality against `Official name` or
`Casual name`), and **fuzzy** (difflib ratio ≥0.92). Title matches are vetoed when
jurisdiction and AGORA authority are incompatible, because titles like "National AI
Strategy" collide across jurisdictions.

**21 of 730 matched (2.9%)** — 7 URL, 5 exact, 9 fuzzy — resolving to 17 unique
AGORA IDs.

**Every match landed in the 81–100 range. None below 81.** Because AGORA membership
is a human inclusion decision made independently of this pipeline, that is
meaningful external corroboration that the scores track real AGORA scoping judgement
at the top end. Matched documents include the EU AI Act (100), the NIST AI RMF
(100), both US executive orders on AI (100), the OECD AI Principles (100), Ghana's
National AI Strategy (90) and Singapore's National AI Strategy 2.0 (85).

The low match rate is expected, not a shortfall: AGORA currently holds 630 US
Congress documents plus ~150 US state documents, while this corpus is global and
predominantly non-US. **An unmatched document is usually outside AGORA's current
collection priorities rather than outside its scope** — which is precisely the gap
this exercise exists to map.

### 7.3 The ingestion shortlist

![Candidates not yet in AGORA](charts/05_agora_candidates.png)

**253 documents score ≥80 and have no match in AGORA**; 114 of those score ≥90.
This is the operational output of the exercise — the shortlist an AGORA analyst
would work through.

The distribution is directly relevant to AGORA's stated priorities. AGORA's
documentation names two next targets: broader US state coverage, and **Chinese
central government documents**. This corpus surfaces only **3** Chinese candidates,
so it will not help materially there. Where it *does* deliver is precisely where
AGORA describes its coverage as "ad hoc": non-US national frameworks. Peru (9),
Egypt (6), Ecuador (4), Brazil, Zimbabwe, Cambodia and Libya all appear with
high-confidence instruments that are absent from AGORA today.

### 7.4 Coverage bias — read every jurisdiction comparison through this

![Text coverage by jurisdiction](charts/04_text_coverage.png)

Whether an initiative has extractable text is **not random**, and the pattern is
strong enough to confound any cross-jurisdiction reading:

| | Initiatives | With text |
|---|---:|---:|
| Anglophone (US, UK, AU, CA, IE, NZ) | 280 | **65.4%** |
| All other jurisdictions | 2,025 | **27.0%** |

Ukraine has **0 of 42** initiatives with text. Portugal 5% of 75, Slovenia 9% of 77,
France 10% of 70, Latvia 10%, Austria 13%, Belgium 14% — against the United States
at 87% of 89.

It skews by document type just as hard. National AI strategies have 71% text
coverage, laws 64%, guidance documents 63% — but initiatives to foster AI compute
access just **5.6%**, public-awareness skills programmes 10%, and public-sector AI
use cases 15%.

**Two consequences.** First, §7.5's jurisdiction chart partly measures *PDF
availability* rather than policy activity — Japan appearing 100% in-scope on 15
documents while France barely registers is substantially an artefact of what was
fetchable. Second, the under-sampled document types are exactly the ones that score
lowest, so the **true out-of-scope share across the full OECD catalogue is likely
higher than the 39.3% measured here**.

### 7.5 Jurisdictions

![Documents by jurisdiction and scope tier](charts/02_jurisdictions.png)

86 jurisdictions are represented. The United States leads with 77 documents,
followed by the United Kingdom (49), European Union (42), Saudi Arabia (41) and
Australia (32).

The in-scope proportion varies sharply and informatively:

| Jurisdiction | Documents | Mean score | In scope (≥60) |
|---|---:|---:|---:|
| Japan | 15 | 87.3 | 100.0% |
| United Kingdom | 49 | 60.8 | 63.3% |
| United States | 77 | 59.9 | 63.6% |
| Saudi Arabia | 41 | 30.2 | 31.7% |
| Canada | 14 | 20.4 | 14.3% |

Saudi Arabia's low mean is not a jurisdiction penalty — it is composition. 28 of its
41 documents score below 40, and they are overwhelmingly personal-data instruments
(Standard Contractual Clauses for Personal Data Transfer, Rules for Appointing a
Data Protection Officer, the National Register of Controllers) that govern data
rather than AI. That is exactly the distinction AGORA's §1.2 subject-matter test is
designed to catch, and the model applied it correctly.

Bar length here should be read as "how much of this jurisdiction we could see",
not "how much AI governance this jurisdiction produces."

### 7.6 Dates

![Documents by year introduced](charts/03_dates.png)

727 of 730 documents carry a usable `Date introduced`. Activity is negligible before
2016, rises steeply through 2017–2018, and plateaus at roughly 90–103 documents a
year from 2019 to 2024. The falloff in 2025 (34) and 2026 (6) reflects the OECD's
own cataloguing lag and PDF-attachment rate, not a decline in AI policymaking.

This shape corroborates AGORA's recency rule (§2.1) — that "directly" addressing AI
generally excludes instruments predating modern machine learning. The corpus is
overwhelmingly post-2016 by construction.

### 7.7 Legal force vs subject matter — the strongest validation available

![Binding status vs scope tier](charts/06_binding_vs_scope.png)

The OECD supplies a `Binding` label, independent of anything in this pipeline. At
first glance it appears to *contradict* the scores: documents labelled **Binding**
average **46.4**, while **Non-binding** average **50.9**. Legally binding documents
scoring lower looks like a failure.

It is not. Nearly half of the OECD's binding documents are out of AGORA's scope
because they are **general data-protection law**, not AI law — Saudi Arabia's PDPL
and its implementing rules, Brazil's LGPD, Norway's Health Register Act, New York's
Electronic Monitoring Bill. Binding, and not about AI.

One rationale demonstrates the distinction being drawn deliberately: for a Saudi
guidance document the model notes that although the issuing authority is SDAIA, the
Saudi *Data and AI* Authority, the text itself is entirely personal-data protection
— so it fails the subject-matter test regardless of who published it.

Restrict to documents that genuinely are about AI (score ≥60) and the ordering
rights itself: **Binding 85.2, Non-binding 82.7.**

The model therefore separates **legal force** from **subject matter**, which is
exactly what AGORA §1.2 requires. This is stronger evidence than the AGORA match in
§7.2, because it covers all 730 documents against an independent label rather than
21 against a membership list.

### 7.8 Face validity

Mean score by OECD initiative type orders exactly as AGORA's operative-text
criterion predicts:

| Initiative type | n | Mean score |
|---|---:|---:|
| National AI strategy | 63 | 82.6 |
| Principles/guidelines/frameworks for trustworthy AI | 65 | 77.0 |
| Declaration, opinion, or outcome document | 18 | 72.2 |
| Guidance document | 81 | 59.8 |
| Law/legislation/act | 28 | 57.1 |
| … | | |
| Research grants/funding | 21 | 38.8 |
| Support for AI diffusion in firms | 14 | 37.4 |
| Networks and communities of practice | 31 | 31.7 |
| Investment in AI compute capacity | 14 | 27.1 |
| Initiatives to promote data access and sharing | 29 | 21.1 |

By OECD category: "National – Strategy" 82.6, "Regulations, guidelines and
standards" 62.5, "AI policy initiatives, programmes and projects" 40.4. The model is
discriminating on operative content rather than on topic.

### 7.9 No evidence of a language penalty

Documents whose verified title is non-English average **58.3**; English-titled
documents average **52.9** (documents where no title was returned are excluded from
both). If anything non-English documents score slightly higher, and there is no sign
the model penalises material it has to read in another script.

*A caution on how this was measured.* An earlier check using a crude
regex script-detector appeared to show Korean-script documents averaging 29.7
against 54.6 for Latin — a large apparent penalty. That was an artefact: the
detector classified documents as Korean on a single stray character, and the
resulting "Korean" set turned out to be Ontario's *Working for Workers Act*, New
York's *Electronic Monitoring Bill* and *Canada's Digital Charter*, with a median
Hangul fraction of 0.00. The figures above instead use the model's own
`Name (original language) ISO code`, which is verified against the document text by
the check in §6. Script detection on extracted PDF text is unreliable and should not
be used for this purpose.

---

## 8. Limitations

**Metadata leaks into the score.** Of 36 groups of documents sharing byte-identical
text, only 16 scored identically. The largest spread was **65 points** — ID_2005
scored 10 and ID_2006 scored 75 on the same 764,929-character document. Since the
text is identical, the only differing input is the metadata block, so the initiative
name and OECD summary are influencing scores despite the prompt instructing
otherwise. *If per-document scores must be defensible, drop the metadata block from
`build_user_prompt` and re-run text-only.*

**Run-to-run variance.** Repeat runs of the same model at temperature 0 move
individual scores by roughly ±5–10 points (provider non-determinism). Treat scores
as band indicators, not precise values. Majority-of-3 sampling would tighten this at
triple the cost.

**Truncated documents score higher** — 63.7 mean against 40.6 for untruncated. Most
likely confounded (long documents are more often substantive laws; short extractions
are more often press releases) but not controlled for.

**Two documents are unscoreable.** ID_1719 (Brazil) and ID_1965 (Mexico) extracted
as `(cid:NNN)` font-code garbage — 66% and 88% of the sent window — yet both
received 75. Treat as unscored. Only 9 of 730 show any such damage.

**Source-data defects.** 47 rows share text byte-identically with another row (37
groups); some are genuine duplicate listings, others are mis-attached PDFs ("STEM
Cell Network" and "Genome Canada" carry the same document). Three AGORA matches
collapse many-to-one because of OECD errors: ID_1790 and ID_1986 carry an identical
Federal Register URL, and three separate Chinese initiatives point at the same PDF.
One document (ID_0321, Israel) had its Hebrew extracted in reversed character order.

**Coverage is biased, not merely partial.** 1,575 of 2,305 initiatives were never
assessed because no source document was fetched — and as §7.4 shows, which ones are
missing correlates strongly with language (anglophone 65% coverage vs 27% for
everyone else) and with document type (compute-access initiatives 5.6% vs national
strategies 71%). This is the most consequential limitation in the report. No
statement of the form "jurisdiction X produces more in-scope AI governance than
jurisdiction Y" is supportable from this data, and the measured 39.3% out-of-scope
share is probably an underestimate for the catalogue as a whole.

---

## 9. Reproducing

```bash
python assess_scope.py --rows 1-730 --model google/gemini-3.5-flash-lite \
    --max-tokens 2500 --max-cost 5.00 --workers 8 --tag fullrun
python match_agora.py results/<output>.csv --show-matches
python summarise_run.py results/<output>_agora.csv
python make_charts.py results/<output>_agora.csv
```

`OPENROUTER_API_KEY` is read from the repo-root `.env`. Preview a selection with
`--list` and estimate cost with `--estimate` before spending anything.

---

## 10. Suggested next steps

1. **Re-fetch missing PDFs, prioritised by the coverage gap.** 1,227 of the unassessed rows carry a landing-page `Link`. Targeting the worst-covered jurisdictions first (Ukraine 0%, Portugal 5%, Slovenia 9%, France 10%) would attack the report's biggest weakness directly, and is worth more than any refinement to the scoring itself.
2. **Text-only re-run** to eliminate the metadata leak, then compare the identical-text groups — the single highest-value change to per-document score defensibility.
3. **Hand the 253-document shortlist (§7.3) to CSET** for adjudication. It is the deliverable; it also yields a labelled set for measuring precision at ≥80.
4. **Human validation of the borderline band** — 26 documents scored 40–59. Adjudicating those calibrates the rubric where it is weakest.
5. **Summary-tier pass over the 1,575 unassessed initiatives** using the OECD abstract, with a confidence flag marking the weaker tier (~0.6 M tokens). Weaker per document, but it is the only route to unbiased coverage without a crawl.

---

*Charts were rendered on the light surface only; palettes were validated for
colourblind separation and contrast before use.*
