import streamlit as st
from ui.state import busy
from core.types import ToastType
from io import BytesIO
import zipfile
import os

def display_website_summary():
    summary_header_col1, summary_header_col2 = st.columns([0.50,0.50    ])

    with summary_header_col1:
        st.subheader("📝 Website Summary", width="content")
    
    with summary_header_col2:
        summary_buttons_container = st.container(horizontal=True, horizontal_alignment="right")

    with summary_buttons_container:
        st.download_button(
        "⬇️ Download Summary",
        (st.session_state.results_website_summary or "").encode("utf-8"),
        file_name=f"website_summary.txt",
        width='content',
        key=f"dl_website_summary",
        disabled=busy(),
        )

    with st.expander("📋 View and copy raw summary"):
        st.code(st.session_state.results_website_summary or "", language=None)

    st.write(st.session_state.results_website_summary)


def display_text_summary():
    summary_header_col1, summary_header_col2 = st.columns([0.50,0.50    ])

    with summary_header_col1:
        st.subheader("📝 Text Summary")
    
    with summary_header_col2:
        summary_buttons_container = st.container(horizontal=True, horizontal_alignment="right")

    with summary_buttons_container:
        st.download_button(
        "⬇️ Download Summary",
        (st.session_state.results_text_summary or "").encode("utf-8"),
        file_name=f"text_summary.txt",
        width='content',
        key=f"dl_text_summary",
        disabled=busy(),
        )

    with st.expander("📋 View and copy raw summary"):
        st.code(st.session_state.results_text_summary or "", language=None)
    
    st.write(st.session_state.results_text_summary)


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
                        disabled=busy()
                        )

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

            summary_header_col1, summary_header_col2 = st.columns([0.50,0.50])

            with summary_header_col1:
                with st.expander("📋 View and copy raw summary"):
                    st.code(row["summary"] or "", language=None)

            with summary_header_col2:
                st.download_button(
                "⬇️ Download Summary",
                (row["summary"] or "").encode("utf-8"),
                file_name=f"{filename}_summary.txt",
                width='stretch',
                key=f"dl_{filename}_summary",
                disabled=busy()
                )

            st.write(row["summary"])
            
    else:
        st.info("Click a row to view its full summary.")

def display_master_summary(single_file_name: str = None):
    summary_header_col1, summary_header_col2 = st.columns([0.50,0.50])
    is_single_file = single_file_name is not None

    with summary_header_col1:
        st.subheader(f"📝 {'File' if single_file_name else 'Master'} Summary", width="content")
    
    with summary_header_col2:
        summary_buttons_container = st.container(horizontal=True, horizontal_alignment="right")
    
    with summary_buttons_container:
        st.download_button(
        f"⬇️ Download Summary",
        (st.session_state.results_master_summary or "").encode("utf-8"),
        file_name=f"Master_Summary.txt" if not is_single_file else f"{single_file_name}_summary.txt",
        width='content',
        key=f"dl_master_summary",
        disabled=busy()
        )
    
    with st.expander("📋 View and copy raw summary"):
        st.code(st.session_state.results_master_summary or "", language=None)

    st.write(st.session_state.results_master_summary)

