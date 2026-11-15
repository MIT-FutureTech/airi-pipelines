import math
from collections import defaultdict

from org_mitigations.excerpts import Excerpt


def group_excerpts(excerpts: list[Excerpt], *, max_chars: int) -> list[list[Excerpt]]:
    by_document: defaultdict[str, list[Excerpt]] = defaultdict(list)
    for excerpt in excerpts:
        by_document[excerpt.document_id].append(excerpt)

    groups: list[list[Excerpt]] = []
    group: list[Excerpt] = []
    size = 0
    for document_excerpts in by_document.values():
        for piece in _split_evenly(document_excerpts, max_chars=max_chars):
            piece_size = _size(piece)
            if group and size + piece_size > max_chars:
                groups.append(group)
                group = []
                size = 0
            group.extend(piece)
            size += piece_size
    if group:
        groups.append(group)
    return groups


def _split_evenly(excerpts: list[Excerpt], *, max_chars: int) -> list[list[Excerpt]]:
    total = _size(excerpts)
    count = max(1, math.ceil(total / max_chars))
    target = total / count
    pieces: list[list[Excerpt]] = []
    piece: list[Excerpt] = []
    size = 0
    for excerpt in excerpts:
        if piece and size + len(excerpt.text) > target and len(pieces) < count - 1:
            pieces.append(piece)
            piece = []
            size = 0
        piece.append(excerpt)
        size += len(excerpt.text)
    pieces.append(piece)
    return pieces


def _size(excerpts: list[Excerpt]) -> int:
    return sum(len(excerpt.text) for excerpt in excerpts)
