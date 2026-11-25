from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class BundleSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_hide_none_type=True,
    cli_prog_name="org_mitigations.bundle",
):
    r"""
    Bundle the mitigations in Airtable, with their quotes and the codes they're
    tagged with, for the reviewer app.

    Needs the AIRTABLE_TOKEN environment variable.

    Example usage:

      uv run python -m org_mitigations.bundle \
        --export-dir /path/to/exports/ \
        --output-path pipelines/org-mitigations/reviewer/public/data/bundle.json
    """

    export_dir: Path = Field(
        default=...,
        description="A folder with companies.csv, documents.csv and passages.csv",
    )
    airtable_base_id: str = Field(
        default="appHrhJQHkZz4c82U",
        description="The Airtable base that holds the export's companies,"
        + " documents and passages",
    )
    output_path: Path = Field(
        default=...,
        description="Where to write the bundle",
    )
