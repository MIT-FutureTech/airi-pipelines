from pydantic import BaseModel

from risk_repository.evaluate.match import DocumentMatchResult


class DocumentExtractionMetrics(BaseModel):
    quick_ref: str
    gt_risk_count: int
    pipeline_risk_count: int
    matched_count: int


class ExtractionMetrics(BaseModel):
    documents_evaluated: int
    gt_risk_count: int
    pipeline_risk_count: int
    matched_count: int
    precision: float
    recall: float
    f1: float
    per_document: list[DocumentExtractionMetrics]


def evaluate_extraction(
    match_results: list[DocumentMatchResult],
) -> ExtractionMetrics:
    per_document = [
        DocumentExtractionMetrics(
            quick_ref=doc.quick_ref,
            gt_risk_count=len(doc.gt_risks),
            pipeline_risk_count=len(doc.pipeline_risks),
            matched_count=len(doc.matches),
        )
        for doc in match_results
    ]

    total_gt = sum(d.gt_risk_count for d in per_document)
    total_pipeline = sum(d.pipeline_risk_count for d in per_document)
    total_matched = sum(d.matched_count for d in per_document)
    precision = total_matched / total_pipeline if total_pipeline > 0 else 0.0
    recall = total_matched / total_gt if total_gt > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return ExtractionMetrics(
        documents_evaluated=len(per_document),
        gt_risk_count=total_gt,
        pipeline_risk_count=total_pipeline,
        matched_count=total_matched,
        precision=precision,
        recall=recall,
        f1=f1,
        per_document=per_document,
    )
