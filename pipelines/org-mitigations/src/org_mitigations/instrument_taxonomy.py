from pathlib import Path

from pydantic import BaseModel

INSTRUMENT_TAXONOMY_PATH = (
    Path(__file__).parent.parent.parent
    / "prompts"
    / "mitigation_instrument_taxonomy.json"
)


class Instrument(BaseModel):
    code: str
    name: str
    short_name: str
    definition: str
    scope: str | None
    examples: list[str]
    exclusions: str | None


class Modality(BaseModel):
    code: str
    name: str
    instruments: list[Instrument]


class _Category(BaseModel):
    code: str
    name: str
    short_name: str
    parent: str | None
    definition: str
    scope: str
    key_examples: str
    exclusions: str


class _TaxonomyFile(BaseModel):
    categories: list[_Category]


def load_instrument_taxonomy(path: Path) -> list[Modality]:
    taxonomy_file = _TaxonomyFile.model_validate_json(path.read_text())
    modalities: dict[str, Modality] = {}
    for category in taxonomy_file.categories:
        if category.parent is None:
            modalities[category.code] = Modality(
                code=category.code, name=category.name, instruments=[]
            )
        else:
            modalities[category.parent].instruments.append(
                Instrument(
                    code=category.code,
                    name=category.name,
                    short_name=category.short_name,
                    definition=category.definition,
                    scope=category.scope or None,
                    examples=(
                        category.key_examples.split("; ")
                        if category.key_examples
                        else []
                    ),
                    exclusions=category.exclusions or None,
                )
            )
    return list(modalities.values())


def render_instrument_taxonomy(path: Path) -> str:
    taxonomy_file = _TaxonomyFile.model_validate_json(path.read_text())
    modalities: dict[str, list[str]] = {}
    for category in taxonomy_file.categories:
        if category.parent is None:
            modalities[category.code] = [
                f"MODALITY {category.code}: {category.name.upper()}",
                category.definition,
            ]
        else:
            modalities[category.parent].append(_render_instrument(category))
    return "\n\n".join("\n".join(lines) for lines in modalities.values())


def _render_instrument(category: _Category) -> str:
    line = f"- {category.code}: {category.name} — {category.definition}"
    if category.scope:
        line += f" Scope: {category.scope}"
    if category.key_examples:
        line += f" Examples: {category.key_examples}."
    if category.exclusions:
        line += f" ({category.exclusions})"
    return line
