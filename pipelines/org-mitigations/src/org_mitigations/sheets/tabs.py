import csv
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, Field

from org_mitigations.companies import Company
from org_mitigations.documents import DatePrecision, Document
from org_mitigations.domain_taxonomy import Locus
from org_mitigations.evidence import Evidence
from org_mitigations.excerpts import Excerpt
from org_mitigations.instrument_taxonomy import Modality
from org_mitigations.instruments.calls import InstrumentsResult
from org_mitigations.locate import locate_quote
from org_mitigations.practices.answer import Affiliation, Relation
from org_mitigations.practices.calls import PracticesResult
from org_mitigations.search.answer import Strength
from org_mitigations.search.mitigations import FoundMitigation


class ExcerptRow(BaseModel):
    excerpt_id: str = Field(serialization_alias="Excerpt ID")
    company: str = Field(serialization_alias="Company")
    document_id: str = Field(serialization_alias="Document ID")
    document_title: str = Field(serialization_alias="Document title")
    document_type: str = Field(serialization_alias="Document type")
    document_date: str = Field(serialization_alias="Document date")
    document_link: str = Field(serialization_alias="Document link")
    order_in_document: int = Field(serialization_alias="Order in document")
    passage_ids: str = Field(serialization_alias="Passage IDs")
    text: str = Field(serialization_alias="Text")


class EvidenceRow(BaseModel):
    evidence_id: str = Field(serialization_alias="Evidence ID")
    mitigation_id: str = Field(serialization_alias="Mitigation ID")
    company: str = Field(serialization_alias="Company")
    document_id: str = Field(serialization_alias="Document ID")
    excerpt_id: str = Field(serialization_alias="Excerpt ID")
    domain_code: str = Field(serialization_alias="Domain code")
    domain_name: str = Field(serialization_alias="Domain name")
    mitigation_name: str = Field(serialization_alias="Mitigation")
    strength: Strength = Field(serialization_alias="Strength")
    quote: str = Field(serialization_alias="Quote")
    quote_start: int | None = Field(serialization_alias="Quote start")
    quote_end: int | None = Field(serialization_alias="Quote end")
    search_reasoning: str = Field(serialization_alias="Search reasoning")


class MitigationRow(BaseModel):
    mitigation_id: str = Field(serialization_alias="Mitigation ID")
    company: str = Field(serialization_alias="Company")
    sector: str = Field(serialization_alias="Sector")
    domain_code: str = Field(serialization_alias="Domain code")
    domain_name: str = Field(serialization_alias="Domain name")
    mitigation_name: str = Field(serialization_alias="Mitigation")
    search_reasoning: str = Field(serialization_alias="Search reasoning")
    quotes: str = Field(serialization_alias="Quotes")
    practices: str = Field(serialization_alias="Practices")
    instrument_code: str = Field(serialization_alias="Instrument code")
    instrument_name: str = Field(serialization_alias="Instrument name")
    instrument_reasoning: str = Field(serialization_alias="Instrument reasoning")


class PracticeRow(BaseModel):
    mitigation_id: str = Field(serialization_alias="Mitigation ID")
    company: str = Field(serialization_alias="Company")
    sector: str = Field(serialization_alias="Sector")
    domain_code: str = Field(serialization_alias="Domain code")
    domain_name: str = Field(serialization_alias="Domain name")
    mitigation_name: str = Field(serialization_alias="Mitigation")
    practice: str = Field(serialization_alias="Practice")
    subtypes: str = Field(serialization_alias="Subtypes")
    reasoning: str = Field(serialization_alias="LLM reasoning")
    quotes: str = Field(serialization_alias="Quotes")


class AffiliationRow(BaseModel):
    name: str = Field(serialization_alias="Name")
    relation: Relation = Field(serialization_alias="Relation")
    company_count: int = Field(serialization_alias="Companies")
    companies: str = Field(serialization_alias="Company names")
    mention_count: int = Field(serialization_alias="Mentions")
    example_mitigation_id: str = Field(serialization_alias="Example mitigation ID")
    example_quotes: str = Field(serialization_alias="Example quotes")


def format_document_date(document: Document) -> str:
    if document.date is None or document.date_precision is None:
        return ""
    match document.date_precision:
        case DatePrecision.DAY:
            return document.date.isoformat()
        case DatePrecision.MONTH:
            return document.date.strftime("%Y-%m")
        case DatePrecision.YEAR:
            return document.date.strftime("%Y")


def excerpt_rows(
    *,
    company_names: list[str],
    companies: list[Company],
    documents: list[Document],
    excerpts: list[Excerpt],
) -> list[ExcerptRow]:
    companies_by_name = {company.name: company for company in companies}
    excerpts_by_document: defaultdict[str, list[Excerpt]] = defaultdict(list)
    for excerpt in excerpts:
        excerpts_by_document[excerpt.document_id].append(excerpt)

    rows: list[ExcerptRow] = []
    for name in company_names:
        company = companies_by_name[name]
        company_documents = sorted(
            (
                document
                for document in documents
                if document.company_id == company.company_id
            ),
            key=lambda document: document.document_id,
        )
        for document in company_documents:
            for order, excerpt in enumerate(
                excerpts_by_document[document.document_id], start=1
            ):
                rows.append(
                    ExcerptRow(
                        excerpt_id=excerpt.excerpt_id,
                        company=company.name,
                        document_id=document.document_id,
                        document_title=document.title,
                        document_type=document.doc_type,
                        document_date=format_document_date(document),
                        document_link=document.link,
                        order_in_document=order,
                        passage_ids=";".join(excerpt.passage_ids),
                        text=excerpt.text,
                    )
                )
    return rows


def evidence_rows(
    *,
    company_names: list[str],
    domain_taxonomy: list[Locus],
    companies: list[Company],
    documents: list[Document],
    excerpts: list[Excerpt],
    evidence: list[Evidence],
) -> list[EvidenceRow]:
    companies_by_name = {company.name: company for company in companies}
    company_order = {
        companies_by_name[name].company_id: order
        for order, name in enumerate(company_names)
    }
    company_names_by_id = {company.company_id: company.name for company in companies}
    company_ids_by_document = {
        document.document_id: document.company_id for document in documents
    }
    domains = [domain for locus in domain_taxonomy for domain in locus.domains]
    domain_order = {domain.code: order for order, domain in enumerate(domains)}
    domain_names = {domain.code: domain.name for domain in domains}
    excerpts_by_id = {excerpt.excerpt_id: excerpt for excerpt in excerpts}

    selected = sorted(
        (
            item
            for item in evidence
            if company_ids_by_document[item.document_id] in company_order
        ),
        key=lambda item: (
            company_order[company_ids_by_document[item.document_id]],
            domain_order[item.domain_code],
            item.document_id,
        ),
    )
    rows: list[EvidenceRow] = []
    for item in selected:
        location = locate_quote(item.quote, excerpts_by_id[item.excerpt_id].text)
        rows.append(
            EvidenceRow(
                evidence_id=item.evidence_id,
                mitigation_id=item.mitigation_id,
                company=company_names_by_id[company_ids_by_document[item.document_id]],
                document_id=item.document_id,
                excerpt_id=item.excerpt_id,
                domain_code=item.domain_code,
                domain_name=domain_names[item.domain_code],
                mitigation_name=item.mitigation_name,
                strength=item.strength,
                quote=item.quote,
                quote_start=location.start if location else None,
                quote_end=location.end if location else None,
                search_reasoning=item.reasoning,
            )
        )
    return rows


def mitigation_rows(
    *,
    company_names: list[str],
    domain_taxonomy: list[Locus],
    instrument_taxonomy: list[Modality],
    companies: list[Company],
    mitigations: list[FoundMitigation],
    practices_results: Mapping[str, PracticesResult],
    instruments_results: Mapping[str, InstrumentsResult],
) -> list[MitigationRow]:
    companies_by_id = {company.company_id: company for company in companies}
    domain_names = {
        domain.code: domain.name
        for locus in domain_taxonomy
        for domain in locus.domains
    }
    instrument_names = {
        instrument.code: instrument.name
        for modality in instrument_taxonomy
        for instrument in modality.instruments
    }
    selected = _selected_mitigations(
        company_names=company_names,
        domain_taxonomy=domain_taxonomy,
        companies=companies,
        mitigations=mitigations,
        practices_results=practices_results,
    )
    missing = [
        mitigation.mitigation_id
        for mitigation in selected
        if mitigation.mitigation_id not in instruments_results
    ]
    if missing:
        raise ValueError(
            f"No instruments result for {len(missing)} of {len(selected)}"
            + f" mitigations, such as {missing[0]}"
        )
    rows: list[MitigationRow] = []
    for mitigation in selected:
        practices = practices_results[mitigation.mitigation_id].answer
        instrument = instruments_results[mitigation.mitigation_id].answer
        rows.append(
            MitigationRow(
                mitigation_id=mitigation.mitigation_id,
                company=companies_by_id[mitigation.company_id].name,
                sector=companies_by_id[mitigation.company_id].sector,
                domain_code=mitigation.domain_code,
                domain_name=domain_names[mitigation.domain_code],
                mitigation_name=mitigation.name,
                search_reasoning=mitigation.reasoning,
                quotes="\n\n".join(quote.quote for quote in mitigation.quotes),
                practices="; ".join(
                    tagged.name for tagged in practices.tagged_practices
                ),
                instrument_code=instrument.instrument_code,
                instrument_name=instrument_names[instrument.instrument_code],
                instrument_reasoning=instrument.reasoning,
            )
        )
    return rows


def practice_rows(
    *,
    company_names: list[str],
    domain_taxonomy: list[Locus],
    companies: list[Company],
    mitigations: list[FoundMitigation],
    practices_results: Mapping[str, PracticesResult],
) -> list[PracticeRow]:
    companies_by_id = {company.company_id: company for company in companies}
    domain_names = {
        domain.code: domain.name
        for locus in domain_taxonomy
        for domain in locus.domains
    }
    selected = _selected_mitigations(
        company_names=company_names,
        domain_taxonomy=domain_taxonomy,
        companies=companies,
        mitigations=mitigations,
        practices_results=practices_results,
    )
    return [
        PracticeRow(
            mitigation_id=mitigation.mitigation_id,
            company=companies_by_id[mitigation.company_id].name,
            sector=companies_by_id[mitigation.company_id].sector,
            domain_code=mitigation.domain_code,
            domain_name=domain_names[mitigation.domain_code],
            mitigation_name=mitigation.name,
            practice=tagged.name,
            subtypes="; ".join(tagged.subtypes),
            reasoning=tagged.reasoning,
            quotes="\n\n".join(
                _cited_quote(mitigation, number) for number in tagged.quote_numbers
            ),
        )
        for mitigation in selected
        for tagged in practices_results[
            mitigation.mitigation_id
        ].answer.tagged_practices
    ]


def affiliation_rows(
    *,
    company_names: list[str],
    domain_taxonomy: list[Locus],
    companies: list[Company],
    mitigations: list[FoundMitigation],
    practices_results: Mapping[str, PracticesResult],
) -> list[AffiliationRow]:
    companies_by_id = {company.company_id: company for company in companies}
    selected = _selected_mitigations(
        company_names=company_names,
        domain_taxonomy=domain_taxonomy,
        companies=companies,
        mitigations=mitigations,
        practices_results=practices_results,
    )
    mentions: defaultdict[
        tuple[str, Relation], list[tuple[FoundMitigation, Affiliation]]
    ] = defaultdict(list)
    for mitigation in selected:
        for affiliation in practices_results[
            mitigation.mitigation_id
        ].answer.affiliations:
            mentions[(affiliation.name, affiliation.relation)].append(
                (mitigation, affiliation)
            )

    rows: list[AffiliationRow] = []
    for (name, relation), found in mentions.items():
        company_ids = list(
            dict.fromkeys(mitigation.company_id for mitigation, _ in found)
        )
        example_mitigation, example_affiliation = found[0]
        rows.append(
            AffiliationRow(
                name=name,
                relation=relation,
                company_count=len(company_ids),
                companies="; ".join(
                    companies_by_id[company_id].name for company_id in company_ids
                ),
                mention_count=len(found),
                example_mitigation_id=example_mitigation.mitigation_id,
                example_quotes="\n\n".join(
                    _cited_quote(example_mitigation, number)
                    for number in example_affiliation.quote_numbers
                ),
            )
        )
    return sorted(
        rows, key=lambda row: (-row.company_count, row.name.casefold(), row.relation)
    )


def _selected_mitigations(
    *,
    company_names: list[str],
    domain_taxonomy: list[Locus],
    companies: list[Company],
    mitigations: list[FoundMitigation],
    practices_results: Mapping[str, PracticesResult],
) -> list[FoundMitigation]:
    companies_by_name = {company.name: company for company in companies}
    company_order = {
        companies_by_name[name].company_id: order
        for order, name in enumerate(company_names)
    }
    domains = [domain for locus in domain_taxonomy for domain in locus.domains]
    domain_order = {domain.code: order for order, domain in enumerate(domains)}

    selected = sorted(
        (
            mitigation
            for mitigation in mitigations
            if mitigation.company_id in company_order
        ),
        key=lambda mitigation: (
            company_order[mitigation.company_id],
            domain_order[mitigation.domain_code],
        ),
    )
    missing = [
        mitigation.mitigation_id
        for mitigation in selected
        if mitigation.mitigation_id not in practices_results
    ]
    if missing:
        raise ValueError(
            f"No practices result for {len(missing)} of {len(selected)}"
            + f" mitigations, such as {missing[0]}"
        )
    return selected


def _cited_quote(mitigation: FoundMitigation, number: int) -> str:
    if not 1 <= number <= len(mitigation.quotes):
        raise ValueError(
            f"The practices answer for {mitigation.mitigation_id} cites quote"
            + f" {number}, but the mitigation has {len(mitigation.quotes)}"
        )
    return mitigation.quotes[number - 1].quote


def write_tab[Row: BaseModel](path: Path, row_type: type[Row], rows: list[Row]) -> None:
    fieldnames = [
        field.serialization_alias or name
        for name, field in row_type.model_fields.items()
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row.model_dump(by_alias=True) for row in rows)
