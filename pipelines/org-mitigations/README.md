# Organization Mitigations

A project to understand how organizations are mitigating risks from AI

## Methodology

Excerpts from corporate documents are shown to an LLM, which searches them for
evidence of each mitigation type in the taxonomy. Each mitigation it finds is
then shown to an LLM again, with its quotes, to tag it with practices from a
fixed list (`prompts/practice_list.json`). Separately, an LLM classifies each
mitigation by its instrument, the lever it uses to create change
(`prompts/mitigation_instrument_taxonomy.json`), with the other mitigations
found in the same documents as context.

## Running the pipeline

The pipeline runs in stages: `search`, then `practices` and `instruments`.
`--stages` says which to run; the practices and instruments stages read the
search's results from the same output folder. See `uv run python -m org_mitigations --help` for the arguments and
options.

The pipeline needs the `OPENROUTER_API_KEY` environment variable to be set.

## Bundling evidence for the reviewer

The reviewer app reads its data from a JSON file which the Python code can
compile. See `uv run python -m org_mitigations.bundle --help`.

## Exporting evidence for a spreadsheet

The Python code can also write companies' excerpts, the LLM's evidence, the
mitigations it found with their practices, and the bodies and commitments the
mitigations name, as CSV files, one per spreadsheet tab. Unlike the bundle, they include every excerpt the LLM read, including those
it found no evidence in. The run needs results from both stages. See
`uv run python -m org_mitigations.sheets --help`.
