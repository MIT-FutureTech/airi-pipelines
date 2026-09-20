import csv
import logging
from collections.abc import Iterator, Sequence
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# csv.field_size_limit(sys.maxsize) overflows the C long on Windows. The largest
# document text in the OECD corpus is under 1 MB; this is ample headroom.
_CSV_FIELD_SIZE_LIMIT = 2**31 - 1


class DocumentRecord(BaseModel, frozen=True):
    """One candidate document, as the pipeline sees it.

    Source-agnostic by design: the OECD export is the first corpus but not the
    intended last, so anything OECD-specific belongs in the loader, not here.
    """

    readable_id: str
    slug: str
    link: str
    aggregator_link: str
    name: str
    jurisdiction: str
    organization: str
    date_introduced: str
    most_recent_activity: str
    most_recent_activity_date: str
    category: str
    initiative_type: str
    binding: str
    summary: str
    text: str
    csv_row: int
    text_row: int | None = None


def oecd_slug(aggregator_link: str) -> str:
    """The trailing path segment of an OECD.AI initiative URL, unique per row.

    Preferred as a join key over the positional ID, which is only row order and
    shifts whenever the export is regenerated.
    """
    return aggregator_link.rstrip("/").rsplit("/", 1)[-1]


def _read_rows(csv_path: Path) -> Iterator[dict[str, str]]:
    previous_limit = csv.field_size_limit(_CSV_FIELD_SIZE_LIMIT)
    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                yield {
                    key: (value or "") for key, value in row.items() if key is not None
                }
    finally:
        csv.field_size_limit(previous_limit)


def load_oecd_corpus(csv_path: Path) -> list[DocumentRecord]:
    """Read the OECD.AI Policy Observatory export into document records.

    The export carries already-extracted document text in its `Text` column, so
    no PDF fetching or extraction happens here.
    """
    records: list[DocumentRecord] = []
    for csv_row, row in enumerate(_read_rows(csv_path), start=1):
        aggregator_link = row["Aggregator Link"]
        records.append(
            DocumentRecord(
                readable_id=row["ID"],
                slug=oecd_slug(aggregator_link),
                link=row["Link"],
                aggregator_link=aggregator_link,
                name=row["Name"],
                jurisdiction=row["Jurisdiction"],
                organization=row["Organization"],
                date_introduced=row["Date introduced"],
                most_recent_activity=row["Most recent activity"],
                most_recent_activity_date=row["Most recent activity date"],
                category=row["Category"],
                initiative_type=row["Initiative type"],
                binding=row["Binding"],
                summary=row["Aggregator Summary"],
                text=row["Text"],
                csv_row=csv_row,
            )
        )
    logger.info(f"Loaded {len(records)} records from {csv_path}")
    return records


def select_with_text(
    records: Sequence[DocumentRecord], min_chars: int
) -> list[DocumentRecord]:
    """Records carrying usable extracted text, in corpus order, numbered from 1.

    Most of the OECD corpus has no text at all: 1,575 of 2,305 rows had no PDF
    fetched or failed extraction. A further handful extract to a few characters
    of junk, which min_chars excludes.
    """
    selected: list[DocumentRecord] = []
    for record in records:
        if len(record.text.strip()) >= min_chars:
            selected.append(record.model_copy(update={"text_row": len(selected) + 1}))
    logger.info(
        f"{len(selected)} of {len(records)} records have at least {min_chars} characters"
    )
    return selected


def apply_selection(
    records: Sequence[DocumentRecord],
    *,
    document_ids: Sequence[str] | None,
    limit: int | None,
) -> list[DocumentRecord]:
    if document_ids is not None:
        wanted = set(document_ids)
        records = [record for record in records if record.readable_id in wanted]
        missing = wanted - {record.readable_id for record in records}
        if missing:
            logger.warning(f"Requested IDs not present in corpus: {sorted(missing)}")
    if limit is not None:
        records = records[:limit]
    return list(records)
