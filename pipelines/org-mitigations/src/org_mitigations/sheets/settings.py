from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from org_mitigations.settings import DEFAULT_MAX_CHARS


class SheetsSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_hide_none_type=True,
    cli_prog_name="org_mitigations.sheets",
):
    r"""
    Write companies' excerpts, the LLM's evidence, the mitigations it found
    with their practices, and the bodies and commitments the mitigations name,
    as CSV files, one per spreadsheet tab.

    Example usage:

      uv run python -m org_mitigations.sheets \
        --export-dir /path/to/exports/ \
        --run-dir /path/to/output/ \
        --company-names "Example Bank" --company-names "Example Retail" \
        --output-dir /path/to/sheets/
    """

    export_dir: Path = Field(
        default=...,
        description="A folder with companies.csv, documents.csv and passages.csv",
    )
    run_dir: Path = Field(
        default=...,
        description="The run's output folder, which the pipeline's --output-dir named",
    )
    max_chars: int = Field(
        default=DEFAULT_MAX_CHARS,
        description="The --max-chars the run used",
    )
    company_names: list[str] | None = Field(
        default=None,
        description="The companies to include, in the order to list them."
        + " Default: every company, by name",
    )
    output_dir: Path = Field(
        default=...,
        description="Where to write the CSV files",
    )
