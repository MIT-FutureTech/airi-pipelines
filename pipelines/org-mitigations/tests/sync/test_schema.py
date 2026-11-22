from collections.abc import Mapping

import pytest
from pydantic import BaseModel

from org_mitigations.sync.codes import CODE_FIELD_TYPES, CodeRecord
from org_mitigations.sync.mitigations import MITIGATION_FIELD_TYPES, MitigationRecord
from org_mitigations.sync.quotes import QUOTE_FIELD_TYPES, QuoteRecord
from org_mitigations.sync.schema import FieldType, field_mismatches
from toolbox.airtable import FieldSchema, TableSchema


def _schema(*fields: tuple[str, str]) -> TableSchema:
    return TableSchema(
        id="tblQuotes",
        name="Mitigation Quotes",
        fields=[
            FieldSchema(id=f"fld{number}", name=name, type=field_type)
            for number, (name, field_type) in enumerate(fields)
        ],
    )


class TestFieldMismatches:
    def test_finds_none_when_every_field_has_its_type(self) -> None:
        schema = _schema(
            ("ID", "singleLineText"),
            ("Quote", "multilineText"),
            ("Note", "multilineText"),
        )

        assert (
            field_mismatches(
                schema, {"ID": FieldType.SINGLE_LINE_TEXT, "Quote": FieldType.LONG_TEXT}
            )
            == []
        )

    def test_lists_missing_and_mistyped_fields(self) -> None:
        schema = _schema(("ID", "singleLineText"), ("Quote", "singleLineText"))

        assert field_mismatches(
            schema,
            {
                "ID": FieldType.SINGLE_LINE_TEXT,
                "Quote": FieldType.LONG_TEXT,
                "Strength": FieldType.SINGLE_SELECT,
            },
        ) == [
            "Mitigation Quotes's field 'Quote' is singleLineText, not multilineText",
            "Mitigation Quotes has no field 'Strength'",
        ]


class TestFieldTypes:
    @pytest.mark.parametrize(
        ("record_type", "field_types"),
        [
            (CodeRecord, CODE_FIELD_TYPES),
            (MitigationRecord, MITIGATION_FIELD_TYPES),
            (QuoteRecord, QUOTE_FIELD_TYPES),
        ],
    )
    def test_give_every_record_field_a_type(
        self, record_type: type[BaseModel], field_types: Mapping[str, FieldType]
    ) -> None:
        aliases = [
            field.serialization_alias for field in record_type.model_fields.values()
        ]

        assert aliases == list(field_types)
