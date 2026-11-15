import logging

from pydantic import BaseModel

from org_mitigations.bundle.run import Run
from org_mitigations.companies import Company
from org_mitigations.documents import Document
from org_mitigations.evidence import Evidence
from org_mitigations.excerpts import Excerpt
from org_mitigations.locate import Span, locate_quote
from org_mitigations.taxonomy import Locus

logger = logging.getLogger(__name__)


class LocatedEvidence(Evidence):
    location: Span | None


class Bundle(BaseModel):
    run: Run
    taxonomy: list[Locus]
    companies: list[Company]
    documents: list[Document]
    excerpts: list[Excerpt]
    evidence: list[LocatedEvidence]


def assemble_bundle(
    *,
    company_names: list[str],
    run: Run,
    taxonomy: list[Locus],
    companies: list[Company],
    documents: list[Document],
    excerpts: list[Excerpt],
    evidence: list[Evidence],
) -> Bundle:
    companies_by_name = {company.name: company for company in companies}
    selected_companies = [companies_by_name[name] for name in company_names]
    company_ids = {company.company_id for company in selected_companies}

    excerpted_document_ids = {excerpt.document_id for excerpt in excerpts}
    selected_documents = [
        document
        for document in documents
        if document.company_id in company_ids
        and document.document_id in excerpted_document_ids
    ]
    document_ids = {document.document_id for document in selected_documents}

    excerpts_by_id = {excerpt.excerpt_id: excerpt for excerpt in excerpts}
    located_evidence: list[LocatedEvidence] = []
    for item in evidence:
        if item.document_id not in document_ids:
            continue
        excerpt = excerpts_by_id[item.excerpt_id]
        location = locate_quote(item.quote, excerpt.text)
        located_evidence.append(LocatedEvidence(**item.model_dump(), location=location))
    located = sum(item.location is not None for item in located_evidence)
    logger.info(f"Located {located} of {len(located_evidence)} quotes")

    used_excerpt_ids = {item.excerpt_id for item in located_evidence}
    return Bundle(
        run=run,
        taxonomy=taxonomy,
        companies=selected_companies,
        documents=selected_documents,
        excerpts=[
            excerpt for excerpt in excerpts if excerpt.excerpt_id in used_excerpt_ids
        ],
        evidence=located_evidence,
    )
