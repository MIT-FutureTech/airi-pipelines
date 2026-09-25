# AGORA Screening

Pre-screens candidate policy documents for whether they fall within the scope of
[AGORA](https://agora.eto.tech/), the CSET/ETO database of AI laws, regulations
and standards. Each document gets a 0-100 scope score and a short rationale.

AIRI's role in the AGORA collaboration is this pre-screening step: taking large
candidate corpora and deciding which documents are worth an analyst's attention.
The output is a ranked shortlist, not an inclusion decision.

## Why recall matters more than precision

A false positive costs a little more work at the next stage. A false negative
means a genuine AGORA document is never seen at all. Tune accordingly: this
pipeline should let borderline documents through.

## Status

The scoring stage is ported from a proof of concept (`docs/poc-report.md`) onto
the shared `toolbox` library, and is exercised end to end by the tests against a
stub LLM client.

**The port reproduces the proof of concept.** Full 730-document regression run
on the PoC's own model, 2026-09-20: 730 of 730 scored, $2.67 against its $2.61,
mean score 54.5 against 53.9, and 57.5 per cent at or above the in-scope
threshold against 57.1.

Per document the agreement is much looser - 53 per cent identical, 41 documents
crossing the threshold - but that is not the port. Re-running this pipeline
against *itself* moves documents nearly as much, which is the reproducibility
finding below. The proof of concept also ran at the provider's default
temperature, so its scores were a single sample rather than a fixed point.

`agora_screening.compare` runs against the baseline today and reproduces the
report's findings.

## Layout

| Path | Contents |
|---|---|
| `prompts/agora_scope.md` | AGORA's scoping definition and the 0-100 banded rubric. **This is the tuning surface** - it is injected wholesale into the system prompt, so it can be edited without touching Python. |
| `input/` | Source corpora. Gitignored; see its README for what belongs there. |
| `baseline/` | Proof-of-concept results, kept for regression comparison. Gitignored. |
| `docs/poc-report.md` | Methodology and results of the PoC full run: 730 documents, 2026-07-28. Charts referenced in it are not copied here; they live in the `governance-mapping` repo alongside the original. |
| `docs/poc-scope-schema.json` | The PoC's raw JSON Schema for structured output, superseded by a Pydantic model but kept because the field descriptions carry hard-won prompt wording. |

## Background

`docs/poc-report.md` is the main context document. Three findings from it shape
this pipeline's design:

- **Metadata leaked into the scores.** Of 36 groups of documents with
  byte-identical text, only 16 scored identically - one pair 65 points apart.
  The only differing input was the metadata block, so the initiative name and
  category were influencing a score the prompt said should come from the text.
  Hence the intended two-stage split: triage sees only metadata, scoring sees
  only document text.
- **Models confabulate titles.** Asked for a native-language title, Gemini
  invented a different Arabic title on each run for an Egyptian document
  containing no Arabic at all. The fix is a deterministic check, computed in
  code, that the returned title actually occurs in the supplied text.
- **Corrupt extractions still score well.** Two documents that extracted mostly
  to `(cid:NNN)` glyph codes were scored 75. Text quality needs to gate scoring
  rather than be left for the model to notice.

## Scope of a run

The OECD corpus has 2,305 initiatives, of which only 730 carry usable extracted
text. The PoC assessed those 730 and left the rest unassessed. A metadata-only
triage stage is what brings the other 1,575 into coverage.

## Running

From the repository root. Put a real `OPENROUTER_API_KEY` in `.env` first.

```bash
# Five documents, to check the wiring before spending anything
uv run --env-file=.env -m agora_screening \
    --output-dir pipelines/agora-screening/output \
    --limit 5 \
    --export-csv pipelines/agora-screening/output/results.csv

# The whole corpus
uv run --env-file=.env -m agora_screening \
    --output-dir pipelines/agora-screening/output \
    --export-csv pipelines/agora-screening/output/results.csv
```

`--help` lists every option.

## Model and cost

The default is `google/gemini-3.5-flash-lite` at temperature 0. A full
730-document run costs **$2.67** and takes under three minutes at
`--concurrency 8`.

`google/gemini-3.8-flash` also works and costs about **$9** for the same run.
Almost all of the difference is output tokens - roughly 1,130 per document
against flash-lite's 175, billed at $3.75 per million. Nothing measured so far
shows it scoring better, and with no labelled ground truth there is currently
no way to tell. Until there is, the cheaper model is the default.

## Reproducibility - read this before trusting a single score

**Temperature 0 does not make scoring deterministic.** Re-running 100 unchanged
documents through the unchanged pipeline reproduced:

| | |
|---|---|
| exactly | 72 of 100 |
| within 5 points | 91 of 100 |
| within 10 points | 96 of 100 |
| moved more than 20 points | 3 of 100 |
| crossed the in-scope threshold | 2 of 100 |

So a document's score carries a few points of noise either way, with a small
tail of large swings. For a recall-first shortlist that is tolerable: take
everything at or above the threshold and accept churn at the boundary. It does
mean **an individual score is not defensible on its own**, and that a shortlist
regenerated next week will not have identical membership.

If per-document defensibility ever matters, score each document several times
and take the median. That is not built, but it is the obvious next move, and it
is what the scale of the noise argues for.

Results are one JSON file per document under `output/score/`. A second run skips
documents already scored, so an interrupted run resumes; `--force` rescores. To
re-run a handful after a rubric change, delete their JSON files or pass
`--document-ids ID_0002,ID_0005`.

## The run report

Every run finishes by writing `report.md` into the output directory (or to
`--report-path`). It is the summary of what the run did, meant to be read
before the CSV:

- **Run** - model, temperature, rubric, corpus and text budget, taken from
  `run.json`, which the run writes before its first LLM call.
- **Coverage** - corpus size, how many records carried scoreable text, how
  many results are on disk, how many were written in this run versus carried
  over from earlier runs of the same directory, and how many failed.
- **Scores** - the banded distribution, mean and median, and the count at or
  above the in-scope threshold: the shortlist.
- **Highest-scoring documents** - the top ten with their English titles.
- **Checks that need no ground truth** - title verification counts, truncation,
  extraction quality and text invariance, each explained in one line.
- **Token usage** - totals, with a note that cost is not captured.
- **Outputs** - where everything landed.

To rebuild it after deleting or re-scoring individual results:

```bash
uv run -m agora_screening.report --output-dir pipelines/agora-screening/output
```

## Comparing two runs

```bash
uv run -m agora_screening.compare \
    --results pipelines/agora-screening/output/results.csv \
    --baseline pipelines/agora-screening/baseline/poc_results_rows1-730_agora-matched.csv
```

Offline, no API calls. Reports the score distribution, title-check counts,
extraction quality, and two checks that need no labelled ground truth:

- **Text invariance** - documents whose source text is byte-identical should
  score identically. Read a spread against the run-to-run noise above: single
  digits could be either, but the corpus contains groups spreading 40 to 78
  points, which noise does not explain. That is the metadata block influencing
  a score the prompt tells the model to take from the text alone.
- **Movement against a baseline** - per-document deltas and how many documents
  crossed the in-scope threshold. Same caveat: the pipeline moves about 2.5
  points per document against *itself*, so that is the floor against which any
  comparison should be read.

## Deviations from the proof of concept

| PoC | Here | Why |
|---|---|---|
| Default sampling temperature | `--temperature 0.0` | Reduces variance. It does not eliminate it - see the reproducibility table above. |
| `--rows 1-5,20,50-60` | `--limit` and `--document-ids` | Matches the sibling pipeline's CLI. Row ranges over an implicit eligible-set ordering were a footgun; IDs are stable. |
| `--max-cost` ceiling in USD | Token counts only | `toolbox` reports tokens but not cost, and OpenRouter only returns cost when sent a request field the shared client does not expose. Worth adding to `toolbox` rather than working around here. |
