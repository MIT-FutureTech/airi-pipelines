import asyncio
import logging

from risk_repository.audit.bundle import assemble_bundle
from risk_repository.audit.settings import AuditSettings
from toolbox.airtable import AirtableClient
from toolbox.log import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = AuditSettings()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx"])

    async with AirtableClient(timeout=settings.airtable_timeout) as airtable:
        bundle = await assemble_bundle(settings, airtable=airtable)

    settings.output_path.parent.mkdir(parents=True, exist_ok=True)
    settings.output_path.write_text(bundle.model_dump_json(indent=2))
    logger.info(f"Wrote bundle to {settings.output_path}")


if __name__ == "__main__":
    asyncio.run(main())
