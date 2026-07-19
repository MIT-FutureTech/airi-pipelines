from collections.abc import Iterable

from pydantic import BaseModel, Field

from risk_repository.evaluate.ground_truth import CategoryLevel, GroundTruthRisk
from risk_repository.evaluate.match import DocumentMatchResult
from risk_repository.extract import ExtractedRisk


class NodeTally(BaseModel):
    """Nodes bucketed by how many counterparts each one matched"""

    total: int = 0
    matched: int = 0
    unmatched: int = 0
    multi: int = 0

    def record(self, degree: int) -> None:
        self.total += 1
        if degree == 0:
            self.unmatched += 1
        elif degree == 1:
            self.matched += 1
        else:
            self.multi += 1

    def add(self, other: "NodeTally") -> None:
        self.total += other.total
        self.matched += other.matched
        self.unmatched += other.unmatched
        self.multi += other.multi


class SideTally(BaseModel):
    overall: NodeTally = Field(default_factory=NodeTally)
    category: NodeTally = Field(default_factory=NodeTally)
    subcategory: NodeTally = Field(default_factory=NodeTally)

    def record(self, level: CategoryLevel, degree: int) -> None:
        self.overall.record(degree)
        if level == CategoryLevel.CATEGORY:
            self.category.record(degree)
        else:
            self.subcategory.record(degree)

    def add(self, other: "SideTally") -> None:
        self.overall.add(other.overall)
        self.category.add(other.category)
        self.subcategory.add(other.subcategory)


class Scores(BaseModel):
    precision: float
    recall: float
    f1: float


class DocumentExtractionMetrics(BaseModel):
    readable_id: str
    ground_truth: SideTally
    pipeline: SideTally


class ExtractionMetrics(BaseModel):
    documents_evaluated: int
    ground_truth: SideTally
    pipeline: SideTally
    per_document: list[DocumentExtractionMetrics]


def scores(ground_truth: NodeTally, pipeline: NodeTally) -> Scores:
    """Precision, recall, and F1 counting only nodes matched one-to-one.

    Recall credits a ground-truth node only when the pipeline recovered it as a
    single node; precision credits a pipeline node only when it maps to a single
    ground-truth node. Splits and lumps therefore lower the side they burden.
    """
    recall = ground_truth.matched / ground_truth.total if ground_truth.total else 0.0
    precision = pipeline.matched / pipeline.total if pipeline.total else 0.0
    denominator = precision + recall
    f1 = 2 * precision * recall / denominator if denominator else 0.0
    return Scores(precision=precision, recall=recall, f1=f1)


def evaluate_extraction(
    match_results: list[DocumentMatchResult],
) -> ExtractionMetrics:
    per_document: list[DocumentExtractionMetrics] = []
    for doc in match_results:
        if not doc.gt_risks:
            continue
        gt_degrees = _degrees(len(doc.gt_risks), (m.gt_index for m in doc.matches))
        pipeline_degrees = _degrees(
            len(doc.pipeline_risks), (m.pipeline_index for m in doc.matches)
        )

        gt_side = SideTally()
        for risk, degree in zip(doc.gt_risks, gt_degrees, strict=True):
            gt_side.record(_gt_level(risk), degree)

        pipeline_side = SideTally()
        for risk, degree in zip(doc.pipeline_risks, pipeline_degrees, strict=True):
            pipeline_side.record(_pipeline_level(risk), degree)

        per_document.append(
            DocumentExtractionMetrics(
                readable_id=doc.readable_id,
                ground_truth=gt_side,
                pipeline=pipeline_side,
            )
        )

    total_gt = SideTally()
    total_pipeline = SideTally()
    for doc_metrics in per_document:
        total_gt.add(doc_metrics.ground_truth)
        total_pipeline.add(doc_metrics.pipeline)

    return ExtractionMetrics(
        documents_evaluated=len(per_document),
        ground_truth=total_gt,
        pipeline=total_pipeline,
        per_document=per_document,
    )


def _gt_level(risk: GroundTruthRisk) -> CategoryLevel:
    if risk.category_level is not None:
        return risk.category_level
    return CategoryLevel.SUBCATEGORY if risk.subcategory else CategoryLevel.CATEGORY


def _pipeline_level(risk: ExtractedRisk) -> CategoryLevel:
    return (
        CategoryLevel.SUBCATEGORY
        if risk.subcategory.strip()
        else CategoryLevel.CATEGORY
    )


def _degrees(node_count: int, indices: Iterable[int]) -> list[int]:
    degrees = [0] * node_count
    for index in indices:
        degrees[index] += 1
    return degrees
