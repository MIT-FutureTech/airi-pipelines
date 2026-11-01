from pathlib import Path

from pydantic import BaseModel

TAXONOMY_PATH = (
    Path(__file__).parent.parent.parent / "prompts" / "mitigation_domain_taxonomy.json"
)


class Code(BaseModel):
    code: str
    name: str
    short_name: str
    definition: str
    examples: list[str]


class Locus(BaseModel):
    code: str
    name: str
    short_name: str
    definition: str
    codes: list[Code]


class _Category(BaseModel):
    code: str
    name: str
    short_name: str
    parent: str | None
    definition: str
    key_examples: str


class _TaxonomyFile(BaseModel):
    categories: list[_Category]


_OTHER_CODE_SUFFIXES = (".A", ".C")


def load_taxonomy(path: Path) -> list[Locus]:
    """Read the taxonomy's loci and codes, leaving out the Other codes."""
    taxonomy_file = _TaxonomyFile.model_validate_json(path.read_text())
    loci: dict[str, Locus] = {}
    for category in taxonomy_file.categories:
        if category.parent is None:
            loci[category.code] = Locus(
                code=category.code,
                name=category.name,
                short_name=category.short_name,
                definition=category.definition,
                codes=[],
            )
            continue
        if category.code.endswith(_OTHER_CODE_SUFFIXES):
            continue
        if not category.key_examples:
            raise ValueError(f"Code {category.code} has no examples")
        loci[category.parent].codes.append(
            Code(
                code=category.code,
                name=category.name,
                short_name=category.short_name,
                definition=category.definition,
                examples=category.key_examples.split("; "),
            )
        )
    return list(loci.values())
