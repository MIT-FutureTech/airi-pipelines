from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from org_mitigations.excerpts import excerpt_id


class Strength(StrEnum):
    DESCRIBED = "described"
    STATED = "stated"
    REFERENCE = "reference"


class Evidence(BaseModel):
    document_id: str
    code: str
    mitigation: str
    quote: str
    strength: Strength
    excerpt_id: str


class _Quote(BaseModel):
    excerpt: int
    quote: str
    strength: Strength


class _Mitigation(BaseModel):
    mitigation: str
    evidence: list[_Quote]


class _Result(BaseModel):
    classifications: list[_Mitigation]


class _Input(BaseModel):
    match_id: str
    document_id: str
    code: str


class _LLMOutput(BaseModel):
    input: _Input
    result: _Result


def load_evidence(llm_output_dir: Path) -> list[Evidence]:
    evidence: list[Evidence] = []
    for path in sorted(llm_output_dir.glob("*.json")):
        output = _LLMOutput.model_validate_json(path.read_text())
        match_id = output.input.match_id.removesuffix(f"__{output.input.code}")
        evidence.extend(
            Evidence(
                document_id=output.input.document_id,
                code=output.input.code,
                mitigation=mitigation.mitigation,
                quote=quote.quote,
                strength=quote.strength,
                excerpt_id=excerpt_id(match_id, quote.excerpt),
            )
            for mitigation in output.result.classifications
            for quote in mitigation.evidence
        )
    return evidence
