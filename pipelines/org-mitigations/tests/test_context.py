import pytest

from org_mitigations.context import Context, build_contexts
from org_mitigations.documents import Document
from org_mitigations.excerpts import Excerpt


def _document(document_id: str, company_id: str, doc_type: str, title: str) -> Document:
    return Document(
        document_id=document_id,
        company_id=company_id,
        title=title,
        doc_type=doc_type,
        date=None,
        date_precision=None,
        link=f"https://example.com/{document_id}.pdf",
    )


def _excerpt(document_id: str, number: int, text: str) -> Excerpt:
    return Excerpt(
        excerpt_id=f"{document_id}_excerpt{number}",
        document_id=document_id,
        text=text,
        passage_ids=[f"{document_id}_{number}"],
    )


DOCUMENTS = [
    _document("Example_Bank_001", "recA", "Annual report", "2025 Annual Report"),
    _document("Example_Bank_002", "recA", "AI governance", "Our Approach to AI"),
    _document("Example_Retail_001", "recB", "ESG report", "Sustainability Report"),
]
CONTEXT_BODY = """\
<document id="Example_Bank_001">
<doc_type>Annual report</doc_type>
<title>2025 Annual Report</title>
<excerpts>
<excerpt id="1">[...] We train staff. [...]</excerpt>
<excerpt id="2">[...] We test models. [...]</excerpt>
</excerpts>
</document>
<document id="Example_Bank_002">
<doc_type>AI governance</doc_type>
<title>Our Approach to AI</title>
<excerpts>
<excerpt id="3">[...] Our board oversees AI. [...]</excerpt>
</excerpts>
</document>"""


class TestBuildContexts:
    def test_lays_out_documents_with_numbered_excerpts(self) -> None:
        excerpts = [
            _excerpt("Example_Bank_001", 1, "We train staff."),
            _excerpt("Example_Bank_001", 2, "We test models."),
            _excerpt("Example_Bank_002", 1, "Our board oversees AI."),
        ]

        assert build_contexts(excerpts, DOCUMENTS, max_chars=1000) == [
            Context(
                context_id="Example_Bank",
                company_id="recA",
                text=CONTEXT_BODY,
                excerpt_ids=[
                    "Example_Bank_001_excerpt1",
                    "Example_Bank_001_excerpt2",
                    "Example_Bank_002_excerpt1",
                ],
            ),
        ]

    def test_numbers_a_companys_contexts_when_it_needs_several(self) -> None:
        excerpts = [
            _excerpt("Example_Bank_001", 1, "We train staff."),
            _excerpt("Example_Bank_002", 1, "Our board oversees AI."),
        ]

        contexts = build_contexts(excerpts, DOCUMENTS, max_chars=30)

        assert [context.context_id for context in contexts] == [
            "Example_Bank_group1",
            "Example_Bank_group2",
        ]
        assert '<excerpt id="1">[...] Our board oversees AI.' in contexts[1].text

    def test_gives_each_company_its_own_contexts(self) -> None:
        excerpts = [
            _excerpt("Example_Bank_001", 1, "We train staff."),
            _excerpt("Example_Retail_001", 1, "We label AI-generated images."),
        ]

        contexts = build_contexts(excerpts, DOCUMENTS, max_chars=1000)

        assert [(c.context_id, c.company_id) for c in contexts] == [
            ("Example_Bank", "recA"),
            ("Example_Retail", "recB"),
        ]

    def test_rejects_a_company_whose_documents_are_named_differently(self) -> None:
        documents = [
            *DOCUMENTS,
            _document("Other_Bank_001", "recA", "Annual report", "Annual Report"),
        ]
        excerpts = [
            _excerpt("Example_Bank_001", 1, "We train staff."),
            _excerpt("Other_Bank_001", 1, "We test models."),
        ]

        with pytest.raises(ValueError, match="several names"):
            build_contexts(excerpts, documents, max_chars=1000)

    def test_rejects_two_companies_whose_documents_share_a_name(self) -> None:
        documents = [
            *DOCUMENTS,
            _document("Example_Bank_003", "recC", "Annual report", "Annual Report"),
        ]
        excerpts = [
            _excerpt("Example_Bank_001", 1, "We train staff."),
            _excerpt("Example_Bank_003", 1, "We test models."),
        ]

        with pytest.raises(ValueError, match="both have documents named"):
            build_contexts(excerpts, documents, max_chars=1000)
