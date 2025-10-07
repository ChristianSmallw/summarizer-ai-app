# core/types.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

# class Strategy(str, Enum):
#     MAP_ONLY   = "map-only"
#     MAP_REDUCE = "map-reduce"
#     MAP_REFINE = "map-refine"

class ErrorSection(Enum):
    FILE = 1
    URL = 2
    TEXT = 3

class ToastType(Enum):
    NONE = 0
    SUCCESS = 1
    ERROR = 2
    CANCEL = 3


@dataclass
class ModelSettings:
    use_local: bool
    model_name: str
    temperature: float
    reasoning: str
    verbosity: str
    chunk_size: int
    overlap: int
    strategy: str

@dataclass
class PromptSettings:
    summary_length: str 
    format_choice: str 
    tone_choice: str 
    focus_tags: list[str]
    language: str
    include_sections: list[str]
    critique_style: str
    evidence_mode: str
    critique_confidence: int
