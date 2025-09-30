import streamlit as st
import pandas as pd
from core.chunking import default_chunk_size_for, default_overlap_for
from core.models import OPENAI_MODELS

def init_session_state() -> None:
    """Ensure all default session state keys exist with sane defaults."""

    st.session_state.setdefault("busy_file", False)
    st.session_state.setdefault("busy_web", False)

    st.session_state.setdefault("sel_idx", None)
    st.session_state.setdefault("results_df", pd.DataFrame())
    st.session_state.setdefault("results_website_summary", None)
    st.session_state.setdefault("results_master_summary", None)
    st.session_state.setdefault("backup_results_df", pd.DataFrame())
    st.session_state.setdefault("backup_results_website_summary", None)
    st.session_state.setdefault("backup_results_master_summary", None)

    st.session_state.setdefault("enable_individual", True)
    st.session_state.setdefault("enable_master", False)

    # Model-dependent defaults
    st.session_state.setdefault("model_name", "gpt-5-nano")
    st.session_state.setdefault(
        "chunk_size",
        default_chunk_size_for(st.session_state["model_name"], OPENAI_MODELS),
    )
    st.session_state.setdefault(
        "overlap",
        default_overlap_for(st.session_state["chunk_size"]),
    )
    st.session_state.setdefault("strategy", "map-reduce")

def busy() -> bool:
    """Function to determine if the app should be in a 'in progress' state"""
    return st.session_state.busy_file or st.session_state.busy_web

def refresh_chunking_defaults(selected_models):
    st.session_state.chunk_size = default_chunk_size_for(st.session_state.model_name, selected_models)
    st.session_state.overlap    = default_overlap_for(st.session_state.chunk_size)  

def on_chunk_change():
    max_overlap = int(st.session_state.chunk_size * 0.5)
    st.session_state.overlap = min(st.session_state.overlap, max_overlap)