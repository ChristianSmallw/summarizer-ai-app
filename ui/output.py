import streamlit as st
from ui.state import busy
from io import BytesIO
import zipfile
import os

def display_website_summary():
    st.subheader("📝 Website Summary")
    st.write(st.session_state.results_website_summary)
    st.download_button(
    "⬇️ Download Website Summary",
    (st.session_state.results_website_summary or "").encode("utf-8"),
    file_name=f"website_summary.txt",
    width='stretch',
    key=f"dl_website_summary",
    disabled=busy(),
    )

def display_summary_df():

    summary_header_col1, summary_header_col2 = st.columns([0.50,0.50    ])

    with summary_header_col1:
        st.subheader("📝 All Summary Files")

    with summary_header_col2:
        mem_zip = BytesIO()
        with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for r in st.session_state.results_df.itertuples(index=False):
                filename, ext = os.path.splitext(getattr(r, "file"))
                safe = filename.replace("/", "_")
                zf.writestr(f"{safe}__summary.txt", getattr(r, "summary"))
            if st.session_state.results_master_summary:
                zf.writestr("MASTER_SUMMARY.txt", st.session_state.results_master_summary)
        mem_zip.seek(0)
        st.download_button("⬇️ Download all summaries (ZIP📦)", 
                        data=mem_zip, 
                        file_name="summaries.zip", 
                        mime="application/zip",
                        width='stretch',
                        disabled=busy())

    left, right = st.columns([0.12, 0.88])
    with left:
        st.markdown("**✅ Select**")
    with right:
        st.caption("Tick a row, then see details below.")

    #display files in dataframe
    event = st.dataframe(
        st.session_state.results_df[["file","type","size","preview"]],
        hide_index=True,
        width='stretch',
        on_select="ignore" if busy() else "rerun",      
        #on_select="rerun",                
        selection_mode="single-row", 
        key="results_table"
    )

    #reset selected index if out of bounds
    if st.session_state.sel_idx is not None and st.session_state.sel_idx >= len(st.session_state.results_df):
        st.session_state.sel_idx = None

    # 2) Read the selection dict safely
    if not busy():
        rows = (event or {}).get("selection", {}).get("rows", [])
        st.session_state.sel_idx = rows[0] if rows else st.session_state.sel_idx

    # 3) Show expander if we have a selected index
    if st.session_state.sel_idx is not None and 0 <= st.session_state.sel_idx < len(st.session_state.results_df):
        row = st.session_state.results_df.iloc[st.session_state.sel_idx]
        filename, ext = os.path.splitext(row["file"])
        with st.expander(f"Summary — {row['file']}", expanded=True):
            st.write(row["summary"])
            st.download_button(
            "⬇️ Download Summary",
            (row["summary"] or "").encode("utf-8"),
            file_name=f"{filename}_summary.txt",
            width='stretch',
            key=f"dl_{filename}_summary",
            disabled=busy()
    )
    else:
        st.info("Click a row to view its full summary.")

def display_master_summary():
    st.subheader("📝 Overall Summary")
    st.write(st.session_state.results_master_summary)
    st.download_button(
    "⬇️ Download Overall Summary",
    (st.session_state.results_master_summary or "").encode("utf-8"),
    file_name=f"OVERALL_SUMMARY.txt",
    width='stretch',
    key=f"dl_overall_summary",
    disabled=busy()
    )