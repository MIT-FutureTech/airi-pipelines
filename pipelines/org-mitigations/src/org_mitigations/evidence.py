from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from org_mitigations.excerpts import excerpt_id


class Strength(StrEnum):
    DESCRIBED = "described"
    STATED = "stated"
    REFERENCE = "reference"


class Evidence(BaseModel):
    evidence_id: str
    mitigation_id: str
    document_id: str
    code: str
    mitigation: str
    reasoning: str
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
    reasoning: str


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
        for mitigation_number, mitigation in enumerate(
            output.result.classifications, start=1
        ):
            mitigation_id = f"{output.input.match_id}__{mitigation_number}"
            evidence.extend(
                Evidence(
                    evidence_id=f"{mitigation_id}.{quote_number}",
                    mitigation_id=mitigation_id,
                    document_id=output.input.document_id,
                    code=output.input.code,
                    mitigation=mitigation.mitigation,
                    reasoning=mitigation.reasoning,
                    quote=quote.quote,
                    strength=quote.strength,
                    excerpt_id=excerpt_id(match_id, quote.excerpt),
                )
                for quote_number, quote in enumerate(mitigation.evidence, start=1)
            )
    return evidence
