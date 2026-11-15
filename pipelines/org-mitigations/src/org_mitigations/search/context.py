from collections import defaultdict
from itertools import groupby

from pydantic import BaseModel

from org_mitigations.documents import Document
from org_mitigations.excerpts import Excerpt
from org_mitigations.search.grouping import group_excerpts


class Context(BaseModel):
    context_id: str
    company_id: str
    text: str
    excerpt_ids: list[str]


def build_contexts(
    excerpts: list[Excerpt],
    documents: list[Document],
    *,
    max_chars: int,
) -> list[Context]:
    documents_by_id = {document.document_id: document for document in documents}
    by_company: defaultdict[str, list[Excerpt]] = defaultdict(list)
    for excerpt in excerpts:
        company_id = documents_by_id[excerpt.document_id].company_id
        by_company[company_id].append(excerpt)

    contexts: list[Context] = []
    companies_by_prefix: dict[str, str] = {}
    for company_id, company_excerpts in by_company.items():
        prefix = _document_id_prefix(company_excerpts)
        if prefix in companies_by_prefix:
            raise ValueError(
                f"Companies {companies_by_prefix[prefix]} and {company_id} both have"
                + f" documents named {prefix}"
            )
        companies_by_prefix[prefix] = company_id
        groups = group_excerpts(company_excerpts, max_chars=max_chars)
        for number, group in enumerate(groups, start=1):
            context_id = prefix if len(groups) == 1 else f"{prefix}_group{number}"
            contexts.append(
                Context(
                    context_id=context_id,
                    company_id=company_id,
                    text=_render(group, documents_by_id),
                    excerpt_ids=[excerpt.excerpt_id for excerpt in group],
                )
            )
    return contexts


def _document_id_prefix(excerpts: list[Excerpt]) -> str:
    prefixes = {excerpt.document_id.rsplit("_", 1)[0] for excerpt in excerpts}
    if len(prefixes) != 1:
        raise ValueError(
            f"A company's documents have several names: {sorted(prefixes)}"
        )
    return prefixes.pop()


def _render(excerpts: list[Excerpt], documents_by_id: dict[str, Document]) -> str:
    blocks: list[str] = []
    number = 0
    for document_id, document_excerpts in groupby(
        excerpts, key=lambda excerpt: excerpt.document_id
    ):
        document = documents_by_id[document_id]
        lines: list[str] = []
        for excerpt in document_excerpts:
            number += 1
            lines.append(f'<excerpt id="{number}">[...] {excerpt.text} [...]</excerpt>')
        blocks.append(
            f'<document id="{document_id}">\n'
            + f"<doc_type>{document.doc_type}</doc_type>\n"
            + f"<title>{document.title}</title>\n"
            + "<excerpts>\n"
            + "\n".join(lines)
            + "\n</excerpts>\n</document>"
        )
    return "\n".join(blocks)
