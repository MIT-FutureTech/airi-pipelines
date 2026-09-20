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

Scaffold only. The scoring logic is being ported from a proof of concept
(`docs/poc-report.md`) onto the shared `toolbox` library.

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

Not yet runnable. Once the port lands, from the repository root:

```bash
uv run --env-file=.env -m agora_screening --output-dir pipelines/agora-screening/output/
```

Needs `OPENROUTER_API_KEY` in the repository-root `.env`. The PoC's full
730-document run cost $2.61 and took under six minutes.
