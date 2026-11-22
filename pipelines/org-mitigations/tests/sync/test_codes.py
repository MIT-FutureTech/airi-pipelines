from org_mitigations.domain_taxonomy import (
    DOMAIN_TAXONOMY_PATH,
    Domain,
    Locus,
    load_domain_taxonomy,
)
from org_mitigations.instrument_taxonomy import (
    INSTRUMENT_TAXONOMY_PATH,
    Instrument,
    Modality,
    load_instrument_taxonomy,
)
from org_mitigations.practice_list import (
    PRACTICE_LIST_PATH,
    Practice,
    load_practice_list,
)
from org_mitigations.sync.codes import CodeRecord, Taxonomy, code_records


def _domain(code: str, exclusions: str | None) -> Domain:
    return Domain(
        code=code,
        name=f"Domain {code}",
        short_name=f"D{code}",
        definition=f"Definition of {code}.",
        boundary_question=f"Is it {code}?",
        examples=["First example", "Second example"],
        exclusions=exclusions,
    )


def _instrument(code: str) -> Instrument:
    return Instrument(
        code=code,
        name=f"Instrument {code}",
        short_name=f"I{code}",
        definition=f"Definition of {code}.",
        scope=None,
        examples=[],
        exclusions=None,
    )


def _practice(name: str, subtypes: list[str]) -> Practice:
    return Practice(
        name=name,
        definition=f"Definition of {name}.",
        counts=["This counts.", "So does this."],
        does_not_count=["This doesn't."],
        subtypes=subtypes,
    )


class TestCodeRecords:
    def test_numbers_domains_across_loci(self) -> None:
        records = code_records(
            domain_taxonomy=[
                Locus(
                    code="1",
                    name="AI System",
                    short_name="AI System",
                    definition="...",
                    domains=[_domain("1.1", None), _domain("1.2", "Not this.")],
                ),
                Locus(
                    code="2",
                    name="Human & Organization",
                    short_name="Organization",
                    definition="...",
                    domains=[_domain("2.1", None)],
                ),
            ],
            instrument_taxonomy=[],
            practices=[],
        )

        assert records == [
            CodeRecord(
                key="Domain 1.1",
                taxonomy=Taxonomy.DOMAIN,
                code="1.1",
                name="Domain 1.1",
                short_name="D1.1",
                group="AI System",
                order=1,
                definition="Definition of 1.1.",
                details="Boundary question: Is it 1.1?\n"
                + "Examples: First example; Second example",
            ),
            CodeRecord(
                key="Domain 1.2",
                taxonomy=Taxonomy.DOMAIN,
                code="1.2",
                name="Domain 1.2",
                short_name="D1.2",
                group="AI System",
                order=2,
                definition="Definition of 1.2.",
                details="Boundary question: Is it 1.2?\n"
                + "Examples: First example; Second example\n"
                + "Exclusions: Not this.",
            ),
            CodeRecord(
                key="Domain 2.1",
                taxonomy=Taxonomy.DOMAIN,
                code="2.1",
                name="Domain 2.1",
                short_name="D2.1",
                group="Human & Organization",
                order=3,
                definition="Definition of 2.1.",
                details="Boundary question: Is it 2.1?\n"
                + "Examples: First example; Second example",
            ),
        ]

    def test_gives_an_instrument_with_nothing_more_to_say_no_details(self) -> None:
        records = code_records(
            domain_taxonomy=[],
            instrument_taxonomy=[
                Modality(code="O", name="Other", instruments=[_instrument("O.C")])
            ],
            practices=[],
        )

        assert records == [
            CodeRecord(
                key="Instrument O.C",
                taxonomy=Taxonomy.INSTRUMENT,
                code="O.C",
                name="Instrument O.C",
                short_name="IO.C",
                group="Other",
                order=1,
                definition="Definition of O.C.",
                details=None,
            )
        ]

    def test_keys_practices_by_name(self) -> None:
        records = code_records(
            domain_taxonomy=[],
            instrument_taxonomy=[],
            practices=[
                _practice("Model cards", []),
                _practice("Red teaming", ["Internal", "External"]),
            ],
        )

        assert records == [
            CodeRecord(
                key="Practice Model cards",
                taxonomy=Taxonomy.PRACTICE,
                code=None,
                name="Model cards",
                short_name=None,
                group=None,
                order=1,
                definition="Definition of Model cards.",
                details="Counts: This counts. So does this.\n"
                + "Does not count: This doesn't.",
            ),
            CodeRecord(
                key="Practice Red teaming",
                taxonomy=Taxonomy.PRACTICE,
                code=None,
                name="Red teaming",
                short_name=None,
                group=None,
                order=2,
                definition="Definition of Red teaming.",
                details="Counts: This counts. So does this.\n"
                + "Does not count: This doesn't.\n"
                + "Subtypes: Internal; External",
            ),
        ]

    def test_gives_every_code_in_the_pipelines_files_its_own_key(self) -> None:
        records = code_records(
            domain_taxonomy=load_domain_taxonomy(DOMAIN_TAXONOMY_PATH),
            instrument_taxonomy=load_instrument_taxonomy(INSTRUMENT_TAXONOMY_PATH),
            practices=load_practice_list(PRACTICE_LIST_PATH),
        )

        assert len({record.key for record in records}) == len(records) == 56
