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

It runs. A five-document sample on `google/gemini-3.8-flash` scored 5 of 5,
verified every title against the source text, and moved a mean of 3.2 points
against the proof of concept's scores for the same documents, with no document
crossing the in-scope threshold. That is a different model as well as different
code, so it is corroboration rather than proof, and it is only five documents.

**The full 730-document regression run has not been done.** Until it has, the
port is unproven at corpus scale.

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

The default is `google/gemini-3.8-flash` at temperature 0.

Budget about **$9 for a full 730-document run**, measured from a five-document
sample at 10,800 input and 1,130 output tokens per document. The proof of
concept cost $2.61 on `google/gemini-3.5-flash-lite`, and almost all of the
difference is output tokens: it averaged about 150 per document against this
model's 1,130, which at $3.75 per million output tokens is where the money
goes. Passing `--model google/gemini-3.5-flash-lite` reproduces the cheaper
configuration.

Results are one JSON file per document under `output/score/`. A second run skips
documents already scored, so an interrupted run resumes; `--force` rescores. To
re-run a handful after a rubric change, delete their JSON files or pass
`--document-ids ID_0002,ID_0005`.

## Reporting on a run

```bash
uv run -m agora_screening.compare \
    --results pipelines/agora-screening/output/results.csv \
    --baseline pipelines/agora-screening/baseline/poc_results_rows1-730_agora-matched.csv
```

Offline, no API calls. Reports the score distribution, title-check counts,
extraction quality, and two checks that need no labelled ground truth:

- **Text invariance** - documents whose source text is byte-identical must score
  identically. Any spread is metadata influencing the score.
- **Movement against a baseline** - per-document deltas and, in particular, how
  many documents crossed the in-scope threshold. This is the regression gate for
  the port: same rubric and same model should move very few.

## Deviations from the proof of concept

| PoC | Here | Why |
|---|---|---|
| Default sampling temperature | `--temperature 0.0` | A document must score the same on re-run, or the invariance check measures sampling noise rather than metadata leakage. |
| `--rows 1-5,20,50-60` | `--limit` and `--document-ids` | Matches the sibling pipeline's CLI. Row ranges over an implicit eligible-set ordering were a footgun; IDs are stable. |
| `--max-cost` ceiling in USD | Token counts only | `toolbox` reports tokens but not cost, and OpenRouter only returns cost when sent a request field the shared client does not expose. Worth adding to `toolbox` rather than working around here. |
