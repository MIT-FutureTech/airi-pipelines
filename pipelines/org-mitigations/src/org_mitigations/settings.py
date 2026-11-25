from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class BundleSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_hide_none_type=True,
    cli_prog_name="org_mitigations",
):
    r"""
    Bundle an LLM run's evidence for the reviewer app.

    Example usage:

      uv run python -m org_mitigations \
        --taxonomy-file /path/to/taxonomy.json \
        --export-dir /path/to/exports/ \
        --excerpt-files /path/to/documents-excerpts.csv \
        --excerpt-files /path/to/companies-excerpts.csv \
        --llm-output-dir /path/to/classifications \
        --temperature 1 \
        --reasoning-effort medium \
        --company-names Amazon --company-names Apple \
        --output-path pipelines/org-mitigations/reviewer/public/data/bundle.json
    """

    taxonomy_file: Path = Field(
        default=...,
        description="The mitigation taxonomy file in JSON format",
    )
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
    temperature: float = Field(
        default=...,
        description="The temperature the LLM run used",
    )
    reasoning_effort: str = Field(
        default=...,
        description="The reasoning effort the LLM run used",
    )
    company_names: list[str] = Field(
        default=...,
        description="The companies to include",
    )
    output_path: Path = Field(
        default=...,
        description="Where to write the bundle",
    )
