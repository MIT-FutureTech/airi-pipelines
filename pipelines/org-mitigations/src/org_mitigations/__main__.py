import logging

from org_mitigations.bundle import assemble_bundle
from org_mitigations.companies import load_companies
from org_mitigations.documents import load_documents
from org_mitigations.evidence import load_evidence
from org_mitigations.excerpts import Excerpt, load_excerpts
from org_mitigations.run import load_run
from org_mitigations.settings import BundleSettings
from org_mitigations.taxonomy import load_taxonomy
from toolbox.log import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = BundleSettings()
    configure_logging(level=logging.INFO)

    excerpts: list[Excerpt] = []
    for path in settings.excerpt_files:
        excerpts.extend(load_excerpts(path))

    bundle = assemble_bundle(
        company_names=settings.company_names,
        run=load_run(
            settings.llm_output_dir,
            temperature=settings.temperature,
            reasoning_effort=settings.reasoning_effort,
        ),
        taxonomy=load_taxonomy(settings.taxonomy_file),
        companies=load_companies(settings.export_dir),
        documents=load_documents(settings.export_dir),
        excerpts=excerpts,
        evidence=load_evidence(settings.llm_output_dir),
    )

    settings.output_path.parent.mkdir(parents=True, exist_ok=True)
    settings.output_path.write_text(bundle.model_dump_json())
    logger.info(f"Wrote bundle to {settings.output_path}")


if __name__ == "__main__":
    main()
