from pathlib import Path

from org_mitigations.companies import Company, load_companies

COMPANIES_CSV = """\
company_id,name,sector_id,sector,description
recA,Example Bank,recS1,Finance and Insurance,"A bank, with a comma"
recB,Example Retail,recS2,"Trade, Transportation, and Utilities",A retailer
"""


class TestLoadCompanies:
    def test_reads_each_row(self, tmp_path: Path) -> None:
        (tmp_path / "companies.csv").write_text(COMPANIES_CSV)

        assert load_companies(tmp_path) == [
            Company(
                company_id="recA",
                name="Example Bank",
                sector="Finance and Insurance",
            ),
            Company(
                company_id="recB",
                name="Example Retail",
                sector="Trade, Transportation, and Utilities",
            ),
        ]
