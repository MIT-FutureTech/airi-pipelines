import logging
from collections.abc import Mapping

from pydantic import BaseModel

from org_mitigations.bundle.synced import SyncedCode, SyncedMitigation, SyncedQuote
from org_mitigations.companies import Company
from org_mitigations.documents import Document
from org_mitigations.excerpts import Excerpt
from org_mitigations.locate import Span, locate_quote
from org_mitigations.search.answer import Strength
from org_mitigations.sync.codes import Taxonomy
from org_mitigations.sync.mitigations import Status

logger = logging.getLogger(__name__)


class BundleQuote(BaseModel):
    evidence_id: str
    mitigation_record_id: str
    document_id: str
    excerpt_id: str
    quote: str
    strength: Strength
    location: Span | None


class Bundle(BaseModel):
    codes: list[SyncedCode]
    companies: list[Company]
    documents: list[Document]
    excerpts: list[Excerpt]
    mitigations: list[SyncedMitigation]
    quotes: list[BundleQuote]


def build_bundle(
    *,
    codes: list[SyncedCode],
    mitigations: list[SyncedMitigation],
    quotes: list[SyncedQuote],
    companies: list[Company],
    documents: list[Document],
    excerpts: list[Excerpt],
    document_ids_by_record_id: Mapping[str, str],
    passage_ids_by_record_id: Mapping[str, str],
) -> Bundle:
    current = sorted(
        (
            mitigation
            for mitigation in mitigations
            if mitigation.status == Status.CURRENT
        ),
        key=lambda mitigation: mitigation.mitigation_id,
    )
    company_ids = {mitigation.company_id for mitigation in current}
    unknown_company_ids = company_ids - {company.company_id for company in companies}
    if unknown_company_ids:
        raise ValueError(
            f"Mitigations name companies the export doesn't have: {sorted(unknown_company_ids)}"
        )

    current_record_ids = {mitigation.record_id for mitigation in current}
    excerpts_by_passage_id = {
        passage_id: excerpt
        for excerpt in excerpts
        for passage_id in excerpt.passage_ids
    }
    bundle_quotes = [
        _bundle_quote(
            quote,
            excerpts_by_passage_id=excerpts_by_passage_id,
            document_ids_by_record_id=document_ids_by_record_id,
            passage_ids_by_record_id=passage_ids_by_record_id,
        )
        for quote in sorted(quotes, key=lambda quote: quote.evidence_id)
        if quote.mitigation_record_id in current_record_ids
    ]
    located = sum(quote.location is not None for quote in bundle_quotes)
    logger.info(f"Located {located} of {len(bundle_quotes)} quotes")

    document_ids = {quote.document_id for quote in bundle_quotes}
    excerpt_ids = {quote.excerpt_id for quote in bundle_quotes}
    taxonomies = list(Taxonomy)
    return Bundle(
        codes=sorted(
            codes, key=lambda code: (taxonomies.index(code.taxonomy), code.order)
        ),
        companies=sorted(
            (company for company in companies if company.company_id in company_ids),
            key=lambda company: company.name,
        ),
        documents=[
            document for document in documents if document.document_id in document_ids
        ],
        excerpts=[excerpt for excerpt in excerpts if excerpt.excerpt_id in excerpt_ids],
        mitigations=current,
        quotes=bundle_quotes,
    )


def _bundle_quote(
    quote: SyncedQuote,
    *,
    excerpts_by_passage_id: Mapping[str, Excerpt],
    document_ids_by_record_id: Mapping[str, str],
    passage_ids_by_record_id: Mapping[str, str],
) -> BundleQuote:
    quote_excerpts = {
        excerpt.excerpt_id: excerpt
        for excerpt in (
            excerpts_by_passage_id[passage_ids_by_record_id[record_id]]
            for record_id in quote.passage_record_ids
        )
    }
    if len(quote_excerpts) != 1:
        raise ValueError(
            f"Quote {quote.evidence_id}'s passages are in {len(quote_excerpts)}"
            + " excerpts, not one"
        )
    [excerpt] = quote_excerpts.values()
    document_id = document_ids_by_record_id[quote.document_record_id]
    if excerpt.document_id != document_id:
        raise ValueError(
            f"Quote {quote.evidence_id} is from {document_id},"
            + f" but its passages are from {excerpt.document_id}"
        )
    return BundleQuote(
        evidence_id=quote.evidence_id,
        mitigation_record_id=quote.mitigation_record_id,
        document_id=document_id,
        excerpt_id=excerpt.excerpt_id,
        quote=quote.quote,
        strength=quote.strength,
        location=locate_quote(quote.quote, excerpt.text),
    )
