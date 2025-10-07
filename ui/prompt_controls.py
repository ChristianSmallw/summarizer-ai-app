import streamlit as st
from ui.state import busy
from core.types import PromptSettings

def render_prompt_controls(section: str) -> PromptSettings:
        
    with st.container(horizontal=True):
        summary_length = st.selectbox(
                                        "Select summary length:",
                                        ["Short (2-3 sentences)", "Medium (1-2 paragraphs)", "Detailed (longer summary)"], 
                                        key=f"{section}_summary_length",
                                        disabled=busy()
                                        )
        tone_choice = st.selectbox("Tone/Voice",
                                     ["Neutral","Executive","Technical","Friendly","Persuasive"],
                                    key=f"{section}_tone_choice",
                                    disabled=busy()
                                    )
        language    = st.selectbox("Language", 
                                     ["Auto","English","Spanish","French","German"],
                                        key=f"{section}_language",
                                        disabled=busy()
                                    )
    with st.container(horizontal=True):
        format_choice = st.selectbox("Format", 
                                     ["Paragraphs","Bullets","Headings + bullets","Q&A","Table (when possible)"],
                                    key=f"{section}_format_choice",
                                    disabled=busy()
                                    )
        focus_tags = st.multiselect("Focus (optional)", 
                                        ["Key points","Action items","Pros/Cons","Risks","Entities & facts","Numbers & metrics","Quotes", "Emotional texture", "Vibe"], 
                                        #default=["Key points","Action items"],
                                        key=f"{section}_focus_tags",
                                        disabled=busy()
                                        )
        include_sections = st.multiselect(
                                        "Include in summary(optional)",
                                        [
                                            "Strengths",
                                            "Critique",
                                            "Suggestions",
                                            "Risks / Red flags",
                                            "Gaps / Missing info",
                                            "Assumptions",
                                            "Counterarguments",
                                            "Questions",
                                            "Action items",
                                            "Clarity issues",
                                            "Logical fallacies",
                                            "Fact-check flags",
                                            "Quality score"
                                        ],
                                        key=f"{section}_include_sections",
                                        disabled=busy()
                                        #default=["Strengths","Critique","Suggestions","Action items"]
                                   )
    if "Critique" in include_sections:
        with st.container(horizontal=True):

            critique_style = st.selectbox("Critique style", ["Gentle","Balanced","Blunt"], index=1,
                                        key=f"{section}_critique_style",
                                        disabled=busy())

            evidence_mode  = st.selectbox("Evidence mode", ["None","Quote excerpts","Quote + line refs"], index=1,
                                        key=f"{section}_evidence_mode",
                                        disabled=busy())

            critique_confidence = st.slider("Critique confidence\n (0=hedged, 10=direct)", 0, 10, 7,
                                        key=f"{section}_critique_confidence",
                                        disabled=busy())


    return PromptSettings(
        summary_length=summary_length,
        format_choice=format_choice,
        tone_choice=tone_choice,
        focus_tags=focus_tags,
        language=language,
        include_sections=include_sections,
        critique_style=critique_style if "Critique" in include_sections else None,
        evidence_mode=evidence_mode if "Critique" in include_sections else None,
        critique_confidence=critique_confidence if "Critique" in include_sections else None
    )