import streamlit as st
import pandas as pd
from core.chunking import default_chunk_size_for, default_overlap_for
from core.models import OPENAI_MODELS
from core.types import ErrorSection, ToastType
import traceback

def init_session_state() -> None:
    """Ensure all default session state keys exist with sane defaults."""

    st.session_state.setdefault("busy_file", False)
    st.session_state.setdefault("busy_web", False)
    st.session_state.setdefault("busy_text", False)

    st.session_state.setdefault("sel_idx", None)
    st.session_state.setdefault("results_df", pd.DataFrame())
    st.session_state.setdefault("results_website_summary", None)
    st.session_state.setdefault("results_master_summary", None)
    st.session_state.setdefault("results_text_summary", None)
    st.session_state.setdefault("results_single_file_name", None)

    st.session_state.setdefault("backup_results_df", pd.DataFrame())
    st.session_state.setdefault("backup_results_website_summary", None)
    st.session_state.setdefault("backup_results_master_summary", None)
    st.session_state.setdefault("backup_results_text_summary", None)
    st.session_state.setdefault("backup_results_single_file_name", None)

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

    st.session_state.setdefault("error", [])
    st.session_state.setdefault("error_toast", ToastType.NONE)

def busy() -> bool:
    """Function to determine if the app should be in a 'in progress' state"""
    return st.session_state.busy_file or st.session_state.busy_web or st.session_state.busy_text

def refresh_chunking_defaults(selected_models):
    st.session_state.chunk_size = default_chunk_size_for(st.session_state.model_name, selected_models)
    st.session_state.overlap    = default_overlap_for(st.session_state.chunk_size)  

def on_chunk_change():
    max_overlap = int(st.session_state.chunk_size * 0.5)
    st.session_state.overlap = min(st.session_state.overlap, max_overlap)

def push_error(msg: str, section: ErrorSection, exc: Exception | None = None):
    st.session_state.error.append({
        "message": msg,
        "section": section,
        "trace": "".join(traceback.format_exception(exc)).strip() if exc else None
    })
    st.session_state.error_toast = ToastType.ERROR

def display_error(section: ErrorSection):
    for err in st.session_state.get("error", []):
        if err["section"] == section:
            st.error(err["message"])
            if err.get("trace"):
                with st.expander("Error Details", icon="🚨"): st.code(err["trace"])

def clear_error(section: ErrorSection):
    errs = st.session_state.get("error", [])
    st.session_state.error = [e for e in errs if e["section"] != section]

def display_toast():
    match st.session_state.error_toast:
        case ToastType.SUCCESS:
            st.toast("Successfully summarized!", icon="🎉")
        case ToastType.ERROR:
            st.toast(f"Something went wrong...", icon="🤔")
        case ToastType.CANCEL:
            st.toast(f"Operation cancelled.", icon="✋")
    st.session_state.error_toast = ToastType.NONE