import streamlit as st
from utils.summarizer import extract_text_from_url, summarize_text
from utils.text_io import extract_text_from_bytes
import pandas as pd

#Session States

if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame(columns=["file","type","size","summary"])
if "sel_idx" not in st.session_state:
    st.session_state.sel_idx = None

# UI interface

st.set_page_config(page_title="GPT Article Summarizer")

st.title("📰 AI Summarizer")

st.header('Upload a file or enter URL to summarize.')

length = st.selectbox(
    "📝 Select summary length:",
    ["Short (2-3 sentences)", "Medium (1-2 paragraphs)", "Detailed (longer summary)"]
)

col_input1, col_input2 = st.columns(2)

with col_input1:
    files = st.file_uploader(label="📁 File Upload:",
                             type=["txt", "md", "log", "json", "csv", "html", "htm", "pdf", "docx"],
                             accept_multiple_files=True)

with col_input2:
    url = st.text_input(label="🔗 Enter URL:", disabled=(files is not None))
    summarize_btn = st.button("Summarize")

#internal function

def _length_instr(choice: str) -> str:
    if choice.startswith("Short"): return "2–3 sentences"
    if choice.startswith("Medium"): return "1–2 paragraphs"
    return "a detailed summary."

#Summarize code event

if summarize_btn and files:
    file_count = len(files)
    files_data = []
    for idx, file in enumerate(files):
        data = file.getvalue()
        try:
            with st.spinner(f"Extracting text from file({idx + 1}/{file_count})…"):
                text, meta = extract_text_from_bytes(file.name, data)
        except Exception as e:
            st.error(str(e))
            st.stop()
        #st.caption(f"{meta['filename']} • {meta['type']} • {meta['size_bytes']:,} bytes")
        prompt = f"Summarize the following text in {_length_instr(length)}:"
        with st.spinner(f"Summarizing({idx + 1}/{file_count})…"):
            summary = summarize_text(text, prompt=prompt)

        files_data.append({
            "file": meta["filename"],
            "data": file, 
            "type": meta["type"], 
            "size": meta["size_bytes"], 
            "summary": summary
        })

    st.session_state.results_df = pd.DataFrame(files_data)
    # --- Interactive table with selection ---
    # selection = st.dataframe(
    #     df[["file", "type", "size", "summary"]],  # show only needed cols
    #     use_container_width=True,
    #     hide_index=True,
    #     on_select="rerun",
    #     selection_mode="single-row",
    #     key="results_table"
    # )

    # tabs = st.tabs([f"{file['meta']['filename']}_summary" for file in file_data])
    # for idx,tab in enumerate(tabs):
    #     with tab:        
    #         st.subheader("📝 Summary")
    #         st.write(file_data[idx]["summary"])
if summarize_btn and url.strip():
    with st.spinner("Fetching and summarizing..."):
        article_text = extract_text_from_url(url)
        if not article_text:
            st.error("Could not extract webpage content.")
        else:
            prompt = f"Summarize this page in {_length_instr(length)}:"
            summary = summarize_text(article_text, prompt=prompt)
            # st.subheader("📄 Cleaned Article Text")
            # st.write(article_text[:3000])  # show first 3000 characters
            st.subheader("📝 Summary")
            st.write(summary)
#elif summarize_btn and not url.strip():
    #st.warning("Please enter a valid URL.")

# ---------- RENDER (always) ----------
df = st.session_state.results_df

#if df.empty:
    #st.info("Upload files and click Summarize.")
if not df.empty:
    # 1) Show interactive table. Put it OUTSIDE the button block.
    event = st.dataframe(
        df[["file","type","size","summary"]],
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
    if st.session_state.sel_idx is not None and 0 <= st.session_state.sel_idx < len(df):
        row = df.iloc[st.session_state.sel_idx]
        with st.expander(f"Details — {row['file']}", expanded=True):
            st.subheader("Summary")
            st.write(row["summary"])
    else:
        st.info("Click a row to view its full summary.")