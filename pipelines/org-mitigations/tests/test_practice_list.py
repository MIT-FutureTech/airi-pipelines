import json
from pathlib import Path

import pytest

from org_mitigations.practice_list import (
    PRACTICE_LIST_PATH,
    Practice,
    load_practice_list,
    render_practice_list,
)

RED_TEAMING = Practice(
    name="Red teaming",
    definition="Red teaming is a testing method in which people try to make AI fail.",
    counts=["Internal and external red teams.", "Automated red teaming."],
    does_not_count=["Ordinary quality testing (Model testing)."],
    subtypes=["External red teaming", "Automated red teaming"],
)
AI_POLICY = Practice(
    name="Published AI policy",
    definition="A published AI policy is a policy in which a company publishes AI principles.",
    counts=["A named, published document of responsible AI principles."],
    does_not_count=["Passing statements of values."],
    subtypes=[],
)


class TestLoadPracticeList:
    def test_reads_each_practice(self, tmp_path: Path) -> None:
        path = tmp_path / "practice_list.json"
        path.write_text(
            json.dumps(
                {"practices": [RED_TEAMING.model_dump(), AI_POLICY.model_dump()]}
            )
        )

        assert load_practice_list(path) == [RED_TEAMING, AI_POLICY]

    def test_rejects_a_name_used_twice(self, tmp_path: Path) -> None:
        path = tmp_path / "practice_list.json"
        path.write_text(
            json.dumps({"practices": [AI_POLICY.model_dump(), AI_POLICY.model_dump()]})
        )

        with pytest.raises(ValueError, match="Published AI policy"):
            load_practice_list(path)

    def test_loads_the_pipelines_practice_list(self) -> None:
        assert load_practice_list(PRACTICE_LIST_PATH)


class TestRenderPracticeList:
    def test_lists_each_practice_with_its_subtypes_if_any(self) -> None:
        assert render_practice_list([RED_TEAMING, AI_POLICY]) == (
            "- Red teaming: Red teaming is a testing method in which people try to"
            + " make AI fail.\n"
            + "  Counts: Internal and external red teams. Automated red teaming.\n"
            + "  Does not count: Ordinary quality testing (Model testing).\n"
            + "  Subtypes: External red teaming; Automated red teaming\n"
            + "- Published AI policy: A published AI policy is a policy in which a"
            + " company publishes AI principles.\n"
            + "  Counts: A named, published document of responsible AI principles.\n"
            + "  Does not count: Passing statements of values."
        )
