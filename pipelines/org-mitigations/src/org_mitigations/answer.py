from enum import StrEnum

from pydantic import BaseModel


class Strength(StrEnum):
    DESCRIBED = "described"
    STATED = "stated"
    REFERENCE = "reference"


class Quote(BaseModel):
    excerpt: int
    quote: str
    strength: Strength


class Mitigation(BaseModel):
    mitigation: str
    evidence: list[Quote]
    reasoning: str


class Answer(BaseModel):
    match_id: str
    has_mitigation: bool
    reason: str | None
    classifications: list[Mitigation]
