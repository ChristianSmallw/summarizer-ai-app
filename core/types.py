# core/types.py
from __future__ import annotations
from dataclasses import dataclass
# from enum import Enum

# class Strategy(str, Enum):
#     MAP_ONLY   = "map-only"
#     MAP_REDUCE = "map-reduce"
#     MAP_REFINE = "map-refine"

@dataclass
class ModelSettings:
    use_local: bool
    model_name: str
    chunk_size: int
    overlap: int
    strategy: str

class PromptSettings:
    length_choice: str 
    format_choice: str 
    tone_choice: str 
    focus_tags: list[str]
