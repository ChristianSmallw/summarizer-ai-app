# core/chunking/packer.py
from __future__ import annotations
from .tokenizers import (
    count_units, truncate_units, truncate_head_units,
    default_chunk_size, default_overlap
)
from .splitters import split_by_paragraphs, split_long_paragraph

def chunk_text(
    text: str,
    *,
    chunk_size: int | None = None,
    overlap: int | None = None,
    hard_max: int | None = None,
) -> list[str]:
    """
    Greedy paragraph packer with optional overlap and safety caps.
    """
    if chunk_size is None:
        chunk_size = default_chunk_size()
    if overlap is None:
        overlap = default_overlap()

    paras_raw = split_by_paragraphs(text)
    # Expand long paragraphs
    paras: list[str] = []
    for p in paras_raw:
        paras.extend(split_long_paragraph(p, chunk_size))

    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0

    def _emit_current():
        nonlocal cur, cur_len
        if not cur:
            return
        chunk = "\n\n".join(cur).strip()
        if count_units(chunk) > chunk_size:
            chunk = truncate_units(chunk, chunk_size)
        chunks.append(chunk)
        cur, cur_len = [], 0

    for p in paras:
        p_len = count_units(p)
        if cur_len == 0:
            cur, cur_len = [p], p_len
            continue

        if cur_len + p_len <= chunk_size:
            cur.append(p); cur_len += p_len
        else:
            _emit_current()
            if overlap > 0 and chunks:
                tail = chunks[-1]
                tail_overlap = truncate_head_units(tail, min(overlap, count_units(tail)))
                if tail_overlap:
                    cur = [tail_overlap, p]
                    cur_len = count_units(tail_overlap) + count_units(p)
                else:
                    cur, cur_len = [p], p_len
            else:
                cur, cur_len = [p], p_len

    _emit_current()

    if hard_max and hard_max > 0 and len(chunks) > hard_max:
        merged = "\n\n".join(chunks)
        target = max(200, len(merged) // hard_max)
        re_packed = chunk_text(merged, chunk_size=target, overlap=0)
        return re_packed[:hard_max]

    return chunks
