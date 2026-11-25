from collections.abc import Mapping

from pydantic import BaseModel

from org_mitigations.search.calls import SearchResult


class RunSettings(BaseModel):
    prompt_file: str
    model: str
    temperature: float
    reasoning_effort: str


def single_model(results: Mapping[str, SearchResult]) -> str:
    models = {result.model for result in results.values()}
    if len(models) != 1:
        raise ValueError(f"Expected one model in the results, found {sorted(models)}")
    return models.pop()
