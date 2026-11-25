import os
import tempfile
from pathlib import Path

from pydantic import BaseModel


class ResultStore[T: BaseModel]:
    """A folder of results, one JSON file per item, so a rerun can skip finished items.

    When using multiple stores, give each one its own directory to avoid conflicts.

    Usage:

        store = ResultStore(output_dir / "scores", ScoreResult)
        if not store.has(item_id):
            store.save(item_id, await score(item))
    """

    _directory: Path
    _schema: type[T]

    def __init__(self, directory: Path, schema: type[T]) -> None:
        self._directory = directory
        self._schema = schema

    def has(self, item_id: str) -> bool:
        return self._path(item_id).exists()

    def save(self, item_id: str, result: T) -> None:
        path = self._path(item_id)
        self._directory.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_path = tempfile.mkstemp(
            dir=self._directory, prefix=f".{item_id}.", suffix=".tmp"
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(result.model_dump_json(indent=2))
        Path(temporary_path).replace(path)

    def load(self, item_id: str) -> T:
        return self._read(self._path(item_id))

    def load_all(self) -> dict[str, T]:
        if not self._directory.exists():
            return {}
        return {
            path.stem: self._read(path)
            for path in sorted(self._directory.glob("*.json"))
        }

    def _path(self, item_id: str) -> Path:
        if not item_id or item_id.startswith(".") or "/" in item_id or "\\" in item_id:
            raise ValueError(f"Can't use {item_id!r} as a file name")
        return self._directory / f"{item_id}.json"

    def _read(self, path: Path) -> T:
        return self._schema.model_validate_json(path.read_text(encoding="utf-8"))
