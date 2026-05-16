import logging

import httpx
from pydantic import BaseModel, Field

from risk_repository.documents import get_full_text
from risk_repository.records import DocumentRecord
from risk_repository.results import (
    PipelineStage,
    invalidate_downstream,
    result_path,
    save,
)
from risk_repository.settings import RiskRepositorySettings
from toolbox.concurrency import ConcurrentMap
from toolbox.llm import LLMClient, Message
from toolbox.log import log_context

logger = logging.getLogger(__name__)


class ExtractedRisk(BaseModel):
    supporting_quote: str = Field(
        description="A verbatim quote from the document that supports this risk entry.",
    )
    description: str = Field(
        description="A close paraphrase of how the authors describe this risk.",
    )
    category: str = Field(
        description="The risk category name as used by the original authors, or empty string if not explicitly categorized.",
    )
    subcategory: str = Field(
        description="The risk subcategory name as used by the original authors, or empty string if not explicitly categorized.",
    )


class ExtractionResult(BaseModel):
    risks: list[ExtractedRisk]


async def extract_risks(
    client: LLMClient,
    document: str,
) -> ExtractionResult:
    messages = [
        Message(role="system", content=EXTRACTION_SYSTEM_PROMPT),
        Message(role="user", content=format_extraction_user_prompt(document)),
    ]
    result = await client.generate_structured(messages, ExtractionResult)
    if result.usage is None:
        logger.info("No LLM usage returned")
    else:
        logger.info(f"Usage: {result.usage.model_dump_json()}")
    return result.value


EXTRACTION_SYSTEM_PROMPT = """
You are a research assistant for the AI Risk Repository, a living database of AI risks
classified according to multiple taxonomies. Your task is to extract every distinct AI
risk mentioned in a document.

## Instructions

- Extract risks exactly as the original authors present them. Maintain fidelity to their categorizations and descriptions. Do not reinterpret, generalize, or merge risks.
- Use the authors' own category and subcategory names. If the document does not use explicit categories or subcategories, use an empty string.
- Write each risk description as a close paraphrase of the source text.
- Include a verbatim supporting quote from the document for each risk.
- Each distinct risk should be its own entry, even if risks seem similar to each other.
- If the document contains no extractable AI risks, return an empty list.

When generating your response, follow the field order of the schema: the first field in the schema should be the first field of your response.
"""

_EXTRACTION_USER_PROMPT = """
Extract all AI risks from the following document.

<document>

{document}

</document>
"""


def format_extraction_user_prompt(document: str) -> str:
    return _EXTRACTION_USER_PROMPT.format(document=document)


async def _extract_one(
    record: DocumentRecord,
    *,
    llm: LLMClient,
    http_client: httpx.AsyncClient,
    settings: RiskRepositorySettings,
) -> None:
    with log_context(readable_id=record.readable_id):
        output_path = result_path(
            settings.output_dir, PipelineStage.EXTRACT, record.readable_id
        )
        if not settings.force and output_path.exists():
            return
        full_text = await get_full_text(
            record,
            cache_dir=settings.download_cache_dir,
            client=http_client,
            max_truncation_ratio=settings.document_max_truncation_ratio,
            max_document_length=settings.document_length_limit,
        )
        if full_text is None:
            logger.warning("Skipping extraction: no full text available")
            return
        extraction = await extract_risks(llm, full_text)
        save(output_path, extraction)
        invalidate_downstream(
            settings.output_dir, PipelineStage.EXTRACT, record.readable_id
        )
        logger.info(f"Extracted {len(extraction.risks)} risks")


async def run_extraction(
    records: list[DocumentRecord],
    *,
    llm: LLMClient,
    http_client: httpx.AsyncClient,
    settings: RiskRepositorySettings,
) -> None:
    runner = ConcurrentMap(
        max_concurrency=settings.concurrency,
        progress_description="Extracting",
    )
    async for _ in runner.map(
        records,
        _extract_one,
        llm=llm,
        http_client=http_client,
        settings=settings,
    ):
        pass
