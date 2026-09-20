import logging
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PipelineStage(StrEnum):
    SCORE = "score"


STAGE_ORDER = [PipelineStage.SCORE]


def stage_dir(output_dir: Path, stage: PipelineStage) -> Path:
    return output_dir / stage.value


def result_path(output_dir: Path, stage: PipelineStage, readable_id: str) -> Path:
    return stage_dir(output_dir, stage) / f"{readable_id}.json"


def save(path: Path, result: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(result.model_dump_json(indent=2), encoding="utf-8")


def load[T: BaseModel](path: Path, schema: type[T]) -> T:
    return schema.model_validate_json(path.read_text(encoding="utf-8"))


def load_stage[T: BaseModel](
    output_dir: Path, stage: PipelineStage, schema: type[T]
) -> list[T]:
    directory = stage_dir(output_dir, stage)
    if not directory.exists():
        return []
    return [load(path, schema) for path in sorted(directory.glob("*.json"))]
