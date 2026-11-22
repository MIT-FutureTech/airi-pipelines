import asyncio
import logging
from collections.abc import Mapping

from org_mitigations.corpus import load_corpus
from org_mitigations.domain_taxonomy import DOMAIN_TAXONOMY_PATH, load_domain_taxonomy
from org_mitigations.evidence import evidence_from_mitigations
from org_mitigations.instrument_taxonomy import (
    INSTRUMENT_TAXONOMY_PATH,
    load_instrument_taxonomy,
)
from org_mitigations.practice_list import PRACTICE_LIST_PATH, load_practice_list
from org_mitigations.search.calls import SearchResult
from org_mitigations.search.context import build_contexts
from org_mitigations.search.mitigations import mitigations_from_results
from org_mitigations.settings import PipelineStage
from org_mitigations.sync.codes import CODE_FIELD_TYPES, code_records
from org_mitigations.sync.mitigations import MITIGATION_FIELD_TYPES
from org_mitigations.sync.quotes import QUOTE_FIELD_TYPES
from org_mitigations.sync.record_ids import record_ids_by_key
from org_mitigations.sync.schema import FieldType, field_mismatches
from org_mitigations.sync.settings import SyncSettings
from toolbox.airtable import AirtableClient, Table
from toolbox.log import configure_logging
from toolbox.results import ResultStore

logger = logging.getLogger(__name__)

CODES_TABLE = "Mitigation Codes"
MITIGATIONS_TABLE = "Mitigations"
QUOTES_TABLE = "Mitigation Quotes"
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
    evidence = evidence_from_mitigations(mitigations, corpus.excerpts)
    codes = code_records(
        domain_taxonomy=load_domain_taxonomy(DOMAIN_TAXONOMY_PATH),
        instrument_taxonomy=load_instrument_taxonomy(INSTRUMENT_TAXONOMY_PATH),
        practices=load_practice_list(PRACTICE_LIST_PATH),
    )

    async with AirtableClient(timeout=_AIRTABLE_TIMEOUT) as client:
        codes_table, mitigations_table, quotes_table = (
            Table(client, base_id=settings.airtable_base_id, table_name=name)
            for name in [CODES_TABLE, MITIGATIONS_TABLE, QUOTES_TABLE]
        )
        await _check_fields(
            {
                codes_table: CODE_FIELD_TYPES,
                mitigations_table: MITIGATION_FIELD_TYPES,
                quotes_table: QUOTE_FIELD_TYPES,
            }
        )
        existing_codes = record_ids_by_key(await codes_table.all(fields=["Key"]), "Key")
        existing_mitigations = record_ids_by_key(
            await mitigations_table.all(fields=["ID"]), "ID"
        )
        existing_quotes = record_ids_by_key(await quotes_table.all(fields=["ID"]), "ID")

    _report(CODES_TABLE, [code.key for code in codes], existing_codes)
    _report(
        MITIGATIONS_TABLE,
        [mitigation.mitigation_id for mitigation in mitigations],
        existing_mitigations,
    )
    _report(QUOTES_TABLE, [item.evidence_id for item in evidence], existing_quotes)


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


def _report(table_name: str, keys: list[str], existing: Mapping[str, str]) -> None:
    missing = [key for key in keys if key not in existing]
    others = set(existing) - set(keys)
    logger.info(
        f"{table_name}: {len(keys) - len(missing)} of the run's {len(keys)}"
        + f" are already in Airtable, {len(missing)} aren't."
        + f" Airtable has {len(others)} that aren't in the run."
    )


if __name__ == "__main__":
    asyncio.run(main())
