import csv
from pathlib import Path

from pydantic import BaseModel


class Company(BaseModel):
    company_id: str
    name: str
    sector: str


def load_companies(export_dir: Path) -> list[Company]:
    with (export_dir / "companies.csv").open(encoding="utf-8", newline="") as file:
        return [Company.model_validate(row) for row in csv.DictReader(file)]
