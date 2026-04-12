import logging
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PipelineStage(StrEnum):
    SCREEN = "screening"
    EXTRACT = "extraction"
    CLASSIFY = "classification"


STAGE_ORDER = [PipelineStage.SCREEN, PipelineStage.EXTRACT, PipelineStage.CLASSIFY]


def result_path(output_dir: Path, stage: PipelineStage, record_id: str) -> Path:
    return output_dir / stage.value / f"{record_id}.json"


def save(path: Path, result: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.model_dump_json(indent=2))


def load[T: BaseModel](path: Path, schema: type[T]) -> T:
    contents = path.read_text()
    return schema.model_validate_json(contents)


def invalidate_downstream(
    output_dir: Path,
    stage: PipelineStage,
    record_id: str,
) -> None:
    stage_idx = STAGE_ORDER.index(stage)
    for downstream in STAGE_ORDER[stage_idx + 1 :]:
        path = result_path(output_dir, downstream, record_id)
        if path.exists():
            path.unlink()
            logger.info(f"Invalidated {downstream.value} for {record_id}")
