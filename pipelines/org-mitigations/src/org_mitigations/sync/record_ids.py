from toolbox.airtable import Record


def record_ids_by_key(records: list[Record], key_field: str) -> dict[str, str]:
    record_ids: dict[str, str] = {}
    for record in records:
        if key_field not in record.fields:
            raise ValueError(f"Record {record.id} has no {key_field}")
        key = record.fields[key_field]
        if not isinstance(key, str):
            raise TypeError(f"Record {record.id}'s {key_field} isn't text: {key!r}")
        if key in record_ids:
            raise ValueError(
                f"Records {record_ids[key]} and {record.id}"
                + f" have the same {key_field}, {key!r}"
            )
        record_ids[key] = record.id
    return record_ids
