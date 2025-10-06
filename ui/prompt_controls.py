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
    with st.container(horizontal=True):
        format_choice = st.selectbox("Format", 
                                     ["Paragraphs","Bullets","Headings + bullets","Q&A","Table (when possible)"],
                                    key=f"{section}_format_choice",
                                    disabled=busy()
                                    )
        focus_tags = st.multiselect("Focus (optional)", 
                                        ["Key points","Action items","Pros/Cons","Risks","Entities & facts","Numbers & metrics","Quotes", "Vibe"], 
                                        #default=["Key points","Action items"],
                                        key=f"{section}_focus_tags",
                                        disabled=busy()
                                        )

    return PromptSettings(
        summary_length=summary_length,
        format_choice=format_choice,
        tone_choice=tone_choice,
        focus_tags=focus_tags
    )