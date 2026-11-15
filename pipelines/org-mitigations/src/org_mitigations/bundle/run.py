from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel

from org_mitigations.search.calls import SearchResult


class Run(BaseModel):
    prompt_file: str
    model: str
    temperature: float
    reasoning_effort: str


class _Metadata(BaseModel, frozen=True):
    prompt_file: str
    llm_model: str


class _LLMOutput(BaseModel):
    metadata: _Metadata


def load_run(llm_output_dir: Path, *, temperature: float, reasoning_effort: str) -> Run:
    settings: set[_Metadata] = set()
    for path in llm_output_dir.glob("*.json"):
        output = _LLMOutput.model_validate_json(path.read_text())
        settings.add(output.metadata)
    if len(settings) != 1:
        raise ValueError(
            f"Expected one prompt and model in {llm_output_dir}, found {settings}"
        )
    metadata = settings.pop()
    return Run(
        prompt_file=metadata.prompt_file,
        model=metadata.llm_model,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
    )


def single_model(results: Mapping[str, SearchResult]) -> str:
    models = {result.model for result in results.values()}
    if len(models) != 1:
        raise ValueError(f"Expected one model in the results, found {sorted(models)}")
    return models.pop()
