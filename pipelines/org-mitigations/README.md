# Organization Mitigations

A project to understand how organizations are mitigating risks from AI

## Bundling evidence for the reviewer

The reviewer app reads its data from a JSON file which the Python code can
compile. See `uv run python -m org_mitigations.bundle --help`.

## Exporting evidence for a spreadsheet

The Python code can also write companies' excerpts and the LLM's evidence as
CSV files, one per spreadsheet tab. Unlike the bundle, they include every
excerpt the LLM read, including those it found no evidence in. See
`uv run python -m org_mitigations.sheets --help`.
