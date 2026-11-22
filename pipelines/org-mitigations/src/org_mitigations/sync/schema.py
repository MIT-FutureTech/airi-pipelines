from collections.abc import Mapping
from enum import StrEnum

from toolbox.airtable import TableSchema


class FieldType(StrEnum):
    SINGLE_LINE_TEXT = "singleLineText"
    LONG_TEXT = "multilineText"
    NUMBER = "number"
    SINGLE_SELECT = "singleSelect"
    LINKS = "multipleRecordLinks"


def field_mismatches(
    schema: TableSchema, expected_types: Mapping[str, FieldType]
) -> list[str]:
    actual_types = {field.name: field.type for field in schema.fields}
    mismatches: list[str] = []
    for name, expected_type in expected_types.items():
        if name not in actual_types:
            mismatches.append(f"{schema.name} has no field {name!r}")
        elif actual_types[name] != expected_type:
            mismatches.append(
                f"{schema.name}'s field {name!r} is {actual_types[name]},"
                + f" not {expected_type}"
            )
    return mismatches
