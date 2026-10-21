import csv
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel, Field

from org_mitigations.companies import Company
from org_mitigations.documents import DatePrecision, Document
from org_mitigations.excerpts import Excerpt


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


def format_date(document: Document) -> str:
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
                        document_date=format_date(document),
                        document_link=document.link,
                        order_in_document=order,
                        passage_ids=";".join(excerpt.passage_ids),
                        text=excerpt.text,
                    )
                )
    return rows


def write_tab[Row: BaseModel](path: Path, row_type: type[Row], rows: list[Row]) -> None:
    fieldnames = [
        field.serialization_alias or name
        for name, field in row_type.model_fields.items()
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row.model_dump(by_alias=True) for row in rows)
