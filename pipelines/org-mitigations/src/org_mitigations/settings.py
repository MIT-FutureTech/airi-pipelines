from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from toolbox.llm import ReasoningEffort

_PIPELINE_DIR = Path(__file__).parent.parent.parent


class PipelineSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
    cli_hide_none_type=True,
    cli_prog_name="org_mitigations",
):
    r"""
    Ask an LLM which mitigations each company's documents describe, with quotes
    as evidence.

    Example usage:

      uv run --env-file=.env python -m org_mitigations \
        --export-dir /path/to/exports/ \
        --output-dir /path/to/output/ \
        --company-names "Example Bank" --company-names "Example Retail"
    """

    export_dir: Path = Field(
        default=...,
        description="A folder with companies.csv, documents.csv and passages.csv",
    )
    output_dir: Path = Field(
        default=...,
        description="Where to write each call's result and log.txt",
    )
    company_names: list[str] | None = Field(
        default=None,
        description="The companies to include. Default: every company",
    )
    prompt_path: Path = Field(
        default=_PIPELINE_DIR / "prompts" / "search_v1.0.md",
        description="The prompt template",
    )
    model: str = Field(
        default="google/gemini-3.5-flash",
        description="The LLM to call",
    )
    temperature: float = Field(
        default=1.0,
        description="Sampling temperature",
    )
    reasoning_effort: ReasoningEffort = Field(
        default="medium",
        description="How much the LLM reasons before answering",
    )
    max_chars: int = Field(
        default=75_000,
        description="""
            Most characters of excerpts in one call. A company's documents are
            split into groups that fit.
        """,
    )
    output_token_limit: int = Field(
        default=8_000,
        description="Most tokens in one answer",
    )
    concurrency: int = Field(
        default=5,
        description="Maximum number of calls at once",
    )
    llm_rate_limit_rps: float = Field(
        default=5.0,
        description="LLM API rate limit in requests per second",
    )
    llm_timeout: float = Field(
        default=120.0,
        description="LLM API timeout in seconds",
    )
    dry_run: bool = Field(
        default=False,
        description="Print the prompts and count the calls without calling the LLM",
    )
