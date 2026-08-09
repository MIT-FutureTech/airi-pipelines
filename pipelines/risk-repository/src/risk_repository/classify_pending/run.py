import logging
from collections.abc import Mapping, Sequence

from risk_repository.classify import DocumentRisks, classify_documents
from risk_repository.classify_pending.reviews import (
    PipelineCoding,
    replace_pipeline_codings,
)
from risk_repository.classify_pending.settings import ClassifyPendingSettings
from toolbox.airtable import AirtableClient
from toolbox.llm import LLMClient
from toolbox.log import log_context

logger = logging.getLogger(__name__)


def report_pending(documents: Sequence[DocumentRisks]) -> None:
    for document in documents:
        print(f"\n{document.readable_id}: {len(document.risks)} risks")
        for risk in document.risks:
            print(f"  {risk.name}")


async def classify_and_write(
    documents: Sequence[DocumentRisks],
    codings: Mapping[str, PipelineCoding],
    *,
    airtable: AirtableClient,
    llm: LLMClient,
    settings: ClassifyPendingSettings,
) -> None:
    async for classified in classify_documents(
        documents,
        llm=llm,
        concurrency=settings.concurrency,
        progress_description="Classifying",
    ):
        with log_context(quick_ref=classified.readable_id):
            await replace_pipeline_codings(
                airtable,
                base_id=settings.airtable_base_id,
                table_name=settings.reviews_table,
                reviewer=settings.pipeline_reviewer,
                classified=classified.classification.risks,
                codings=codings,
            )
