from pathlib import Path

from pydantic import BaseModel


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
    name: str
    short: str
    definition: str
    examples: list[str] | None = None


class _Mitdom(BaseModel):
    categories: dict[str, _Category]


class _Taxonomies(BaseModel):
    mitdom: _Mitdom


class _TaxonomyFile(BaseModel):
    taxonomies: _Taxonomies


def load_taxonomy(path: Path) -> list[Locus]:
    taxonomy_file = _TaxonomyFile.model_validate_json(path.read_text())
    loci: dict[str, Locus] = {}
    for code, category in taxonomy_file.taxonomies.mitdom.categories.items():
        if "." not in code:
            loci[code] = Locus(
                code=code,
                name=category.name,
                short_name=category.short,
                definition=category.definition,
                codes=[],
            )
            continue
        if category.examples is None:
            raise ValueError(f"Code {code} has no examples")
        locus_code = code.split(".")[0]
        loci[locus_code].codes.append(
            Code(
                code=code,
                name=category.name,
                short_name=category.short,
                definition=category.definition,
                examples=category.examples,
            )
        )
    return list(loci.values())
