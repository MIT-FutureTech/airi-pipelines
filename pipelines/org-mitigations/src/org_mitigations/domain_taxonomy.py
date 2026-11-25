from pathlib import Path

from pydantic import BaseModel

DOMAIN_TAXONOMY_PATH = (
    Path(__file__).parent.parent.parent / "prompts" / "mitigation_domain_taxonomy.json"
)


class Domain(BaseModel):
    code: str
    name: str
    short_name: str
    definition: str
    boundary_question: str
    examples: list[str]
    exclusions: str | None


class Locus(BaseModel):
    code: str
    name: str
    short_name: str
    definition: str
    domains: list[Domain]


class _Category(BaseModel):
    code: str
    name: str
    short_name: str
    parent: str | None
    definition: str
    boundary_question: str
    key_examples: str
    exclusions: str


class _TaxonomyFile(BaseModel):
    categories: list[_Category]


_OTHER_CODE_SUFFIXES = (".A", ".C")


def load_domain_taxonomy(path: Path) -> list[Locus]:
    """Read the taxonomy's loci and domains, leaving out the Other domains."""
    taxonomy_file = _TaxonomyFile.model_validate_json(path.read_text())
    loci: dict[str, Locus] = {}
    for category in taxonomy_file.categories:
        if category.parent is None:
            loci[category.code] = Locus(
                code=category.code,
                name=category.name,
                short_name=category.short_name,
                definition=category.definition,
                domains=[],
            )
            continue
        if category.code.endswith(_OTHER_CODE_SUFFIXES):
            continue
        if not category.boundary_question:
            raise ValueError(f"Domain {category.code} has no boundary question")
        if not category.key_examples:
            raise ValueError(f"Domain {category.code} has no examples")
        loci[category.parent].domains.append(
            Domain(
                code=category.code,
                name=category.name,
                short_name=category.short_name,
                definition=category.definition,
                boundary_question=category.boundary_question,
                examples=category.key_examples.split("; "),
                exclusions=category.exclusions or None,
            )
        )
    return list(loci.values())


def render_domain_taxonomy(path: Path) -> str:
    taxonomy_file = _TaxonomyFile.model_validate_json(path.read_text())
    loci: dict[str, list[str]] = {}
    for category in taxonomy_file.categories:
        if category.parent is None:
            loci[category.code] = [
                f"LOCUS {category.code}: {category.name.upper()}",
                f"{category.definition} Boundary question: {category.boundary_question}",
            ]
        else:
            loci[category.parent].append(_render_code(category))
    return "\n\n".join("\n".join(lines) for lines in loci.values())


def _render_code(category: _Category) -> str:
    line = f"- {category.code}: {category.name} — {category.definition}"
    if category.boundary_question:
        line += f" {category.boundary_question}"
    if category.key_examples:
        line += f" Examples: {category.key_examples}."
    if category.exclusions:
        line += f" ({category.exclusions})"
    return line
