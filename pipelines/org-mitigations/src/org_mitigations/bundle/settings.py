from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from org_mitigations.settings import DEFAULT_MAX_CHARS


class BundleSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_hide_none_type=True,
    cli_prog_name="org_mitigations.bundle",
):
    r"""
    Bundle a run's evidence for the reviewer app.

    Example usage:

      uv run python -m org_mitigations.bundle \
        --export-dir /path/to/exports/ \
        --run-dir /path/to/output/ \
        --prompt-file search.md \
        --temperature 1 \
        --reasoning-effort medium \
        --company-names Amazon --company-names Apple \
        --output-path pipelines/org-mitigations/reviewer/public/data/bundle.json
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
    prompt_file: str = Field(
        default=...,
        description="The name of the prompt file the run used",
    )
    temperature: float = Field(
        default=...,
        description="The temperature the run used",
    )
    reasoning_effort: str = Field(
        default=...,
        description="The reasoning effort the run used",
    )
    company_names: list[str] = Field(
        default=...,
        description="The companies to include",
    )
    output_path: Path = Field(
        default=...,
        description="Where to write the bundle",
    )
