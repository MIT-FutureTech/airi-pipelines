import logging

from org_mitigations.corpus import load_corpus
from org_mitigations.domain_taxonomy import DOMAIN_TAXONOMY_PATH, load_domain_taxonomy
from org_mitigations.evidence import evidence_from_mitigations
from org_mitigations.practices.calls import PracticesResult
from org_mitigations.search.calls import SearchResult
from org_mitigations.search.context import build_contexts
from org_mitigations.search.mitigations import mitigations_from_results
from org_mitigations.settings import PipelineStage
from org_mitigations.sheets.settings import SheetsSettings
from org_mitigations.sheets.tabs import (
    EvidenceRow,
    ExcerptRow,
    MitigationRow,
    PracticeRow,
    evidence_rows,
    excerpt_rows,
    mitigation_rows,
    practice_rows,
    write_tab,
)
from toolbox.log import configure_logging
from toolbox.results import ResultStore

logger = logging.getLogger(__name__)


def main() -> None:
    settings = SheetsSettings()
    configure_logging(level=logging.INFO)

    corpus = load_corpus(settings.export_dir, company_names=None)
    contexts = build_contexts(
        corpus.excerpts, corpus.documents, max_chars=settings.max_chars
    )
    results = ResultStore(
        settings.run_dir / PipelineStage.SEARCH,
        SearchResult,
    ).load_all()
    mitigations = mitigations_from_results(results, contexts)
    practices_results = ResultStore(
        settings.run_dir / PipelineStage.PRACTICES,
        PracticesResult,
    ).load_all()
    taxonomy = load_domain_taxonomy(DOMAIN_TAXONOMY_PATH)
    if settings.company_names is None:
        company_names = sorted(company.name for company in corpus.companies)
    else:
        company_names = settings.company_names

    excerpt_tab = excerpt_rows(
        company_names=company_names,
        companies=corpus.companies,
        documents=corpus.documents,
        excerpts=corpus.excerpts,
    )
    evidence_tab = evidence_rows(
        company_names=company_names,
        taxonomy=taxonomy,
        companies=corpus.companies,
        documents=corpus.documents,
        excerpts=corpus.excerpts,
        evidence=evidence_from_mitigations(mitigations, corpus.excerpts),
    )
    located = sum(row.quote_start is not None for row in evidence_tab)
    logger.info(f"Located {located} of {len(evidence_tab)} quotes")
    mitigation_tab = mitigation_rows(
        company_names=company_names,
        taxonomy=taxonomy,
        companies=corpus.companies,
        mitigations=mitigations,
        practices_results=practices_results,
    )
    untagged_tab = [row for row in mitigation_tab if not row.practices]
    practice_tab = practice_rows(
        company_names=company_names,
        taxonomy=taxonomy,
        companies=corpus.companies,
        mitigations=mitigations,
        practices_results=practices_results,
    )

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    excerpts_path = settings.output_dir / "excerpts.csv"
    write_tab(excerpts_path, ExcerptRow, excerpt_tab)
    logger.info(f"Wrote {len(excerpt_tab)} excerpts to {excerpts_path}")
    evidence_path = settings.output_dir / "evidence.csv"
    write_tab(evidence_path, EvidenceRow, evidence_tab)
    logger.info(f"Wrote {len(evidence_tab)} quotes to {evidence_path}")
    mitigations_path = settings.output_dir / "mitigations.csv"
    write_tab(mitigations_path, MitigationRow, mitigation_tab)
    logger.info(f"Wrote {len(mitigation_tab)} mitigations to {mitigations_path}")
    untagged_path = settings.output_dir / "untagged_mitigations.csv"
    write_tab(untagged_path, MitigationRow, untagged_tab)
    logger.info(f"Wrote {len(untagged_tab)} untagged mitigations to {untagged_path}")
    practices_path = settings.output_dir / "practices.csv"
    write_tab(practices_path, PracticeRow, practice_tab)
    logger.info(f"Wrote {len(practice_tab)} practice tags to {practices_path}")


if __name__ == "__main__":
    main()
