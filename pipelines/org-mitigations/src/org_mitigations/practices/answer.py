from enum import StrEnum

from pydantic import BaseModel


class Relation(StrEnum):
    SIGNED = "signed"
    MEMBER = "member"


class TaggedPractice(BaseModel):
    practice: str
    subtypes: list[str]
    quotes: list[int]
    reasoning: str


class Affiliation(BaseModel):
    name: str
    relation: Relation
    quotes: list[int]


class Answer(BaseModel):
    match_id: str
    classifications: list[TaggedPractice]
    named: list[Affiliation]
