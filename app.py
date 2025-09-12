import streamlit as st
from utils.summarizer import extract_text_from_url, summarize_text
from utils.text_io import extract_text_from_bytes
import pandas as pd
import time

#internal function

def _length_instr(choice: str) -> str:
    if choice.startswith("Short"): return "2–3 sentences"
    if choice.startswith("Medium"): return "1–2 paragraphs"
    return "a detailed summary."

def summarize_website(url: str) -> str:
    st.session_state.sel_idx = None
    st.session_state.results_df = pd.DataFrame()
    st.session_state.results_master_summary = None
    with st.spinner("Fetching and summarizing..."):
        article_text = extract_text_from_url(url)
        if not article_text:
            st.error("Could not extract webpage content.")
        else:
            prompt = f"Summarize this page in {_length_instr(length)}:"
            return summarize_text(article_text, prompt=prompt)

#Session States

if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
if "sel_idx" not in st.session_state:
    st.session_state.sel_idx = None
if "results_website_summary" not in st.session_state:
    st.session_state.results_website_summary = None
if "results_master_summary" not in st.session_state:
    st.session_state.results_master_summary = None
if "enable_individual" not in st.session_state:
    st.session_state.enable_individual = True
if "enable_master" not in st.session_state:
    st.session_state.enable_master = False

# UI interface

st.set_page_config(page_title="AI Summarizer")

st.title("📰 AI Summarizer")

st.header('Upload a file or enter URL to summarize.')

length = st.selectbox(
    "📝 Select summary length:",
    ["Short (2-3 sentences)", "Medium (1-2 paragraphs)", "Detailed (longer summary)"]
)

col_input1, col_input2 = st.columns(2)

with st.container(height=400):
    file_tab, url_tab = st.tabs(["📁 File Upload", "🔗 URL"])


# with col_input1:
#    files = st.file_uploader(label="📁 File Upload:",
#                             type=["txt", "md", "log", "json", "csv", "html", "htm", "pdf", "docx"],
#                             accept_multiple_files=True)

# with col_input2:
#    url = st.text_input(label="🔗 Enter URL:", disabled=(files is not None))
#    summarize_btn = st.button("Summarize")


with file_tab:
    files = st.file_uploader(label="",
                            type=["txt", "md", "log", "json", "csv", "html", "htm", "pdf", "docx"],
                            accept_multiple_files=True)

    with st.container(horizontal=True):
        file_summarize_btn = st.button(f"Summarize File" + ("s" if len(files) > 1 else ""), disabled=(len(files) == 0))
        if len(files) > 1:
            st.session_state.enable_individual = st.checkbox(label="Individual Summaries", value=True)
            st.session_state.enable_master = st.checkbox(label="Master Summary", value=False, disabled=(len(files) <= 1))


with url_tab:
    url = st.text_input(label="Enter URL:")
    url_summarize_btn = st.button("Summarize Website")
    if url_summarize_btn and not url.strip():
        st.warning("Please enter a valid URL.")
    elif url_summarize_btn and url.strip():
        st.session_state.results_website_summary = summarize_website(url)

#Summarize code event

if file_summarize_btn and files and (st.session_state.enable_individual or st.session_state.enable_master):
    file_count = len(files)
    files_data = []
    st.session_state.results_website_summary = None
    st.session_state.results_df = pd.DataFrame()
    st.session_state.results_master_summary = None
    master_summary_prompt = ""

    progress_steps = file_count
    progress = 0

    if st.session_state.enable_individual:
        progress_steps += file_count
    if st.session_state.enable_master:
        progress_steps += 1

    my_bar = st.progress(0.0 ,text=f"Processing Files…")

    for idx, file in enumerate(files, start=1):

        my_bar.progress(progress / progress_steps, text=f"{idx}/{file_count} · {file.name} — Extracting…")
        
        data = file.getvalue()
        try:
            text, meta = extract_text_from_bytes(file.name, data)
        except Exception as e:
            st.error(str(e))
            st.stop()
        
        master_summary_prompt += f"#{idx} {meta['filename']}:\n{text}\n\n"

        progress += 1
        my_bar.progress(progress / progress_steps, text=f"{idx}/{file_count} · {file.name} — Extracted")

        if st.session_state.enable_individual:
            my_bar.progress(progress / progress_steps, text=f"{idx}/{file_count} · {file.name} — Summarizing…")
            prompt = f"Summarize the following text in {_length_instr(length)}:"
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
            my_bar.progress(progress / progress_steps, text=f"{idx}/{file_count} · {file.name} — Summarized")

    if st.session_state.enable_master:
        my_bar.progress(progress / progress_steps, text="Building master summary…")
        prompt = f"Give a detailed master summary for all the following text that were extracted from files:"
        st.session_state.results_master_summary = summarize_text(master_summary_prompt, prompt=prompt)
        progress += 1
        my_bar.progress(progress / progress_steps, text="Master summary complete")

    my_bar.progress(1.0, text="✅ Done")
    time.sleep(0.5)
    my_bar.empty()
    st.toast(f"✅ Finished Summarizing all {file_count} files.")
    st.session_state.sel_idx = None
    st.session_state.results_website_summary = None

    if st.session_state.enable_individual:
        st.session_state.results_df = pd.DataFrame(files_data)
elif not st.session_state.enable_individual and not st.session_state.enable_master:
    st.warning("Please check atleast one of the summary options.")


if st.session_state.results_website_summary is not None:
    st.subheader("📝 Website Summary")
    st.write(st.session_state.results_website_summary)


def display_summary_df():
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
        on_select="rerun",           # triggers rerun on click
        selection_mode="single-row", # crucial
        key="results_table"
    )

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

def display_master_summary():
    st.subheader("📝 Master Summary")
    st.write(st.session_state.results_master_summary)

# --- render tabs depending on what you have ---
has_individual = not st.session_state.results_df.empty
has_master = bool(st.session_state.results_master_summary)

if has_individual and has_master:
    tab_individual, tab_master = st.tabs(["Individual Summaries", "Master Summary"])
    with tab_individual:
        display_summary_df()
    with tab_master:
        display_master_summary()
elif has_individual:
    (tab_individual,) = st.tabs(["Individual Summaries"])
    with tab_individual:
        display_summary_df()
elif has_master:
    (tab_master,) = st.tabs(["Master Summary"])
    with tab_master:
        display_master_summary()