from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple, cast

import pymupdf
import pymupdf4llm  # pyright: ignore[reportMissingTypeStubs]

PdfInput = Path | pymupdf.Document


class _PyMuPDFBlock(NamedTuple):
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    block_number: int
    block_type: int


def extract_paragraphs(
    pdf: PdfInput,
    remove_newlines: bool = True,
    pages: Iterable[int] | None = None,
) -> list[str]:
    paragraphs: list[str] = []
    with pymupdf.open(pdf) as document:
        if pages is None:
            pages = range(len(document))
        for page_number in pages:
            page = document[page_number]
            raw_blocks = cast(
                list[tuple[float, float, float, float, str, int, int]],
                page.get_text_blocks(sort=True),  # pyright: ignore[reportUnknownMemberType]
            )
            for raw_block in raw_blocks:
                block = _PyMuPDFBlock(*raw_block)
                para = block.text.strip()
                if remove_newlines:
                    para = para.replace("\n", " ")
                paragraphs.append(para)
    return paragraphs


def convert_to_markdown(
    pdf: PdfInput,
    pages: Iterable[int] | None = None,
) -> str:
    return cast(
        str,
        pymupdf4llm.to_markdown(  # pyright: ignore[reportUnknownMemberType]
            pdf, pages=pages
        ),
    )
