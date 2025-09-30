from __future__ import annotations
import os

_ENCODING_NAME = os.getenv("TOKEN_ENCODING", "cl100k_base")

try:
    import tiktoken
    _enc = tiktoken.get_encoding(_ENCODING_NAME)
    _TOKEN_MODE = True

    def count_units(s: str) -> int:
        return len(_enc.encode(s))

    def decode_ids_safe(ids: list[int]) -> str:
        step = len(ids)
        while step > 0:
            try:
                return _enc.decode(ids[:step])
            except Exception:
                step //= 2
        return ""

    def truncate_units(s: str, max_units: int) -> str:
        try:
            ids = _enc.encode(s)[:max_units]
            return decode_ids_safe(ids)
        except Exception:
            try_max = max_units
            while try_max > 0:
                try:
                    ids = _enc.encode(s)[:try_max]
                    return decode_ids_safe(ids)
                except Exception:
                    try_max //= 2
            return s[: max(0, len(s) // 2)]

    def truncate_head_units(s: str, max_units: int) -> str:
        try:
            ids = _enc.encode(s)
            if max_units >= len(ids):
                return s
            keep = ids[-max_units:]
            return decode_ids_safe(keep)
        except Exception:
            return s[-max(0, len(s) // 2):]

except Exception:  # Fallback to character mode
    _TOKEN_MODE = False

    def count_units(s: str) -> int:
        return len(s)

    def truncate_units(s: str, max_units: int) -> str:
        return s[:max_units]

    def truncate_head_units(s: str, max_units: int) -> str:
        return s[-max_units:] if max_units < len(s) else s


def token_mode() -> bool:
    """True = token mode via tiktoken; False = character mode."""
    return _TOKEN_MODE


def unit_label() -> str:
    return "tokens" if _TOKEN_MODE else "characters"


def default_chunk_size() -> int:
    """Conservative defaults that adapt to token/char mode only."""
    # You can tune these to your UX. Keep simple so there's no cross-module import.
    return 128_000 if _TOKEN_MODE else 2_000


def default_overlap() -> int:
    return 120 if _TOKEN_MODE else 250
