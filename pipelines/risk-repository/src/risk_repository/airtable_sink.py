import logging
from datetime import UTC, datetime

from risk_repository.records import DocumentRecord, FullTextScreeningRecord
from risk_repository.screen import Decision, ScreeningResult
from toolbox.airtable import JsonValue, Table

logger = logging.getLogger(__name__)

TEXT_SOURCE = "full_text"
SCREENING_STATUS = "screened"
DECISION_RULE = "Single full-text screen"


class AirtableScreeningSink:
    _table: Table
    _model: str
    _prompt_version: str | None

    def __init__(
        self,
        *,
        table: Table,
        model: str,
        prompt_version: str | None,
    ) -> None:
        self._table = table
        self._model = model
        self._prompt_version = prompt_version

    async def write(self, record: DocumentRecord, result: ScreeningResult) -> None:
        if not isinstance(record, FullTextScreeningRecord):
            raise TypeError(
                f"Expected FullTextScreeningRecord, got {type(record).__name__}"
            )
        fields: dict[str, JsonValue] = {
            "llm_include": result.decision.value,
            "llm_reasoning": result.criteria_breakdown,
            "n_screens": 1,
            "n_include": 1 if result.decision == Decision.INCLUDE else 0,
            "decision_rule": DECISION_RULE,
            "screening_model_version": self._model,
            "text_source": TEXT_SOURCE,
            "screening_status": SCREENING_STATUS,
            "screened_at": datetime.now(UTC).isoformat(),
        }
        if self._prompt_version is not None:
            fields["screening_prompt_version"] = self._prompt_version
        await self._table.update(record.record_id, fields, typecast=True)
        logger.info(
            f"Wrote full-text decision {result.decision.value} to {record.record_id}"
        )
