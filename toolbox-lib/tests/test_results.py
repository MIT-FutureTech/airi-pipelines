from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from toolbox.results import ResultStore


class Score(BaseModel):
    value: int
    rationale: str


class TestResultStore:
    def test_loads_what_it_saved(self, tmp_path: Path) -> None:
        store = ResultStore(tmp_path / "scores", Score)

        store.save("doc-1", Score(value=80, rationale="In scope"))

        assert store.has("doc-1")
        assert store.load("doc-1") == Score(value=80, rationale="In scope")

    def test_has_nothing_before_saving(self, tmp_path: Path) -> None:
        store = ResultStore(tmp_path / "scores", Score)

        assert not store.has("doc-1")
        assert store.load_all() == {}

    def test_writes_one_json_file_per_item(self, tmp_path: Path) -> None:
        store = ResultStore(tmp_path / "scores", Score)

        store.save("Example_Bank__1.3", Score(value=80, rationale="Café"))

        path = tmp_path / "scores" / "Example_Bank__1.3.json"
        read_back = Score.model_validate_json(path.read_text(encoding="utf-8"))
        expected = Score(value=80, rationale="Café")
        assert read_back == expected

    def test_replaces_an_earlier_result(self, tmp_path: Path) -> None:
        store = ResultStore(tmp_path / "scores", Score)

        store.save("doc-1", Score(value=80, rationale="In scope"))
        store.save("doc-1", Score(value=20, rationale="Out of scope"))

        assert store.load("doc-1") == Score(value=20, rationale="Out of scope")

    def test_loads_all_results_by_item(self, tmp_path: Path) -> None:
        store = ResultStore(tmp_path / "scores", Score)
        store.save("doc-2", Score(value=20, rationale="Out of scope"))
        store.save("doc-1", Score(value=80, rationale="In scope"))

        expected = {
            "doc-1": Score(value=80, rationale="In scope"),
            "doc-2": Score(value=20, rationale="Out of scope"),
        }
        assert store.load_all() == expected

    def test_has_no_result_until_it_is_completely_written(self, tmp_path: Path) -> None:
        store = ResultStore(tmp_path / "scores", Score)

        with (
            patch.object(Path, "replace", side_effect=OSError("interrupted")),
            pytest.raises(OSError, match="interrupted"),
        ):
            store.save("doc-1", Score(value=80, rationale="In scope"))

        assert not store.has("doc-1")
        assert store.load_all() == {}

    @pytest.mark.parametrize("item_id", ["", ".hidden", "../doc-1", "a\\b"])
    def test_rejects_ids_that_are_not_plain_file_names(
        self, tmp_path: Path, item_id: str
    ) -> None:
        store = ResultStore(tmp_path / "scores", Score)

        with pytest.raises(ValueError, match="as a file name"):
            store.save(item_id, Score(value=80, rationale="In scope"))
