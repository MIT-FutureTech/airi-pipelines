import asyncio
import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from risk_repository.audit.bundle import AuditBundle
from toolbox.log import configure_logging

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = "manifest.json"


class ManifestEntry(BaseModel):
    filename: str
    run_name: str | None
    generated_at: datetime


class Manifest(BaseModel):
    bundles: list[ManifestEntry]


class ManifestSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_hide_none_type=True,
    cli_prog_name="risk_repository.audit.manifest",
):
    """
    Build a manifest of audit bundles for the auditor UI to discover.

    Scans a directory for bundle JSON files and writes manifest.json
    alongside them.
    """

    bundles_dir: Path = Field(
        default=...,
        description="Directory containing audit bundle JSON files",
    )


def build_manifest(bundles_dir: Path) -> Manifest:
    entries: list[ManifestEntry] = []
    for path in sorted(bundles_dir.glob("*.json")):
        if path.name == MANIFEST_FILENAME:
            continue
        bundle = AuditBundle.model_validate_json(path.read_text())
        entries.append(
            ManifestEntry(
                filename=path.name,
                run_name=bundle.run_name,
                generated_at=bundle.generated_at,
            )
        )
    return Manifest(bundles=entries)


async def main() -> None:
    settings = ManifestSettings()
    configure_logging(level=logging.INFO)
    manifest = build_manifest(settings.bundles_dir)
    output_path = settings.bundles_dir / MANIFEST_FILENAME
    output_path.write_text(manifest.model_dump_json(indent=2))
    logger.info(f"Wrote {len(manifest.bundles)} entries to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
