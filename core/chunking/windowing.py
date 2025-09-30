from .constants import (
    MIN_CHUNK, OVERLAP_RATIO, CHUNK_TRIGGER_RATIO,
    CHUNK_TARGET_RATIO, DEFAULT_FALLBACK_CTX
)

def default_chunk_size_for(model_name: str, models) -> int:
    ctx = models.get(model_name, {}).get("context", DEFAULT_FALLBACK_CTX)
    return max(MIN_CHUNK, int(ctx * CHUNK_TARGET_RATIO))

def default_overlap_for(chunk_size: int) -> int:
    return max(64, int(chunk_size * OVERLAP_RATIO))

def should_chunk(text_len: int, chunk_size: int) -> bool:
    return text_len > int(chunk_size * CHUNK_TRIGGER_RATIO)