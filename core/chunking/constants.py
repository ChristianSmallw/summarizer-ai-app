from typing import Final

CHUNK_TRIGGER_RATIO:    Final[float] = 0.7      # if text_len > 0.7 * chunk_size → chunk
CHUNK_TARGET_RATIO:     Final[float] = 0.60     # chunk_size ≈ 60% of context window
OVERLAP_RATIO:          Final[float] = 0.12     # overlap ≈ 12% of chunk_size

MIN_CHUNK:              Final[int]   = 512      # floor to avoid silly tiny chunks
MAX_CHUNK:              Final[int]   = 300_000  # UI safety cap on the slider
DEFAULT_FALLBACK_CTX:   Final[int]   = 16_000

DEFAULT_OVERLAP_MIN: Final[int]   = 64