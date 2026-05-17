import asyncio
import logging
from contextlib import AsyncExitStack

from risk_repository.audit.bundle import assemble_bundle
from risk_repository.audit.settings import AuditSettings
from risk_repository.download import make_http_client
from toolbox.airtable import AirtableClient
from toolbox.log import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = AuditSettings()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx"])

    needs_airtable = (
        settings.airtable_documents_table is not None
        or settings.ground_truth_table is not None
    )

    async with AsyncExitStack() as stack:
        airtable: AirtableClient | None = None
        if needs_airtable:
            airtable = await stack.enter_async_context(
                AirtableClient(timeout=settings.airtable_timeout)
            )
        http_client = await stack.enter_async_context(make_http_client())
        bundle = await assemble_bundle(
            settings,
            airtable=airtable,
            http_client=http_client,
        )

    settings.output_path.parent.mkdir(parents=True, exist_ok=True)
    settings.output_path.write_text(bundle.model_dump_json(indent=2))
    logger.info(f"Wrote bundle to {settings.output_path}")


if __name__ == "__main__":
    asyncio.run(main())
