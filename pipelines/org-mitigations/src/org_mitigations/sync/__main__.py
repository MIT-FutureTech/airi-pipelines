import asyncio
import logging
from collections.abc import Mapping, Sequence
from itertools import batched

from pydantic import BaseModel
from tqdm import tqdm

from org_mitigations.corpus import load_corpus
from org_mitigations.documents import load_document_record_ids
from org_mitigations.domain_taxonomy import DOMAIN_TAXONOMY_PATH, load_domain_taxonomy
from org_mitigations.evidence import evidence_from_mitigations
from org_mitigations.instrument_taxonomy import (
    INSTRUMENT_TAXONOMY_PATH,
    load_instrument_taxonomy,
)
from org_mitigations.instruments.calls import InstrumentsResult
from org_mitigations.passages import load_passages
from org_mitigations.practice_list import PRACTICE_LIST_PATH, load_practice_list
from org_mitigations.practices.calls import PracticesResult
from org_mitigations.search.calls import SearchResult
from org_mitigations.search.context import build_contexts
from org_mitigations.search.mitigations import mitigations_from_results
from org_mitigations.settings import PipelineStage
from org_mitigations.sync.codes import CODE_FIELD_TYPES, code_records
from org_mitigations.sync.mitigations import MITIGATION_FIELD_TYPES, mitigation_records
from org_mitigations.sync.quotes import QUOTE_FIELD_TYPES, quote_records
from org_mitigations.sync.record_ids import record_ids_by_key
from org_mitigations.sync.schema import FieldType, field_mismatches
from org_mitigations.sync.settings import SyncSettings
from org_mitigations.table_names import (
    CODES_TABLE,
    MITIGATIONS_TABLE,
    PASSAGES_TABLE,
    QUOTES_TABLE,
)
from toolbox.airtable import AirtableClient, Record, Table
from toolbox.airtable.table import BATCH_SIZE
from toolbox.log import configure_logging
from toolbox.results import ResultStore

logger = logging.getLogger(__name__)

_AIRTABLE_TIMEOUT = 30.0


async def main() -> None:
    settings = SyncSettings()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx"])

    corpus = load_corpus(settings.export_dir, company_names=None)
    contexts = build_contexts(
        corpus.excerpts, corpus.documents, max_chars=settings.max_chars
    )
    mitigations = mitigations_from_results(
        ResultStore(settings.run_dir / PipelineStage.SEARCH, SearchResult).load_all(),
        contexts,
    )
    codes = code_records(
        domain_taxonomy=load_domain_taxonomy(DOMAIN_TAXONOMY_PATH),
        instrument_taxonomy=load_instrument_taxonomy(INSTRUMENT_TAXONOMY_PATH),
        practices=load_practice_list(PRACTICE_LIST_PATH),
    )

    async with AirtableClient(timeout=_AIRTABLE_TIMEOUT) as client:
        codes_table, mitigations_table, quotes_table, passages_table = (
            Table(client, base_id=settings.airtable_base_id, table_name=name)
            for name in [CODES_TABLE, MITIGATIONS_TABLE, QUOTES_TABLE, PASSAGES_TABLE]
        )
        await _check_fields(
            {
                codes_table: CODE_FIELD_TYPES,
                mitigations_table: MITIGATION_FIELD_TYPES,
                quotes_table: QUOTE_FIELD_TYPES,
            }
        )
        logger.info(f"Reading the record IDs of {PASSAGES_TABLE}")
        passage_record_ids = record_ids_by_key(
            await passages_table.all(fields=["Passage ID"]), "Passage ID"
        )

        code_record_ids = await _create_missing(
            codes_table, CODES_TABLE, "Key", codes, dry_run=settings.dry_run
        )
        mitigation_record_ids = await _create_missing(
            mitigations_table,
            MITIGATIONS_TABLE,
            "ID",
            mitigation_records(
                mitigations=mitigations,
                practices_results=ResultStore(
                    settings.run_dir / PipelineStage.PRACTICES, PracticesResult
                ).load_all(),
                instruments_results=ResultStore(
                    settings.run_dir / PipelineStage.INSTRUMENTS, InstrumentsResult
                ).load_all(),
                code_record_ids=code_record_ids,
                pipeline_run=settings.run_dir.name,
            ),
            dry_run=settings.dry_run,
        )
        await _create_missing(
            quotes_table,
            QUOTES_TABLE,
            "ID",
            quote_records(
                evidence=evidence_from_mitigations(mitigations, corpus.excerpts),
                excerpts=corpus.excerpts,
                passages=load_passages(settings.export_dir),
                mitigation_record_ids=mitigation_record_ids,
                document_record_ids=load_document_record_ids(settings.export_dir),
                passage_record_ids=passage_record_ids,
            ),
            dry_run=settings.dry_run,
        )


async def _check_fields(expected: Mapping[Table, Mapping[str, FieldType]]) -> None:
    mismatches = [
        mismatch
        for table, field_types in expected.items()
        for mismatch in field_mismatches(await table.schema(), field_types)
    ]
    if mismatches:
        raise ValueError(
            "The Airtable tables don't have the fields the sync writes:\n"
            + "\n".join(mismatches)
        )


async def _create_missing(
    table: Table,
    table_name: str,
    key_field: str,
    records: Sequence[BaseModel],
    *,
    dry_run: bool,
) -> dict[str, str]:
    """Create the records whose keys aren't in the table yet.

    Returns the record ID of every record, old or new. In a dry run, records that
    would be created get made-up record IDs, so that records linking to them can
    still be built and checked.
    """
    existing = record_ids_by_key(await table.all(fields=[key_field]), key_field)
    rows = [
        record.model_dump(mode="json", by_alias=True, exclude_none=True)
        for record in records
    ]
    keys = {row[key_field] for row in rows}
    missing = [row for row in rows if row[key_field] not in existing]
    logger.info(
        f"{table_name}: {len(rows) - len(missing)} of the run's {len(rows)}"
        + f" are already in Airtable, {len(missing)} aren't."
        + f" Airtable has {len(set(existing) - keys)} that aren't in the run."
    )
    if dry_run:
        return existing | {row[key_field]: f"(new) {row[key_field]}" for row in missing}
    created: list[Record] = []
    with tqdm(desc=table_name, total=len(missing), unit="record") as progress:
        for batch in batched(missing, BATCH_SIZE):
            created.extend(await table.batch_create(batch))
            progress.update(len(batch))
    return existing | record_ids_by_key(created, key_field)


if __name__ == "__main__":
    asyncio.run(main())
