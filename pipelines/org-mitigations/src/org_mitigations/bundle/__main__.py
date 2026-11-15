import logging

from org_mitigations.bundle.assemble import assemble_bundle
from org_mitigations.bundle.run_settings import RunSettings, single_model
from org_mitigations.bundle.settings import BundleSettings
from org_mitigations.corpus import load_corpus
from org_mitigations.domain_taxonomy import DOMAIN_TAXONOMY_PATH, load_domain_taxonomy
from org_mitigations.evidence import evidence_from_mitigations
from org_mitigations.search.calls import SearchResult
from org_mitigations.search.context import build_contexts
from org_mitigations.search.mitigations import mitigations_from_results
from toolbox.log import configure_logging
from toolbox.results import ResultStore

logger = logging.getLogger(__name__)


def main() -> None:
    settings = BundleSettings()
    configure_logging(level=logging.INFO)

    corpus = load_corpus(settings.export_dir, company_names=None)
    contexts = build_contexts(
        corpus.excerpts, corpus.documents, max_chars=settings.max_chars
    )
    results = ResultStore(settings.run_dir / "search", SearchResult).load_all()
    mitigations = mitigations_from_results(results, contexts)

    bundle = assemble_bundle(
        company_names=settings.company_names,
        run=RunSettings(
            prompt_file=settings.prompt_file,
            model=single_model(results),
            temperature=settings.temperature,
            reasoning_effort=settings.reasoning_effort,
        ),
        taxonomy=load_domain_taxonomy(DOMAIN_TAXONOMY_PATH),
        companies=corpus.companies,
        documents=corpus.documents,
        excerpts=corpus.excerpts,
        evidence=evidence_from_mitigations(mitigations, corpus.excerpts),
    )

    settings.output_path.parent.mkdir(parents=True, exist_ok=True)
    settings.output_path.write_text(bundle.model_dump_json())
    logger.info(f"Wrote bundle to {settings.output_path}")


if __name__ == "__main__":
    main()
