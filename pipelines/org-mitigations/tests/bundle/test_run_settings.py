import pytest

from org_mitigations.bundle.run_settings import single_model
from org_mitigations.search.answer import Answer
from org_mitigations.search.calls import SearchResult


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
