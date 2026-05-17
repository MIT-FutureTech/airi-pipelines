from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from risk_repository.screen import Decision, ScreeningResult


class OutcomeClass(StrEnum):
    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    TRUE_NEGATIVE = "true_negative"
    FALSE_NEGATIVE = "false_negative"
    UNLABELED = "unlabeled"


class ScreeningAudit(BaseModel):
    ground_truth_decision: Decision | None
    abstract_result: ScreeningResult | None
    full_text_result: ScreeningResult | None
    outcome_class: OutcomeClass


class AuditDocument(BaseModel):
    readable_id: str
    title: str | None
    url: str | None
    pdf_path: Path | None
    abstract: str | None
    screening: ScreeningAudit


class AuditBundle(BaseModel):
    run_name: str | None
    results_dir: Path
    generated_at: datetime
    documents: list[AuditDocument]
