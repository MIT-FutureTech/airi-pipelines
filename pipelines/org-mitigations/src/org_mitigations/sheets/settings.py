from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class SheetsSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_hide_none_type=True,
    cli_prog_name="org_mitigations.sheets",
):
    r"""
    Write companies' excerpts and the LLM's evidence as CSV files, one per
    spreadsheet tab.

    Example usage:

      uv run python -m org_mitigations.sheets \
        --export-dir /path/to/exports/ \
        --excerpt-files /path/to/documents-excerpts.csv \
        --excerpt-files /path/to/companies-excerpts.csv \
        --llm-output-dir /path/to/classifications \
        --company-names "Example Bank" --company-names "Example Retail" \
        --output-dir /path/to/sheets/
    """

    export_dir: Path = Field(
        default=...,
        description="A folder with companies.csv and documents.csv exports",
    )
    excerpt_files: list[Path] = Field(
        default=...,
        description="The excerpt files the LLM read",
    )
    llm_output_dir: Path = Field(
        default=...,
        description="The LLM run's output folder containing JSON files",
    )
    company_names: list[str] = Field(
        default=...,
        description="The companies to include, in the order to list them",
    )
    output_dir: Path = Field(
        default=...,
        description="Where to write the CSV files",
    )
