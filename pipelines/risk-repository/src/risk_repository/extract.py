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
        description="The risk category name in the authors' exact wording. For a category-level entry this is the category itself; for a subcategory-level entry it is the parent category. Empty only if the document names no category.",
    )
    subcategory: str = Field(
        description="The risk subcategory name in the authors' exact wording, or empty string for a category-level entry (a top-level risk with no subcategory).",
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
classified according to multiple taxonomies. The documents you read propose frameworks,
taxonomies, or other structured classifications of AI risks. Your task is to extract the
named risk categories and subcategories that make up a document's classification.

## What to extract

- Extract the risks the document's framework explicitly names or labels, covering the top two levels of its hierarchy: its risk categories and their subcategories. If the framework is deeper, the top two levels are enough; if it has only one level, extract that level.
- Produce a separate entry for each named category and for each named subcategory:
  - For a category, put its name in `category` and leave `subcategory` empty.
  - For a subcategory, put its parent category's name in `category` and the subcategory's name in `subcategory`.
- Do not invent risks the framework does not name, do not split a single named risk into several entries, and do not merge distinct named risks.
- If the document does not lay out a structured set of named risks, extract only the risks it explicitly labels; do not enumerate every risk it mentions in passing.
- If the document contains no extractable AI risks, return an empty list.

## How to fill each entry

- Use the authors' exact category and subcategory names. Do not rephrase, generalize, or standardize them.
- Write the description as a close paraphrase of how the authors describe that specific category or subcategory.
- Include a verbatim supporting quote from the document for that category or subcategory.

When generating your response, follow the field order of the schema: the first field in the schema should be the first field of your response.
"""

_EXTRACTION_USER_PROMPT = """
Extract the named risk categories and subcategories from the following document.

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
