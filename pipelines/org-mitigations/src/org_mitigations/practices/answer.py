from enum import StrEnum

from pydantic import BaseModel

from org_mitigations.practice_list import Practice


class Relation(StrEnum):
    SIGNED = "signed"
    MEMBER = "member"


class TaggedPractice(BaseModel):
    name: str
    subtypes: list[str]
    quote_numbers: list[int]
    reasoning: str


class Affiliation(BaseModel):
    name: str
    relation: Relation
    quote_numbers: list[int]


class Answer(BaseModel):
    match_id: str
    tagged_practices: list[TaggedPractice]
    affiliations: list[Affiliation]


def unlisted_names(answer: Answer, practices: list[Practice]) -> list[str]:
    subtypes_by_practice = {practice.name: practice.subtypes for practice in practices}
    unlisted: list[str] = []
    for tagged in answer.tagged_practices:
        if tagged.name not in subtypes_by_practice:
            unlisted.append(f"practice {tagged.name!r}")
            continue
        unlisted.extend(
            f"subtype {subtype!r} of {tagged.name!r}"
            for subtype in tagged.subtypes
            if subtype not in subtypes_by_practice[tagged.name]
        )
    return unlisted
