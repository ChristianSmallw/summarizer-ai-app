# core/chunking/splitters.py
from __future__ import annotations
import re
from .tokenizers import count_units

_PARA_SPLIT = re.compile(r"\r?\n\s*\r?\n")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")

def split_by_paragraphs(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = _PARA_SPLIT.split(text.replace("\r\n", "\n"))
    return [p.strip() for p in parts if p.strip()]

def split_long_paragraph(p: str, target_size: int) -> list[str]:
    # Fast path
    if count_units(p) <= int(target_size * 1.5):
        return [p]
    sentences = _SENT_SPLIT.split(p)
    if len(sentences) <= 1:
        return [p]

    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for s in sentences:
        s_len = count_units(s)
        if cur_len == 0 or cur_len + s_len <= target_size:
            cur.append(s); cur_len += s_len
        else:
            chunks.append(" ".join(cur).strip())
            cur, cur_len = [s], s_len
    if cur:
        chunks.append(" ".join(cur).strip())
    return chunks
