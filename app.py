import streamlit as st
from utils.summarizer import extract_text_from_url, summarize_text
from utils.text_io import extract_text_from_bytes
import pandas as pd
import time

#Session States

if "busy_file" not in st.session_state:
    st.session_state.busy_file = False
if "busy_web" not in st.session_state:
    st.session_state.busy_web = False
if "sel_idx" not in st.session_state:
    st.session_state.sel_idx = None
if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
if "results_website_summary" not in st.session_state:
    st.session_state.results_website_summary = None
if "results_master_summary" not in st.session_state:
    st.session_state.results_master_summary = None
if "backup_results_df" not in st.session_state:
    st.session_state.backup_results_df = pd.DataFrame()
if "backup_results_website_summary" not in st.session_state:
    st.session_state.backup_results_website_summary = None
if "backup_results_master_summary" not in st.session_state:
    st.session_state.backup_results_master_summary = None
if "enable_individual" not in st.session_state:
    st.session_state.enable_individual = True
if "enable_master" not in st.session_state:
    st.session_state.enable_master = False

#internal function

def _busy() -> bool:
    return st.session_state.busy_file or st.session_state.busy_web

def _length_instr(choice: str) -> str:
    if choice.startswith("Short"): return "2–3 sentences"
    if choice.startswith("Medium"): return "1–2 paragraphs"
    return "a detailed"

def _summarize_website(url: str) -> str:
    st.session_state.running = True
    st.session_state.sel_idx = None
    st.session_state.results_df = pd.DataFrame()
    st.session_state.results_master_summary = None
    with st.spinner("Fetching and summarizing..."):
        article_text = extract_text_from_url(url)
        if not article_text:
            st.session_state.busy_web = False
            st.error("Could not extract webpage content.")
        else:
            prompt = f"Summarize this page in {_length_instr(length)}:"
            st.session_state.busy_web = False
            return summarize_text(article_text, prompt=prompt)
    

def _summarize_files(files, progress_bar):

    file_count = len(files)
    files_data = []
    master_summary_prompt = ""
    st.session_state.backup_results_website_summary = st.session_state.results_website_summary
    st.session_state.backup_results_df = st.session_state.results_df.copy(deep=True)
    st.session_state.backup_results_master_summary = st.session_state.results_master_summary

    st.session_state.results_website_summary = None
    st.session_state.results_df = pd.DataFrame()
    st.session_state.results_master_summary = None

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
            prompt = f"Give a {_length_instr(length)} summary of the following text:"
            summary = summarize_text(text, prompt=prompt)

            files_data.append({
                "file": meta["filename"],
                "data": file, 
                "type": meta["type"], 
                "size": meta["size_bytes"],
                "original": text,
                "summary": summary
            })
            progress += 1
            progress_bar.progress(progress / progress_steps, text=f"{idx}/{file_count} · {file.name} — Summarized")

    if st.session_state.enable_master:
        progress_bar.progress(progress / progress_steps, text="Building overall summary…")
        prompt = f"Give a {_length_instr(length)} overall summary for all the following text that were extracted from files:"
        st.session_state.results_master_summary = summarize_text(master_summary_prompt, prompt=prompt)
        progress += 1
        progress_bar.progress(progress / progress_steps, text="Overall summary complete")

    progress_bar.progress(1.0, text="✅ Done")
    time.sleep(0.5)
    progress_bar.empty()
    st.toast(f"✅ Finished Summarizing all {file_count} files.")
    st.session_state.sel_idx = None
    st.session_state.results_website_summary = None

    if st.session_state.enable_individual:
        st.session_state.results_df = pd.DataFrame(files_data)

    st.session_state.busy_file = False

def _display_summary_df():
    st.subheader("📝 All Summary Files")
    left, right = st.columns([0.12, 0.88])
    with left:
        st.markdown("**✅ Select**")
    with right:
        st.caption("Tick a row, then see details below.")

    event = st.dataframe(
        st.session_state.results_df[["file","type","size","summary"]],
        hide_index=True,
        use_container_width=True,
        on_select="ignore" if _busy() else "rerun",      
        #on_select="rerun",                
        selection_mode="single-row", 
        key="results_table"
    )

    if _busy():
        return

    # 2) Read the selection dict safely
    rows = (event or {}).get("selection", {}).get("rows", [])
    st.session_state.sel_idx = rows[0] if rows else st.session_state.sel_idx

    # 3) Show expander if we have a selected index
    if st.session_state.sel_idx is not None and 0 <= st.session_state.sel_idx < len(st.session_state.results_df):
        row = st.session_state.results_df.iloc[st.session_state.sel_idx]

        with st.expander(f"Summary — {row['file']}", expanded=True):
            st.write(row["summary"])
    else:
        st.info("Click a row to view its full summary.")

def _display_master_summary():
    st.subheader("📝 Overall Summary")
    st.write(st.session_state.results_master_summary)


# UI interface

st.set_page_config(page_title="AI Summarizer", layout="wide")

container_height = 800

with st.container(horizontal_alignment="center"):
    st.title("📰 AI Summarizer", width=355)
    col_main1, col_main2 = st.columns(2, width=1500)
    with col_main1:
        

        st.header('📥 Summary Input')

        with st.container(height=container_height, border=True):
            file_tab, url_tab = st.tabs(["📁 File Upload", "🔗 URL"])

        with file_tab:
            files = st.file_uploader(label="",
                                    type=["txt", "md", "log", "json", "csv", "html", "htm", "pdf", "docx"],
                                    accept_multiple_files=True,
                                    disabled=_busy())
            file_count = len(files)

            length = st.selectbox(
            "Select summary length:",
            ["Short (2-3 sentences)", "Medium (1-2 paragraphs)", "Detailed (longer summary)"], 
            key="summary_length_files",
            disabled=_busy()
            )


            with st.container(horizontal=True):
                file_summarize_btn = st.button(f"Summarize File" + ("s" if file_count > 1 else ""), disabled=(file_count == 0) or _busy())
                if file_count > 1:
                    st.session_state.enable_individual = st.checkbox(label="Individual Summaries", value=True, disabled=_busy())
                    st.session_state.enable_master = st.checkbox(label="Overall Summary", value=False, disabled=(file_count <= 1) or _busy())

            
            if file_summarize_btn and files and (st.session_state.enable_individual or st.session_state.enable_master or file_count == 1):
                st.session_state.busy_file = True
                st.rerun()
            elif st.session_state.busy_file:
                progress_col1, progress_col2 = st.columns([0.80,0.20])

                with progress_col1:
                    progress_bar = st.progress(0.0 ,text=f"Processing Files…")
                with progress_col2:
                    if st.button("Cancel"):
                        st.session_state.busy_file = False
                        st.session_state.results_website_summary = st.session_state.backup_results_website_summary
                        st.session_state.results_df = st.session_state.backup_results_df
                        st.session_state.results_master_summary = st.session_state.backup_results_master_summary
                        # st.toast(f"❌ Cancelled Summarizing files.")
                        st.rerun()

            elif not st.session_state.enable_individual and not st.session_state.enable_master:
                st.warning("Please check atleast one of the summary options.")
            elif file_count == 0:
                st.warning("Please Select files to summarize above.")
            


        with url_tab:
            url = st.text_input(label="Enter URL:", disabled=_busy())
            length = st.selectbox(
            "Select summary length:",
            ["Short (2-3 sentences)", "Medium (1-2 paragraphs)", "Detailed (longer summary)"], 
            key="summary_length_url",
            disabled=_busy()
            )
            url_summarize_btn = st.button("Summarize Website", disabled=_busy())
            if url_summarize_btn and not url.strip():
                st.warning("Please enter a valid URL.")
            elif url_summarize_btn and url.strip():
                st.session_state.busy_web = True
                st.rerun()
            elif st.session_state.busy_web:
                st.session_state.results_website_summary = _summarize_website(url)
                st.rerun()

    with col_main2:

        has_individual = not st.session_state.results_df.empty
        has_master = bool(st.session_state.results_master_summary)
        has_website_summary = bool(st.session_state.results_website_summary)

        st.header('🧾 Generated Summaries')

        if has_website_summary or has_individual or has_master:
            with st.container(height=container_height, border=True):
                if has_website_summary:
                    (tab_web,) = st.tabs(["Website Summary"])
                    with tab_web:
                        st.subheader("📝 Website Summary")
                        st.write(st.session_state.results_website_summary)
                elif has_individual and has_master:
                    tab_individual, tab_master = st.tabs(["Individual Summaries", "Overall Summary"])
                    with tab_individual:
                        _display_summary_df()
                    with tab_master:
                        _display_master_summary()
                elif has_individual:
                    (tab_individual,) = st.tabs(["Individual Summaries"])
                    with tab_individual:
                        _display_summary_df()
                elif has_master:
                    (tab_master,) = st.tabs(["Overall Summary"])
                    with tab_master:
                        _display_master_summary()
        else:
            with st.container(height=container_height, border=True, horizontal_alignment="center", horizontal=True,vertical_alignment="center"):
                with st.container(width=400):
                    st.image("assets/summary_placeholder.svg", width=300)
                    st.markdown("### Waiting for input...")
                    st.caption("Your generated summary will appear here once ready.")


if st.session_state.busy_file:
    _summarize_files(files, progress_bar)
    st.rerun()