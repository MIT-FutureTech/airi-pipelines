import json
from pathlib import Path

import pytest

from org_mitigations.domain_taxonomy import (
    DOMAIN_TAXONOMY_PATH,
    Code,
    Locus,
    load_domain_taxonomy,
    render_domain_taxonomy,
)


def _category(
    code: str,
    name: str,
    short_name: str,
    parent: str | None,
    definition: str,
    key_examples: str = "",
    *,
    boundary_question: str = "",
    exclusions: str = "",
) -> dict[str, object]:
    return {
        "code": code,
        "name": name,
        "short_name": short_name,
        "level": 1 if parent is None else 2,
        "parent": parent,
        "definition": definition,
        "boundary_question": boundary_question,
        "exclusions": exclusions,
        "key_examples": key_examples,
    }


TAXONOMY_FILE = {
    "name": "Mitigation Domain Taxonomy",
    "version": "0.8",
    "levels": 2,
    "categories": [
        _category(
            "1", "AI System", "AI System", None, "Mitigations at the AI system level."
        ),
        _category(
            "1.1",
            "Interpretability & Transparency",
            "Interpretability",
            "1",
            "Mitigations that make a model legible.",
            "Model cards; SHAP methods",
        ),
        _category(
            "1.2",
            "Alignment & Value Learning",
            "Alignment",
            "1",
            "Mitigations that shape a model's goals.",
            "RLHF",
        ),
        _category(
            "1.A",
            "AI System (Other - Additional)",
            "AISystem-OA",
            "1",
            "AI System mitigations that fit no category above.",
        ),
        _category(
            "2",
            "Human & Organization",
            "Organization",
            None,
            "Mitigations at the organizational level.",
        ),
        _category(
            "2.1",
            "Training & Capacity-building",
            "Training",
            "2",
            "Mitigations that build AI-safety skills.",
            "Staff safety training",
        ),
        _category(
            "2.C",
            "Human & Organization (Other - Cross-cutting)",
            "HumanOrg-OC",
            "2",
            "Mitigations that cut across this locus.",
        ),
    ],
}


class TestLoadDomainTaxonomy:
    def test_nests_codes_under_their_locus(self, tmp_path: Path) -> None:
        path = tmp_path / "taxonomy.json"
        path.write_text(json.dumps(TAXONOMY_FILE))

        assert load_domain_taxonomy(path) == [
            Locus(
                code="1",
                name="AI System",
                short_name="AI System",
                definition="Mitigations at the AI system level.",
                codes=[
                    Code(
                        code="1.1",
                        name="Interpretability & Transparency",
                        short_name="Interpretability",
                        definition="Mitigations that make a model legible.",
                        examples=["Model cards", "SHAP methods"],
                    ),
                    Code(
                        code="1.2",
                        name="Alignment & Value Learning",
                        short_name="Alignment",
                        definition="Mitigations that shape a model's goals.",
                        examples=["RLHF"],
                    ),
                ],
            ),
            Locus(
                code="2",
                name="Human & Organization",
                short_name="Organization",
                definition="Mitigations at the organizational level.",
                codes=[
                    Code(
                        code="2.1",
                        name="Training & Capacity-building",
                        short_name="Training",
                        definition="Mitigations that build AI-safety skills.",
                        examples=["Staff safety training"],
                    ),
                ],
            ),
        ]

    def test_rejects_a_code_without_examples(self, tmp_path: Path) -> None:
        taxonomy_file = {
            "categories": [
                _category("1", "AI System", "AI System", None, "..."),
                _category("1.1", "Interpretability", "Interp", "1", "..."),
            ]
        }
        path = tmp_path / "taxonomy.json"
        path.write_text(json.dumps(taxonomy_file))

        with pytest.raises(ValueError, match=r"Code 1\.1 has no examples"):
            load_domain_taxonomy(path)

    def test_loads_the_pipelines_taxonomy_file(self) -> None:
        assert load_domain_taxonomy(DOMAIN_TAXONOMY_PATH)


class TestRenderDomainTaxonomy:
    def test_lists_each_locus_with_all_its_codes(self, tmp_path: Path) -> None:
        taxonomy_file = {
            "categories": [
                _category(
                    "1",
                    "AI System",
                    "AI System",
                    None,
                    "Mitigations at the AI system level.",
                    boundary_question="Does it change the AI system?",
                ),
                _category(
                    "1.1",
                    "Interpretability & Transparency",
                    "Interpretability",
                    "1",
                    "Mitigations that make a model legible.",
                    "Model cards; SHAP methods",
                    boundary_question="Does it make the model visible?",
                    exclusions="Runtime monitoring → Operational.",
                ),
                _category(
                    "1.A",
                    "AI System (Other - Additional)",
                    "AISystem-OA",
                    "1",
                    "AI System mitigations that fit no category above.",
                ),
                _category(
                    "2",
                    "Human & Organization",
                    "Organization",
                    None,
                    "Mitigations at the organizational level.",
                    boundary_question="Does it change people?",
                ),
                _category(
                    "2.1",
                    "Training & Capacity-building",
                    "Training",
                    "2",
                    "Mitigations that build AI-safety skills.",
                    "Staff safety training",
                    boundary_question="Does it build skills?",
                ),
            ]
        }
        path = tmp_path / "taxonomy.json"
        path.write_text(json.dumps(taxonomy_file))

        assert render_domain_taxonomy(path) == (
            "LOCUS 1: AI SYSTEM\n"
            "Mitigations at the AI system level."
            " Boundary question: Does it change the AI system?\n"
            "- 1.1: Interpretability & Transparency —"
            " Mitigations that make a model legible. Does it make the model visible?"
            " Examples: Model cards; SHAP methods. (Runtime monitoring → Operational.)\n"
            "- 1.A: AI System (Other - Additional) —"
            " AI System mitigations that fit no category above.\n"
            "\n"
            "LOCUS 2: HUMAN & ORGANIZATION\n"
            "Mitigations at the organizational level."
            " Boundary question: Does it change people?\n"
            "- 2.1: Training & Capacity-building —"
            " Mitigations that build AI-safety skills. Does it build skills?"
            " Examples: Staff safety training."
        )
