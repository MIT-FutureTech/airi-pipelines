from pathlib import Path

from pydantic import BaseModel

INSTRUMENT_TAXONOMY_PATH = (
    Path(__file__).parent.parent.parent
    / "prompts"
    / "mitigation_instrument_taxonomy.json"
)


class _Category(BaseModel):
    code: str
    name: str
    parent: str | None
    definition: str
    scope: str
    key_examples: str
    exclusions: str


class _TaxonomyFile(BaseModel):
    categories: list[_Category]


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
