import json
from pathlib import Path

from org_mitigations.instrument_taxonomy import (
    INSTRUMENT_TAXONOMY_PATH,
    Instrument,
    Modality,
    load_instrument_taxonomy,
    render_instrument_taxonomy,
)


def _category(
    code: str,
    name: str,
    parent: str | None,
    definition: str,
    *,
    scope: str = "",
    key_examples: str = "",
    exclusions: str = "",
) -> dict[str, object]:
    return {
        "code": code,
        "name": name,
        "short_name": name,
        "level": 1 if parent is None else 2,
        "parent": parent,
        "definition": definition,
        "scope": scope,
        "exclusions": exclusions,
        "key_examples": key_examples,
    }


class TestLoadInstrumentTaxonomy:
    def test_nests_instruments_under_their_modality(self, tmp_path: Path) -> None:
        taxonomy_file = {
            "categories": [
                _category("1", "Inform", None, "Mitigations that change knowledge."),
                _category(
                    "1.1",
                    "Research & Evidence",
                    "1",
                    "Generate knowledge.",
                    scope="Studies and datasets.",
                    key_examples="Research studies; Research datasets",
                    exclusions="Testing → Evaluation.",
                ),
                _category("1.2", "Information Sharing & Disclosure", "1", "Share."),
                _category("O", "Other", None, "Mitigations that fit nowhere above."),
                _category("O.C", "Other (Cross-cutting)", "O", "Broad or vague."),
            ]
        }
        path = tmp_path / "taxonomy.json"
        path.write_text(json.dumps(taxonomy_file))

        assert load_instrument_taxonomy(path) == [
            Modality(
                code="1",
                name="Inform",
                instruments=[
                    Instrument(
                        code="1.1",
                        name="Research & Evidence",
                        short_name="Research & Evidence",
                        definition="Generate knowledge.",
                        scope="Studies and datasets.",
                        examples=["Research studies", "Research datasets"],
                        exclusions="Testing → Evaluation.",
                    ),
                    Instrument(
                        code="1.2",
                        name="Information Sharing & Disclosure",
                        short_name="Information Sharing & Disclosure",
                        definition="Share.",
                        scope=None,
                        examples=[],
                        exclusions=None,
                    ),
                ],
            ),
            Modality(
                code="O",
                name="Other",
                instruments=[
                    Instrument(
                        code="O.C",
                        name="Other (Cross-cutting)",
                        short_name="Other (Cross-cutting)",
                        definition="Broad or vague.",
                        scope=None,
                        examples=[],
                        exclusions=None,
                    )
                ],
            ),
        ]

    def test_loads_the_pipelines_taxonomy_file(self) -> None:
        modalities = load_instrument_taxonomy(INSTRUMENT_TAXONOMY_PATH)

        assert [len(modality.instruments) for modality in modalities] == [2, 3, 4, 2]


class TestRenderInstrumentTaxonomy:
    def test_lists_each_modality_with_all_its_instruments(self, tmp_path: Path) -> None:
        taxonomy_file = {
            "categories": [
                _category("1", "Inform", None, "Mitigations that change knowledge."),
                _category(
                    "1.1",
                    "Research & Evidence",
                    "1",
                    "Mitigations that generate knowledge.",
                    scope="Studies, datasets.",
                    key_examples="Research studies; Research datasets",
                    exclusions="Testing → Evaluation.",
                ),
                _category(
                    "1.2",
                    "Information Sharing & Disclosure",
                    "1",
                    "Mitigations that share information.",
                    scope="Disclosure, reporting.",
                    key_examples="Incident reports",
                ),
                _category("O", "Other", None, "Mitigations that fit nowhere above."),
                _category("O.A", "Other (Additional)", "O", "Clear instruments."),
            ]
        }
        path = tmp_path / "taxonomy.json"
        path.write_text(json.dumps(taxonomy_file))

        assert render_instrument_taxonomy(path) == (
            "MODALITY 1: INFORM\n"
            "Mitigations that change knowledge.\n"
            "- 1.1: Research & Evidence — Mitigations that generate knowledge."
            " Scope: Studies, datasets."
            " Examples: Research studies; Research datasets."
            " (Testing → Evaluation.)\n"
            "- 1.2: Information Sharing & Disclosure —"
            " Mitigations that share information. Scope: Disclosure, reporting."
            " Examples: Incident reports.\n"
            "\n"
            "MODALITY O: OTHER\n"
            "Mitigations that fit nowhere above.\n"
            "- O.A: Other (Additional) — Clear instruments."
        )

    def test_renders_the_pipelines_taxonomy_file(self) -> None:
        assert render_instrument_taxonomy(INSTRUMENT_TAXONOMY_PATH)
