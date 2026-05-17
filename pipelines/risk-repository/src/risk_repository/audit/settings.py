from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

from risk_repository.settings import (
    DEFAULT_AIRTABLE_BASE_ID,
    DEFAULT_AIRTABLE_DOCUMENTS_TABLE,
    DEFAULT_AIRTABLE_TIMEOUT,
    DEFAULT_DOWNLOAD_CACHE_DIR,
)


class AuditSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
    cli_hide_none_type=True,
    cli_prog_name="risk_repository.audit",
):
    """
    Bundle pipeline results and ground truth for the auditor UI.

    Produces a single JSON file that the auditor frontend reads to display
    pipeline decisions alongside source documents and ground truth labels.
    """

    results_dir: Path = Field(
        default=...,
        description="Directory containing pipeline results to audit",
    )
    output_path: Path = Field(
        default=...,
        description="Path to write the audit bundle JSON file",
    )
    download_cache_dir: Path = Field(
        default=DEFAULT_DOWNLOAD_CACHE_DIR,
        description="Directory of cached PDF downloads",
    )
    run_name: str | None = Field(
        default=None,
        description="Optional human-readable name for this pipeline run",
    )
    airtable_timeout: float = Field(
        default=DEFAULT_AIRTABLE_TIMEOUT,
        description="Airtable API timeout in seconds",
    )
    airtable_base_id: str = Field(
        default=DEFAULT_AIRTABLE_BASE_ID,
        description="Airtable ID for the AI Risk Repository base",
    )
    airtable_documents_table: str | None = Field(
        default=None,
        description="""
            Airtable table name to fetch documents from. Mutually exclusive with
            --csv-path.
        """,
    )
    csv_path: Path | None = Field(
        default=None,
        description="""
            Path to a CSV file of documents to process. Mutually exclusive with
            --airtable-documents-table.
        """,
    )
    ground_truth_table: str | None = Field(
        default=DEFAULT_AIRTABLE_DOCUMENTS_TABLE,
        description="""
            Optional Airtable table name with ground-truth screening decisions.
        """,
    )

    @model_validator(mode="after")
    def _validate_input_source(self) -> Self:
        has_airtable = self.airtable_documents_table is not None
        has_csv = self.csv_path is not None
        if has_airtable == has_csv:
            raise ValueError(
                "Provide exactly one of --airtable-documents-table or --csv-path"
            )
        return self
