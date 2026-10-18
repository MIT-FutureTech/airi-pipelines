import json
from pathlib import Path

import pytest

from org_mitigations.taxonomy import Code, Locus, load_taxonomy

TAXONOMY_FILE = {
    "source": {"file": "protocol.docx"},
    "taxonomies": {
        "mitdom": {
            "categories": {
                "1": {
                    "name": "AI System",
                    "short": "AI System",
                    "definition": "Mitigations at the level of the AI system.",
                },
                "1.1": {
                    "name": "Interpretability & Transparency",
                    "short": "Interpretability",
                    "definition": "Mitigations that make a model legible.",
                    "examples": ["Model cards", "SHAP methods"],
                },
                "1.2": {
                    "name": "Alignment & Value Learning",
                    "short": "Alignment",
                    "definition": "Mitigations that shape a model's goals.",
                    "examples": ["RLHF"],
                },
                "2": {
                    "name": "Human & Organization",
                    "short": "Organization",
                    "definition": "Mitigations at the organizational level.",
                },
                "2.1": {
                    "name": "Training & Capacity-building",
                    "short": "Training",
                    "definition": "Mitigations that build AI-safety skills.",
                    "examples": ["Staff safety training"],
                },
            },
            "other": {
                "1": {
                    "codes": ["1.A", "1.C"],
                    "name": "{parent} (Other)",
                    "definition": "AI System mitigations that fit no category.",
                },
            },
        },
    },
}


class TestLoadTaxonomy:
    def test_nests_codes_under_their_locus(self, tmp_path: Path) -> None:
        path = tmp_path / "public-taxonomy.json"
        path.write_text(json.dumps(TAXONOMY_FILE))

        assert load_taxonomy(path) == [
            Locus(
                code="1",
                name="AI System",
                short_name="AI System",
                definition="Mitigations at the level of the AI system.",
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
        categories = {
            "1": {"name": "AI System", "short": "AI System", "definition": "..."},
            "1.1": {"name": "Interpretability", "short": "Interp", "definition": "..."},
        }
        path = tmp_path / "public-taxonomy.json"
        path.write_text(
            json.dumps({"taxonomies": {"mitdom": {"categories": categories}}})
        )

        with pytest.raises(ValueError, match=r"Code 1\.1 has no examples"):
            load_taxonomy(path)
