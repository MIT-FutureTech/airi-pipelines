import csv
import logging
from collections.abc import Sequence
from pathlib import Path

from agora_screening.corpus import DocumentRecord
from agora_screening.results import PipelineStage, result_path
from agora_screening.results import load as load_result
from agora_screening.score import ScoreResult

logger = logging.getLogger(__name__)

COLUMNS = [
    "ID",
    "OECD slug",
    "Link",
    "Name (original language)",
    "Name (original language) ISO code",
    "Name (original language) found in text",
    "Name (English translation)",
    "Jurisdiction",
    "Date introduced",
    "Most recent activity",
    "Most recent activity date",
    "Scope score",
    "Scope score rationale",
    "LLM model used",
    "LLM query status",
    "Aggregator Link",
    "csv_row",
    "text_row",
    "OECD name",
    "chars_sent",
    "original_chars",
    "truncated",
    "cid_artefact_ratio",
    "prompt_tokens",
    "completion_tokens",
]


def _row(record: DocumentRecord, result: ScoreResult) -> dict[str, str]:
    assessment = result.assessment
    return {
        "ID": record.readable_id,
        "OECD slug": record.slug,
        "Link": record.link,
        "Name (original language)": assessment.name_original_language
        if assessment
        else "",
        "Name (original language) ISO code": (
            assessment.name_original_language_code if assessment else ""
        ),
        "Name (original language) found in text": (
            result.title_check.value if result.title_check else ""
        ),
        "Name (English translation)": assessment.name_english if assessment else "",
        "Jurisdiction": record.jurisdiction,
        "Date introduced": record.date_introduced,
        "Most recent activity": record.most_recent_activity,
        "Most recent activity date": record.most_recent_activity_date,
        "Scope score": str(assessment.scope_score) if assessment else "",
        "Scope score rationale": assessment.scope_score_rationale if assessment else "",
        "LLM model used": result.model or "",
        "LLM query status": result.status.value,
        "Aggregator Link": record.aggregator_link,
        "csv_row": str(record.csv_row),
        "text_row": str(record.text_row) if record.text_row is not None else "",
        "OECD name": record.name,
        "chars_sent": str(result.chars_sent),
        "original_chars": str(result.original_chars),
        "truncated": "yes" if result.truncated else "no",
        "cid_artefact_ratio": f"{result.cid_artefact_ratio:.4f}",
        "prompt_tokens": str(result.input_tokens)
        if result.input_tokens is not None
        else "",
        "completion_tokens": str(result.output_tokens)
        if result.output_tokens is not None
        else "",
    }


def export_csv(
    records: Sequence[DocumentRecord],
    *,
    output_dir: Path,
    csv_path: Path,
) -> int:
    """Write one CSV row per scored document, in corpus order.

    UTF-8 with a BOM so that Excel opens non-Latin titles correctly.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for record in records:
            path = result_path(output_dir, PipelineStage.SCORE, record.readable_id)
            if not path.exists():
                continue
            writer.writerow(_row(record, load_result(path, ScoreResult)))
            written += 1
    logger.info(f"Wrote {written} rows to {csv_path}")
    return written
