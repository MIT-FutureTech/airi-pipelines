from enum import StrEnum

from pydantic import BaseModel


class Strength(StrEnum):
    DESCRIBED = "described"
    STATED = "stated"
    REFERENCE = "reference"


class Quote(BaseModel):
    excerpt_number: int
    quote: str
    strength: Strength


class Mitigation(BaseModel):
    name: str
    quotes: list[Quote]
    reasoning: str


class Answer(BaseModel):
    match_id: str
    has_mitigation: bool
    reason: str | None
    mitigations: list[Mitigation]
