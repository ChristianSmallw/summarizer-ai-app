from core.types import PromptSettings

def _length_instr(choice: str) -> str:
    """Function to determine prompt length from a select box"""
    if choice.startswith("Short"): return "2–3 sentences"
    if choice.startswith("Medium"): return "1–2 paragraphs"
    return "a detailed, multi-section summary"

def _format_instr(fmt:str) -> str:
    return {
        "Bullets": "Use concise bullet points.",
        "Paragraphs": "Use clear paragraphs.",
        "Headings + bullets": "Use section headings followed by bullet points.",
        "Q&A": "Answer as Q&A pairs.",
        "Table (when possible)": "If structure fits, produce a Markdown table."
    }[fmt]

def _tone_instr(tone:str) -> str:
    return {
        "Neutral":"Neutral, plain style.",
        "Executive":"Executive tone with key metrics.",
        "Technical":"Technical register; keep jargon where precise.",
        "Friendly":"Friendly, approachable.",
        "Persuasive":"Persuasive with compelling language."
    }[tone]

def _focus_instr(focus:list[str]) -> str:
    return "Focus on: " + ", ".join(focus) + "." if focus else "Focus on the main ideas."

def _summary_type(type:str) -> str:
    return{
        "Individual": "Summarize the following content in",
        "Overall": "Give a overall summary for the following file content in "
    }[type]

def _build_include_instr(include, style, evidence, conf):
    parts = []

    if "Strengths" in include:
        parts.append("Add **Strengths**: what works well and why.")

    if "Critique" in include:
        tone = {"Gentle":"use respectful, hedged language",
                "Balanced":"be direct but professional",
                "Blunt":"be concise and highly direct"}[style]
        ev = {"None":"", 
              "Quote excerpts":"Cite short quotes to evidence claims.", 
              "Quote + line refs":"Cite short quotes and include line/page refs if available."}[evidence]
        parts.append(
            f"Add **Critique**: {tone}. Focus on content (not author). "
            f"Make criticisms **actionable** and **specific**. {ev} "
            f"Use confidence level ~{conf}/10 (the higher, the less hedging)."
        )

    if "Suggestions" in include:
        parts.append("Add **Suggestions**: concrete edits or steps to resolve each critique.")

    if "Risks / Red flags" in include:
        parts.append("Add **Risks/Red flags**: where this could fail or mislead users.")

    if "Gaps / Missing info" in include:
        parts.append("Add **Gaps/Missing info**: what is needed to make this complete.")

    if "Assumptions" in include:
        parts.append("Add **Assumptions**: implicit premises the author relies on.")

    if "Counterarguments" in include:
        parts.append("Add **Counterarguments/Alt perspectives** briefly.")

    if "Questions" in include:
        parts.append("Add **Questions** the author/stakeholders should answer next.")

    if "Action items" in include:
        parts.append("Add **Action items** as a checklist with owners if inferable.")

    if "Clarity issues" in include:
        parts.append("Add **Clarity issues**: jargon/ambiguity; provide plain-language rewrites.")

    if "Logical fallacies" in include:
        parts.append("Add **Logical issues**: contradictions, fallacies, unsupported leaps.")

    if "Fact-check flags" in include:
        parts.append("Add **Fact-check flags**: list claims that require verification.")

    if "Quality score" in include:
        parts.append("Add **Quality score** (1–5) for Clarity, Evidence, Structure with 1-line rationale each.")

    return "\n".join(f"- {p}" for p in parts)

def build_prompt(type:str, prompt_settings: PromptSettings) -> str:
    return f"""
    {_summary_type(type)} {_length_instr(prompt_settings.summary_length)}.
    {_format_instr(prompt_settings.format_choice)} {_tone_instr(prompt_settings.tone_choice)} {_focus_instr(prompt_settings.focus_tags)}.
    Language: {prompt_settings.language}. If 'Auto', detect language and respond in the same language.

    Also include the following sections if applicable:
    {_build_include_instr(prompt_settings.include_sections, 
                          prompt_settings.critique_style, 
                          prompt_settings.evidence_mode, 
                          prompt_settings.critique_confidence)}

    Content:
    """