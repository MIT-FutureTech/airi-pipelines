import asyncio
import logging

from org_mitigations.bundle.build import build_bundle
from org_mitigations.bundle.settings import BundleSettings
from org_mitigations.bundle.synced import (
    SyncedCode,
    SyncedMitigation,
    SyncedQuote,
    read_synced,
)
from org_mitigations.corpus import load_corpus
from org_mitigations.documents import load_document_record_ids
from org_mitigations.sync.record_ids import record_ids_by_key
from org_mitigations.table_names import (
    CODES_TABLE,
    MITIGATIONS_TABLE,
    PASSAGES_TABLE,
    QUOTES_TABLE,
)
from toolbox.airtable import AirtableClient, Table
from toolbox.log import configure_logging

logger = logging.getLogger(__name__)

_AIRTABLE_TIMEOUT = 30.0


async def main() -> None:
    settings = BundleSettings()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx"])

    corpus = load_corpus(settings.export_dir, company_names=None)
    async with AirtableClient(timeout=_AIRTABLE_TIMEOUT) as client:
        codes_table, mitigations_table, quotes_table, passages_table = (
            Table(client, base_id=settings.airtable_base_id, table_name=name)
            for name in [CODES_TABLE, MITIGATIONS_TABLE, QUOTES_TABLE, PASSAGES_TABLE]
        )
        logger.info("Reading the records from Airtable")
        codes = [read_synced(record, SyncedCode) for record in await codes_table.all()]
        mitigations = [
            read_synced(record, SyncedMitigation)
            for record in await mitigations_table.all()
        ]
        quotes = [
            read_synced(record, SyncedQuote) for record in await quotes_table.all()
        ]
        passage_record_ids = record_ids_by_key(
            await passages_table.all(fields=["Passage ID"]), "Passage ID"
        )

    bundle = build_bundle(
        codes=codes,
        mitigations=mitigations,
        quotes=quotes,
        companies=corpus.companies,
        documents=corpus.documents,
        excerpts=corpus.excerpts,
        document_ids_by_record_id={
            record_id: document_id
            for document_id, record_id in load_document_record_ids(
                settings.export_dir
            ).items()
        },
        passage_ids_by_record_id={
            record_id: passage_id
            for passage_id, record_id in passage_record_ids.items()
        },
    )
    logger.info(
        f"Bundled {len(bundle.mitigations)} mitigations from"
        + f" {len(bundle.companies)} companies, with {len(bundle.quotes)} quotes"
    )

    settings.output_path.parent.mkdir(parents=True, exist_ok=True)
    settings.output_path.write_text(bundle.model_dump_json())
    logger.info(f"Wrote bundle to {settings.output_path}")


if __name__ == "__main__":
    asyncio.run(main())
