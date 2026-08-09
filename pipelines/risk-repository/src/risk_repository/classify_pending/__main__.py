import asyncio
import logging

from risk_repository.classify_pending.reviews import (
    fetch_pipeline_codings,
    pending_risks,
)
from risk_repository.classify_pending.risks import fetch_paper_risks
from risk_repository.classify_pending.run import classify_and_write, report_pending
from risk_repository.classify_pending.settings import ClassifyPendingSettings
from toolbox.airtable import AirtableClient
from toolbox.llm import OpenRouterClient
from toolbox.log import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = ClassifyPendingSettings()
    configure_logging(
        level=logging.INFO,
        filepath=settings.log_path,
        loggers_to_silence=["httpx", "openai"],
    )

    async with AirtableClient(timeout=settings.airtable_timeout) as airtable:
        documents = await fetch_paper_risks(
            airtable,
            base_id=settings.airtable_base_id,
            table_name=settings.risks_table,
            quick_refs=settings.quick_ref,
        )
        codings = await fetch_pipeline_codings(
            airtable,
            base_id=settings.airtable_base_id,
            table_name=settings.reviews_table,
        )
        selected = documents if settings.force else pending_risks(documents, codings)
        if settings.dry_run:
            report_pending(selected)
            return

        async with OpenRouterClient(
            model=settings.model,
            rate_limit_rps=settings.llm_rate_limit_rps,
            timeout=settings.llm_timeout,
        ) as llm:
            await classify_and_write(
                selected,
                codings,
                airtable=airtable,
                llm=llm,
                settings=settings,
            )


if __name__ == "__main__":
    asyncio.run(main())
