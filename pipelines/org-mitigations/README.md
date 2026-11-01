# Organization Mitigations

A project to understand how organizations are mitigating risks from AI

## Methodology

Excerpts from corporate documents are shown to an LLM, which searches them for
evidence of each mitigation type in the taxonomy.

## Running the pipeline

See `uv run python -m org_mitigations --help` for the arguments and options.

The pipeline needs the `OPENROUTER_API_KEY` environment variable to be set.

## Bundling evidence for the reviewer

The reviewer app reads its data from a JSON file which the Python code can
compile. See `uv run python -m org_mitigations.bundle --help`.

## Exporting evidence for a spreadsheet

The Python code can also write companies' excerpts and the LLM's evidence as
CSV files, one per spreadsheet tab. Unlike the bundle, they include every
excerpt the LLM read, including those it found no evidence in. See
`uv run python -m org_mitigations.sheets --help`.
