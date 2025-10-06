import streamlit as st
from core.prompts import build_prompt
from utils.summarizer import extract_text_from_url, summarize_text
from utils.text_io import extract_text_from_bytes
from core.chunking import summarize_in_chunks, should_chunk
from core.types import ModelSettings, PromptSettings, ErrorSection, ToastType
from ui.state import push_error
import pandas as pd
import time


def summarize_user_text(text: str, model_settings: ModelSettings, prompt_settings: PromptSettings) -> str:

    st.session_state.backup_results_website_summary = st.session_state.results_website_summary
    st.session_state.backup_results_df = st.session_state.results_df.copy(deep=True)
    st.session_state.backup_results_master_summary = st.session_state.results_master_summary
    st.session_state.backup_results_text_summary = st.session_state.results_text_summary

    st.session_state.results_website_summary = None
    st.session_state.results_df = pd.DataFrame()
    st.session_state.results_master_summary = None
    st.session_state.results_text_summary = None

    progress_col1, progress_col2 = st.columns([0.80,0.20])

    with progress_col1:
        progress_bar = st.progress(0.0 ,text=f"Preparing summarization…")
    with progress_col2:
        if st.button("Cancel"):
            st.session_state.busy_text = False
            st.session_state.results_website_summary = st.session_state.backup_results_website_summary
            st.session_state.results_df = st.session_state.backup_results_df
            st.session_state.results_master_summary = st.session_state.backup_results_master_summary
            st.session_state.results_text_summary = st.session_state.backup_results_text_summary
            st.session_state.error_toast = ToastType.CANCEL
            st.rerun()

    use_chunking = should_chunk(len(text), model_settings.chunk_size)

    progress_bar.progress(0.5, text="Summarizing Text…")

    if use_chunking:
        summary = summarize_in_chunks(
            full_text=text,
            model_settings=model_settings,
            prompt_settings=prompt_settings
        )
    else:
        summary = summarize_text(text, 
                                model_settings=model_settings,
                                prompt=build_prompt("Individual", prompt_settings))

    st.session_state.busy_text = False
    st.session_state.error_toast = ToastType.SUCCESS
    progress_bar.progress(1.0, text="✅ Done")
    st.toast(f"✅ Finished Summarizing text")
    time.sleep(0.5)
    progress_bar.empty()

    return summary

def summarize_website(url: str, model_settings: ModelSettings, prompt_settings: PromptSettings) -> str:

    st.session_state.backup_results_website_summary = st.session_state.results_website_summary
    st.session_state.backup_results_df = st.session_state.results_df.copy(deep=True)
    st.session_state.backup_results_master_summary = st.session_state.results_master_summary
    st.session_state.backup_results_text_summary = st.session_state.results_text_summary

    st.session_state.results_website_summary = None
    st.session_state.results_df = pd.DataFrame()
    st.session_state.results_master_summary = None
    st.session_state.results_text_summary = None

    progress_col1, progress_col2 = st.columns([0.80,0.20])

    with progress_col1:
        progress_bar = st.progress(0.0 ,text=f"Extracting text from website…")
    with progress_col2:
        if st.button("Cancel"):
            st.session_state.busy_file = False
            st.session_state.results_website_summary = st.session_state.backup_results_website_summary
            st.session_state.results_df = st.session_state.backup_results_df
            st.session_state.results_master_summary = st.session_state.backup_results_master_summary
            st.session_state.results_text_summary = st.session_state.backup_results_text_summary
            st.session_state.error_toast = ToastType.CANCEL
            st.rerun()

    article_text = extract_text_from_url(url)

    if not article_text:
        st.session_state.busy_web = False
        push_error("Could not extract webpage content.", ErrorSection.URL)
    else:

        use_chunking = should_chunk(len(article_text), model_settings.chunk_size)

        progress_bar.progress(0.5, text="Summarizing website…")

        if use_chunking:
            summary = summarize_in_chunks(
                full_text=article_text,
                model_settings=model_settings,
                prompt_settings=prompt_settings
            )
        else:
            summary = summarize_text(article_text, 
                                     model_settings=model_settings,
                                     prompt=build_prompt("Individual", prompt_settings))

        st.session_state.busy_web = False
        st.session_state.error_toast = ToastType.SUCCESS
        progress_bar.progress(1.0, text="✅ Done")
        st.toast(f"✅ Finished Summarizing website")
        time.sleep(0.5)
        progress_bar.empty()

        return summary

            
def summarize_files(files, model_settings: ModelSettings, prompt_settings: PromptSettings):

    st.session_state.backup_results_website_summary = st.session_state.results_website_summary
    st.session_state.backup_results_df = st.session_state.results_df.copy(deep=True)
    st.session_state.backup_results_master_summary = st.session_state.results_master_summary
    st.session_state.backup_results_text_summary = st.session_state.results_text_summary

    st.session_state.results_website_summary = None
    st.session_state.results_df = pd.DataFrame()
    st.session_state.results_master_summary = None
    st.session_state.results_text_summary = None

    progress_col1, progress_col2 = st.columns([0.80,0.20])

    with progress_col1:
        progress_bar = st.progress(0.0 ,text=f"Processing Files…")
    with progress_col2:
        if st.button("Cancel"):
            st.session_state.busy_file = False
            st.session_state.results_website_summary = st.session_state.backup_results_website_summary
            st.session_state.results_df = st.session_state.backup_results_df
            st.session_state.results_master_summary = st.session_state.backup_results_master_summary
            st.session_state.results_text_summary = st.session_state.backup_results_text_summary
            st.session_state.error_toast = ToastType.CANCEL
            st.rerun()

    file_count = len(files)
    files_data = []
    master_summary_prompt = ""

    if file_count == 1:
        st.session_state.enable_individual = False
        st.session_state.enable_master = True

    progress_steps = file_count
    progress = 0

    if st.session_state.enable_individual:
        progress_steps += file_count
    if st.session_state.enable_master:
        progress_steps += 1
    
    for idx, file in enumerate(files, start=1):

        progress_bar.progress(progress / progress_steps, text=f"{idx}/{file_count} · {file.name} — Extracting…")
        
        data = file.getvalue()
        try:
            text, meta = extract_text_from_bytes(file.name, data)
        except Exception as e:
            st.error(str(e))
            st.stop()
        
        master_summary_prompt += f"#{idx} {meta['filename']}:\n{text}\n\n"

        progress += 1
        progress_bar.progress(progress / progress_steps, text=f"{idx}/{file_count} · {file.name} — Extracted")
        
        if st.session_state.enable_individual:
            
            progress_bar.progress(progress / progress_steps, text=f"{idx}/{file_count} · {file.name} — Summarizing…")
            
            use_chunking = should_chunk(len(text), model_settings.chunk_size)

            if use_chunking:
                summary = summarize_in_chunks(
                    full_text=text,
                    model_settings=model_settings,
                    prompt_settings=prompt_settings
                )
            else:
                summary = summarize_text(text,
                                         model_settings=model_settings,
                                         prompt=build_prompt("Individual", prompt_settings))

            files_data.append({
                "file": meta["filename"],
                "data": file, 
                "type": meta["type"], 
                "size": meta["size_bytes"],
                "original": text,
                "summary": summary,
                "preview": summary[:160] + "..."
            })
            progress += 1
            progress_bar.progress(progress / progress_steps, text=f"{idx}/{file_count} · {file.name} — Summarized")

    if st.session_state.enable_master:
        progress_bar.progress(progress / progress_steps, text="Building overall summary…")
                    
        use_chunking = should_chunk(len(master_summary_prompt), model_settings.chunk_size)

        if use_chunking:
            st.session_state.results_master_summary = summarize_in_chunks(
                full_text=master_summary_prompt,
                model_settings=model_settings,
                prompt_settings=prompt_settings
            )
        else:
            st.session_state.results_master_summary = summarize_text(master_summary_prompt, 
                                                                     model_settings=model_settings,
                                                                     prompt=build_prompt("Overall", prompt_settings))

        progress += 1
        progress_bar.progress(progress / progress_steps, text="Overall summary complete")

    progress_bar.progress(1.0, text="✅ Done")
    st.toast(f"✅ Finished Summarizing all {file_count} files.")
    time.sleep(0.5)
    progress_bar.empty()
    st.session_state.sel_idx = None
    st.session_state.results_website_summary = None

    if st.session_state.enable_individual:
        st.session_state.results_df = pd.DataFrame(files_data)

    st.session_state.error_toast = ToastType.SUCCESS