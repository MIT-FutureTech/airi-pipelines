from pathlib import Path

from pydantic import BaseModel

from org_mitigations.companies import Company, load_companies
from org_mitigations.documents import Document, load_documents
from org_mitigations.excerpts import Excerpt, merge_passages
from org_mitigations.passages import load_passages


class Corpus(BaseModel):
    companies: list[Company]
    documents: list[Document]
    excerpts: list[Excerpt]


def load_corpus(
    export_dir: Path,
    *,
    company_names: list[str] | None,
) -> Corpus:
    companies = _select_companies(load_companies(export_dir), company_names)
    company_ids = {company.company_id for company in companies}
    documents = [
        document
        for document in load_documents(export_dir)
        if document.company_id in company_ids
    ]
    document_ids = {document.document_id for document in documents}
    passages = [
        passage
        for passage in load_passages(export_dir)
        if passage.document_id in document_ids
    ]
    return Corpus(
        companies=companies,
        documents=documents,
        excerpts=merge_passages(passages),
    )


def _select_companies(
    all_companies: list[Company],
    selected_names: list[str] | None,
) -> list[Company]:
    if selected_names is None:
        return all_companies
    companies_by_name = {company.name: company for company in all_companies}
    unknown = [name for name in selected_names if name not in companies_by_name]
    if unknown:
        raise ValueError(f"No companies named {unknown}")
    return [companies_by_name[name] for name in selected_names]
