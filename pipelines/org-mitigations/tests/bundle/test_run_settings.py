import json
from pathlib import Path

import pytest

from org_mitigations.bundle.run_settings import RunSettings, load_run, single_model
from org_mitigations.search.answer import Answer
from org_mitigations.search.calls import SearchResult


def write_output(path: Path, *, prompt_file: str, llm_model: str) -> None:
    metadata = {"prompt_file": prompt_file, "llm_model": llm_model, "llm_error": ""}
    path.write_text(json.dumps({"metadata": metadata}))


class TestLoadRun:
    def test_combines_the_recorded_and_supplied_settings(self, tmp_path: Path) -> None:
        for name in ("Example_Bank_001__1.1.json", "Example_Bank_001__1.2.json"):
            write_output(
                tmp_path / name, prompt_file="prompt.md", llm_model="example/model"
            )
        (tmp_path / "log.txt").write_text("Classified 2 rows")

        run = load_run(tmp_path, temperature=1.0, reasoning_effort="medium")

        assert run == RunSettings(
            prompt_file="prompt.md",
            model="example/model",
            temperature=1.0,
            reasoning_effort="medium",
        )

    def test_rejects_a_folder_with_more_than_one_model(self, tmp_path: Path) -> None:
        write_output(
            tmp_path / "Example_Bank_001__1.1.json",
            prompt_file="prompt.md",
            llm_model="example/model",
        )
        write_output(
            tmp_path / "Example_Bank_001__1.2.json",
            prompt_file="prompt.md",
            llm_model="example/other-model",
        )

        with pytest.raises(ValueError, match="Expected one prompt and model"):
            load_run(tmp_path, temperature=1.0, reasoning_effort="medium")


def _result(code: str, *, model: str) -> SearchResult:
    return SearchResult(
        context_id="Example_Bank",
        domain_code=code,
        answer=Answer(
            match_id=f"Example_Bank__{code}",
            has_mitigation=False,
            reason=None,
            classifications=[],
        ),
        model=model,
        usage=None,
    )


class TestSingleModel:
    def test_returns_the_model_every_result_used(self) -> None:
        results = {
            f"Example_Bank__{code}": _result(code, model="example/model")
            for code in ("1.1", "1.2")
        }

        assert single_model(results) == "example/model"

    def test_rejects_results_from_more_than_one_model(self) -> None:
        results = {
            "Example_Bank__1.1": _result("1.1", model="example/model"),
            "Example_Bank__1.2": _result("1.2", model="example/other-model"),
        }

        with pytest.raises(ValueError, match="one model"):
            single_model(results)
