from enum import StrEnum

from pydantic import BaseModel

from org_mitigations.practice_list import Practice


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
    affiliations: list[Affiliation]


def unlisted_names(answer: Answer, practices: list[Practice]) -> list[str]:
    subtypes_by_practice = {practice.name: practice.subtypes for practice in practices}
    unlisted: list[str] = []
    for tagged in answer.classifications:
        if tagged.practice not in subtypes_by_practice:
            unlisted.append(f"practice {tagged.practice!r}")
            continue
        unlisted.extend(
            f"subtype {subtype!r} of {tagged.practice!r}"
            for subtype in tagged.subtypes
            if subtype not in subtypes_by_practice[tagged.practice]
        )
    return unlisted
