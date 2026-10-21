import logging

from org_mitigations.companies import load_companies
from org_mitigations.documents import load_documents
from org_mitigations.excerpts import Excerpt, load_excerpts
from org_mitigations.sheets.settings import SheetsSettings
from org_mitigations.sheets.tabs import ExcerptRow, excerpt_rows, write_tab
from toolbox.log import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = SheetsSettings()
    configure_logging(level=logging.INFO)

    excerpts: list[Excerpt] = []
    for path in settings.excerpt_files:
        excerpts.extend(load_excerpts(path))

    rows = excerpt_rows(
        company_names=settings.company_names,
        companies=load_companies(settings.export_dir),
        documents=load_documents(settings.export_dir),
        excerpts=excerpts,
    )

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    path = settings.output_dir / "excerpts.csv"
    write_tab(path, ExcerptRow, rows)
    logger.info(f"Wrote {len(rows)} excerpts to {path}")


if __name__ == "__main__":
    main()
