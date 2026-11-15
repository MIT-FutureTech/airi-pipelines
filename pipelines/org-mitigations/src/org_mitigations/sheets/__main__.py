import logging

from org_mitigations.companies import load_companies
from org_mitigations.documents import load_documents
from org_mitigations.domain_taxonomy import DOMAIN_TAXONOMY_PATH, load_domain_taxonomy
from org_mitigations.evidence import load_evidence
from org_mitigations.excerpts import Excerpt, load_excerpts
from org_mitigations.sheets.settings import SheetsSettings
from org_mitigations.sheets.tabs import (
    EvidenceRow,
    ExcerptRow,
    evidence_rows,
    excerpt_rows,
    write_tab,
)
from toolbox.log import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = SheetsSettings()
    configure_logging(level=logging.INFO)

    excerpts: list[Excerpt] = []
    for path in settings.excerpt_files:
        excerpts.extend(load_excerpts(path))

    companies = load_companies(settings.export_dir)
    documents = load_documents(settings.export_dir)
    excerpt_tab = excerpt_rows(
        company_names=settings.company_names,
        companies=companies,
        documents=documents,
        excerpts=excerpts,
    )
    evidence_tab = evidence_rows(
        company_names=settings.company_names,
        taxonomy=load_domain_taxonomy(DOMAIN_TAXONOMY_PATH),
        companies=companies,
        documents=documents,
        excerpts=excerpts,
        evidence=load_evidence(settings.llm_output_dir),
    )
    located = sum(row.quote_start is not None for row in evidence_tab)
    logger.info(f"Located {located} of {len(evidence_tab)} quotes")

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    excerpts_path = settings.output_dir / "excerpts.csv"
    write_tab(excerpts_path, ExcerptRow, excerpt_tab)
    logger.info(f"Wrote {len(excerpt_tab)} excerpts to {excerpts_path}")
    evidence_path = settings.output_dir / "evidence.csv"
    write_tab(evidence_path, EvidenceRow, evidence_tab)
    logger.info(f"Wrote {len(evidence_tab)} quotes to {evidence_path}")


if __name__ == "__main__":
    main()
