from pathlib import Path

import pytest

from org_mitigations.domain_taxonomy import DOMAIN_TAXONOMY_PATH, render_domain_taxonomy
from org_mitigations.instrument_taxonomy import (
    INSTRUMENT_TAXONOMY_PATH,
    render_instrument_taxonomy,
)
from org_mitigations.practice_list import (
    PRACTICE_LIST_PATH,
    load_practice_list,
    render_practice_list,
)
from org_mitigations.prompt import Prompt, load_prompt

SEARCH_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "search.md"
PRACTICES_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "practices.md"
INSTRUMENTS_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "instruments.md"

TEMPLATE = """\
<!-- SYSTEM -->
Find mitigations in one of these categories:
$taxonomy
Answer as {"match_id": "<match_id>", "classifications": []}.

<!-- USER -->
<company>$company</company>
<documents>
$context
</documents>
<category>$code</category>
<match_id>$match_id</match_id>
"""


def _write(tmp_path: Path, template: str) -> Path:
    path = tmp_path / "prompt.md"
    path.write_text(template)
    return path


class TestLoadPrompt:
    def test_fills_in_the_taxonomy(self, tmp_path: Path) -> None:
        prompt = load_prompt(_write(tmp_path, TEMPLATE), taxonomy="- 1.1: Example")

        assert prompt == Prompt(
            system="Find mitigations in one of these categories:\n"
            + "- 1.1: Example\n"
            + 'Answer as {"match_id": "<match_id>", "classifications": []}.',
            user_template="<company>$company</company>\n"
            + "<documents>\n"
            + "$context\n"
            + "</documents>\n"
            + "<category>$code</category>\n"
            + "<match_id>$match_id</match_id>",
        )

    def test_rejects_text_before_the_system_section(self, tmp_path: Path) -> None:
        path = _write(tmp_path, f"Notes\n{TEMPLATE}")

        with pytest.raises(ValueError, match="must start with"):
            load_prompt(path, taxonomy="")

    def test_rejects_a_prompt_without_a_user_section(self, tmp_path: Path) -> None:
        path = _write(tmp_path, TEMPLATE.replace("<!-- USER -->", ""))

        with pytest.raises(ValueError, match="needs one"):
            load_prompt(path, taxonomy="")

    def test_rejects_a_system_section_without_the_taxonomy(
        self, tmp_path: Path
    ) -> None:
        path = _write(tmp_path, TEMPLATE.replace("$taxonomy", "(none)"))

        with pytest.raises(ValueError, match="system section has placeholders"):
            load_prompt(path, taxonomy="")

    def test_loads_the_search_prompt(self) -> None:
        assert load_prompt(
            SEARCH_PROMPT_PATH, taxonomy=render_domain_taxonomy(DOMAIN_TAXONOMY_PATH)
        )

    def test_loads_the_practices_prompt(self) -> None:
        assert load_prompt(
            PRACTICES_PROMPT_PATH,
            practices=render_practice_list(load_practice_list(PRACTICE_LIST_PATH)),
        )

    def test_loads_the_instruments_prompt(self) -> None:
        assert load_prompt(
            INSTRUMENTS_PROMPT_PATH,
            instruments=render_instrument_taxonomy(INSTRUMENT_TAXONOMY_PATH),
        )


class TestRenderUser:
    def test_fills_in_the_call(self, tmp_path: Path) -> None:
        prompt = load_prompt(_write(tmp_path, TEMPLATE), taxonomy="")

        assert prompt.render_user(
            company="Example Bank",
            context="<document>...</document>",
            code="2.1",
            match_id="Example_Bank__2.1",
        ) == (
            "<company>Example Bank</company>\n"
            "<documents>\n"
            "<document>...</document>\n"
            "</documents>\n"
            "<category>2.1</category>\n"
            "<match_id>Example_Bank__2.1</match_id>"
        )

    def test_leaves_placeholders_inside_the_context_alone(self, tmp_path: Path) -> None:
        prompt = load_prompt(_write(tmp_path, TEMPLATE), taxonomy="")

        user = prompt.render_user(
            company="Example Bank",
            context="Fees rose by $code million.",
            code="2.1",
            match_id="Example_Bank__2.1",
        )

        assert "Fees rose by $code million." in user

    def test_rejects_values_that_differ_from_the_placeholders(
        self, tmp_path: Path
    ) -> None:
        path = _write(tmp_path, TEMPLATE.replace("$company", "$sector"))
        prompt = load_prompt(path, taxonomy="")

        with pytest.raises(ValueError, match="user section has placeholders"):
            prompt.render_user(
                company="Example Bank",
                context="<document>...</document>",
                code="2.1",
                match_id="Example_Bank__2.1",
            )
