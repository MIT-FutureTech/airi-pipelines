# Risk Repository

This is the LLM pipeline for the [AI Risk Repository](https://airisk.mit.edu/).
It screens academic papers for relevance, extracts individual AI risk
descriptions, and classifies those risks.

## Running

First, make sure you've done [the one-time setup instructions](/README.md#setup).

Then from the root folder of the repository, run

```bash
uv run --env-file=.env -m risk_repository
```

Use `--help` to list the available options.

## Evaluation

The evaluator compares the pipeline output against manually curated ground
truth. It reports several metrics, including precision and recall.

To evaluate pipeline results against ground truth:

```bash
uv run --env-file=.env -m risk_repository.evaluate
```

Use `--help` to list the available options.
