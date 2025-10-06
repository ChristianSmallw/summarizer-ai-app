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

def build_prompt(type:str, prompt_settings: PromptSettings) -> str:
    return f"""
    {_summary_type(type)} {_length_instr(prompt_settings.summary_length)}.
    {_format_instr(prompt_settings.format_choice)} {_tone_instr(prompt_settings.tone_choice)} {_focus_instr(prompt_settings.focus_tags)}.
    Language: {prompt_settings.language}. If 'Auto', detect language and respond in the same language.

    Content:
    """