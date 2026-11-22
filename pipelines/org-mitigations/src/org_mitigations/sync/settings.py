from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from org_mitigations.settings import DEFAULT_MAX_CHARS


class SyncSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
    cli_hide_none_type=True,
    cli_prog_name="org_mitigations.sync",
):
    r"""
    Count how many of a run's mitigations, their quotes, and the codes they're
    tagged with are already in Airtable.

    Needs the AIRTABLE_TOKEN environment variable.

    Example usage:

      uv run python -m org_mitigations.sync \
        --export-dir /path/to/exports/ \
        --run-dir /path/to/output/ \
        --dry-run
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
    airtable_base_id: str = Field(
        default="appHrhJQHkZz4c82U",
        description="The Airtable base that holds the export's companies,"
        + " documents and passages",
    )
    dry_run: bool = Field(
        default=False,
        description="Build every record and report what would be created,"
        + " without writing to Airtable",
    )
