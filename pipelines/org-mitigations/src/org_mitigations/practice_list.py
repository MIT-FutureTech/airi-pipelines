from collections import Counter
from pathlib import Path

from pydantic import BaseModel

PRACTICE_LIST_PATH = (
    Path(__file__).parent.parent.parent / "prompts" / "practice_list.json"
)


class Practice(BaseModel):
    name: str
    definition: str
    counts: list[str]
    does_not_count: list[str]
    subtypes: list[str]


class _PracticeListFile(BaseModel):
    practices: list[Practice]


def load_practice_list(path: Path) -> list[Practice]:
    practices = _PracticeListFile.model_validate_json(path.read_text()).practices
    repeated = [
        name
        for name, count in Counter(practice.name for practice in practices).items()
        if count > 1
    ]
    if repeated:
        raise ValueError(f"Practices named more than once: {repeated}")
    return practices


def render_practice_list(practices: list[Practice]) -> str:
    return "\n".join(_render_practice(practice) for practice in practices)


def _render_practice(practice: Practice) -> str:
    lines = [
        f"- {practice.name}: {practice.definition}",
        f"  Counts: {' '.join(practice.counts)}",
        f"  Does not count: {' '.join(practice.does_not_count)}",
    ]
    if practice.subtypes:
        lines.append(f"  Subtypes: {'; '.join(practice.subtypes)}")
    return "\n".join(lines)
