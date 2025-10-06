# core/chunking/strategies.py
from __future__ import annotations
from .packer import chunk_text
from core.prompts import build_prompt
from utils.summarizer import summarize_text
from core.types import ModelSettings, PromptSettings

def summarize_in_chunks(
    full_text: str,
    model_settings: ModelSettings,
    prompt_settings: PromptSettings
) -> str:
    
    if model_settings.chunk_size is None or model_settings.overlap is None:
        chunks = chunk_text(full_text, chunk_size=model_settings.chunk_size, overlap=model_settings.overlap)
    else:
        chunks = chunk_text(full_text, chunk_size=model_settings.chunk_size, overlap=model_settings.overlap)
    if not chunks:
        return ""

    n = len(chunks)
    map_prompt = build_prompt("Individual", prompt_settings)

    # MAP
    per_chunk = []
    for i, ch in enumerate(chunks, start=1):
        p = f"{map_prompt}\nYou are summarizing CHUNK {i}/{n}. Make it standalone and factual."
        s = summarize_text(ch, model_settings, p)
        per_chunk.append(s)

    if model_settings.strategy == "map-only":
        return "\n\n".join(per_chunk)

    if model_settings.strategy == "map-refine":
        running = ""
        for i, s in enumerate(per_chunk, start=1):
            refine_instr = (
                "Refine and improve the cumulative summary with the new evidence below. "
                "Preserve important details already captured. Note conflicts explicitly."
            )
            refine_prompt = f"{map_prompt}\n{refine_instr}"
            payload = f"Current cumulative summary:\n{running}\n\nNew chunk summary ({i}/{n}):\n{s}"
            running = summarize_text(payload, model_settings, refine_prompt)
        return running

    # map-reduce (default)
    reduce_prompt = build_prompt("Overall", prompt_settings)
    
    combined = "\n\n".join(f"- Chunk {i+1}:\n{cs}" for i, cs in enumerate(per_chunk))
    payload = f"Combine these chunk summaries into a cohesive overall summary:\n\n{combined}\n"
    return summarize_text(payload, model_settings, reduce_prompt)