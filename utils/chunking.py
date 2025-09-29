from __future__ import annotations
import os
import re
import inspect
from typing import List, Optional, Callable, Protocol

# ---- Tokenizer detection (token-accurate when available; char fallback otherwise)

_ENCODING_NAME = os.getenv("TOKEN_ENCODING", "cl100k_base")

try:
    import tiktoken
    _enc = tiktoken.get_encoding(_ENCODING_NAME)

    def _count_tokens(s: str) -> int:
        return len(_enc.encode(s))

    def _decode_ids_safe(ids: List[int]) -> str:
        """Decode token ids with cautious backoff if needed."""
        # tiktoken.decode is usually safe; guard just in case
        step = len(ids)
        while step > 0:
            try:
                return _enc.decode(ids[:step])
            except Exception:
                step //= 2
        return ""

    def _truncate_head_tokens(s: str, max_tokens: int) -> str:
        """Keep the *last* max_tokens tokens of s (drop from the front)."""
        try:
            ids = _enc.encode(s)
            if max_tokens >= len(ids):
                return s
            keep = ids[-max_tokens:]
            return _decode_ids_safe(keep)
        except Exception:
            return s[-max(0, len(s) // 2):]

    def _truncate_tokens(s: str, max_tokens: int) -> str:
        """Trim to max_tokens on token boundaries; decode safely."""
        try:
            ids = _enc.encode(s)[: max_tokens]
            return _decode_ids_safe(ids)
        except Exception:
            # Ultra-defensive: backoff by halves
            try_max = max_tokens
            while try_max > 0:
                try:
                    ids = _enc.encode(s)[: try_max]
                    return _decode_ids_safe(ids)
                except Exception:
                    try_max //= 2
            return s[: max(0, len(s) // 2)]

    _TOKEN_MODE = True
except Exception:  # pragma: no cover - fallback branch
    _TOKEN_MODE = False

    def _count_tokens(s: str) -> int:
        # Char count as a coarse proxy if no tokenizer is available.
        return len(s)

    def _truncate_tokens(s: str, max_tokens: int) -> str:
        # Char trim as a rough proxy for "tokens".
        return s[:max_tokens]

    def _truncate_head_tokens(s: str, max_tokens: int) -> str:
        # Keep the *last* max_tokens chars
        return s[-max_tokens:] if max_tokens < len(s) else s


def token_mode() -> bool:
    """Expose whether we're chunking by tokens (True) or by characters (False)."""
    return _TOKEN_MODE


def unit_label() -> str:
    """Display unit name for UI ('tokens' or 'characters')."""
    return "tokens" if _TOKEN_MODE else "characters"

# Sensible UI defaults (keep headroom for prompts/system text)
DEFAULT_CHUNK_SIZE = 128000 if _TOKEN_MODE else 2000
DEFAULT_OVERLAP    = 120 if _TOKEN_MODE else 250
# MODEL_CONTEXT_WINDOWS = {
#     "gpt-4o-mini": 128_000,
#     "gpt-4o": 128_000,
#     "gpt-3.5-turbo": 16_000,
#     "qwen3-32b": 32_000,  # example; check HF docs
#     # add more as needed
# }

# def default_chunk_size_for(model: str) -> int:
#     window = MODEL_CONTEXT_WINDOWS.get(model, 4000)
#     return int(window * 0.6)   # use ~60% of capacity per chunk

# ---- Boundary-aware splitting

_PARA_SPLIT = re.compile(r"\r?\n\s*\r?\n")  # handle \n and \r\n

def _split_by_paragraphs(text: str) -> List[str]:
    """
    Split on blank lines, preserving natural boundaries.
    Normalizes Windows newlines and trims empties.
    """
    text = text.strip()
    if not text:
        return []
    parts = _PARA_SPLIT.split(text.replace("\r\n", "\n"))
    return [p.strip() for p in parts if p.strip()]

# Optional: simple sentence splitter for mega-paragraph fallback
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")


def _split_long_paragraph(p: str, target_size: int) -> List[str]:
    """
    If a single paragraph far exceeds target_size, split by sentences to reduce drift.
    """
    # Fast path: if it's within ~1.5x budget, let the packer handle it.
    if _count_tokens(p) <= int(target_size * 1.5):
        return [p]

    sentences = _SENT_SPLIT.split(p)
    if len(sentences) <= 1:
        # No good sentence boundaries; let the packer trim on tokens.
        return [p]

    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for s in sentences:
        s_len = _count_tokens(s)
        if cur_len == 0 or cur_len + s_len <= target_size:
            cur.append(s); cur_len += s_len
        else:
            chunks.append(" ".join(cur).strip())
            cur = [s]; cur_len = s_len
    if cur:
        chunks.append(" ".join(cur).strip())
    return chunks


# ---- Chunk packer

def chunk_text(
    text: str,
    *,
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None,
    hard_max: Optional[int] = None
) -> List[str]:
    """
    Greedy paragraph packer with optional overlap and safety caps.
    - Packs paragraph blocks up to ~chunk_size (tokens or chars per mode).
    - If a single paragraph is huge, we sentence-split it first.
    - Ensures no emitted chunk exceeds chunk_size (final token-trim if needed).
    """
    if chunk_size is None:
        chunk_size = DEFAULT_CHUNK_SIZE
    if overlap is None:
        overlap = DEFAULT_OVERLAP

    paras_raw = _split_by_paragraphs(text)
    # Expand very long paragraphs to sentence-based subparas
    paras: List[str] = []
    for p in paras_raw:
        paras.extend(_split_long_paragraph(p, chunk_size))

    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0

    def _emit_current():
        nonlocal cur, cur_len
        if not cur:
            return
        chunk = "\n\n".join(cur).strip()
        # Final guard: never exceed the budget
        if _count_tokens(chunk) > chunk_size:
            chunk = _truncate_tokens(chunk, chunk_size)
        chunks.append(chunk)
        cur, cur_len = [], 0

    for p in paras:
        p_len = _count_tokens(p)
        if cur_len == 0:
            cur = [p]; cur_len = p_len
            continue

        if cur_len + p_len <= chunk_size:
            cur.append(p); cur_len += p_len
        else:
            _emit_current()
            # Add overlap from previous chunk **tail** (by tokens or chars)
            if overlap > 0 and chunks:
                tail = chunks[-1]
                # take last `overlap` units
                tail_overlap = _truncate_head_tokens(tail, min(overlap, _count_tokens(tail)))
                if tail_overlap:
                    cur = [tail_overlap, p]
                    cur_len = _count_tokens(tail_overlap) + _count_tokens(p)
                else:
                    cur = [p]; cur_len = p_len
            else:
                cur = [p]; cur_len = p_len

    _emit_current()

    if hard_max is not None and hard_max > 0 and len(chunks) > hard_max:
        # Coarse collapse: re-pack into ~even bins rather than blind slicing
        merged = "\n\n".join(chunks)
        target = max(200, len(merged) // hard_max)
        re_packed = chunk_text(merged, chunk_size=target, overlap=0)
        return re_packed[:hard_max]

    return chunks


# ---- High-level map / reduce helpers

def summarize_in_chunks(
    full_text: str,
    prompt_builder: Callable[[str, str, str, str, list[str]], str],
    model_name,
    use_local,
    length_choice: str,
    format_choice: str,
    tone_choice: str,
    focus_tags: list[str],
    summarize_text_fn: Callable[[str, str, bool, str], str],  # accepts (text) or (text, *, prompt="")
    *,
    strategy: str = "map-reduce",   # "map-only" | "map-reduce" | "map-refine"
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None
) -> str:
    """
    Orchestrates chunking + summarization.
    - map-only   : returns concatenated per-chunk summaries
    - map-reduce : final combine pass over chunk summaries (default, robust)
    - map-refine : iterative refinement, preserving prior details
    """
    if chunk_size is None:
        chunk_size = DEFAULT_CHUNK_SIZE
    if overlap is None:
        overlap = DEFAULT_OVERLAP

    chunks = chunk_text(full_text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return ""

    n = len(chunks)
    map_prompt = prompt_builder("Individual", length_choice, format_choice, tone_choice, focus_tags)
    map_summaries: List[str] = []

    # MAP
    for i, ch in enumerate(chunks, start=1):
        p = f"{map_prompt}\nYou are summarizing CHUNK {i}/{n}. Make it standalone and factual."
        s = summarize_text_fn(ch, model_name, use_local, p)
        map_summaries.append(s)

    if strategy == "map-only":
        return "\n\n".join(map_summaries)

    if strategy == "map-refine":
        running = ""
        for i, s in enumerate(map_summaries, start=1):
            refine_instr = (
                "Refine and improve the cumulative summary with the new evidence below. "
                "Preserve important details already captured. Note conflicts explicitly."
            )
            refine_prompt = f"{map_prompt}\n{refine_instr}"
            payload = f"Current cumulative summary:\n{running}\n\nNew chunk summary ({i}/{n}):\n{s}"
            running = summarize_text_fn(payload, model_name, use_local, refine_prompt)
        return running

    # REDUCE (default)
    reduce_prompt = prompt_builder("Overall", length_choice, format_choice, tone_choice, focus_tags)
    combined = "\n\n".join(f"- Chunk {i+1}:\n{cs}" for i, cs in enumerate(map_summaries))
    payload = f"Combine these chunk summaries into a cohesive overall summary:\n\n{combined}\n"
    final = summarize_text_fn(payload, model_name, use_local, reduce_prompt)
    return final
