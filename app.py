import streamlit as st
from ui.sidebar import render_sidebar
from ui.prompt_controls import render_prompt_controls
from core.types import ModelSettings, ErrorSection, ToastType
from ui.state import init_session_state, busy, push_error, display_error, clear_error, display_toast
from ui.summarization_controller import summarize_website, summarize_files
from ui.output import display_website_summary, display_summary_df, display_master_summary
import os

#Initialize default values for all session state keys
init_session_state()

# UI interface

st.set_page_config(page_title="🤖 AI Summarizer", layout="wide")

container_height = 800

# Sidebar AI Model and chunking options
sidebar_settings = render_sidebar()


main = st.container(horizontal_alignment="center")

with main:
    st.title("🤖 AI Summarizer", width=355) 
    col_main1, col_main2 = st.columns(2, width=1500)

with col_main1:
    st.header('📥 Summary Input')
    left_input = st.container(height=container_height, border=True)

with left_input:
    file_tab, url_tab = st.tabs(["📁 File Upload", "🔗 URL"])

#File Summarizer Tab

with file_tab:
    with st.container(horizontal=True):
        files = st.file_uploader(label="Upload Files to summarize:",
                                type=["txt", "md", "log", "json", "csv", "html", "htm", "pdf", "docx"],
                                accept_multiple_files=True,
                                disabled=busy())
    file_count = len(files)


    prompt_settings = render_prompt_controls("file")

    with st.container(horizontal=True):
        file_summarize_btn = st.button(f"Summarize File" + ("s" if file_count > 1 else ""), disabled=(file_count == 0) or busy())
        if file_count > 1:
            st.session_state.enable_individual = st.checkbox(label="Individual Summaries", value=True, disabled=busy())
            st.session_state.enable_master = st.checkbox(label="Overall Summary", value=False, disabled=(file_count <= 1) or busy())

    
    if file_summarize_btn and files and (st.session_state.enable_individual or st.session_state.enable_master or file_count == 1):
        st.session_state.busy_file = True
        clear_error(ErrorSection.FILE)
        st.rerun()
    elif not st.session_state.enable_individual and not st.session_state.enable_master:
        st.warning("Please check atleast one of the summary options.")
    elif file_count == 0:
        st.warning("Please Select files to summarize above.")

    display_error(ErrorSection.FILE)
        
#Website Summarizer Tab

with url_tab:
    url = st.text_input(label="Enter URL:", disabled=busy())

    prompt_settings = render_prompt_controls("url")
    
    url_summarize_btn = st.button("Summarize Website", disabled=busy())
    display_error(ErrorSection.URL)

    if url_summarize_btn and not url.strip():
        st.warning("Please enter a valid URL.")
    elif url_summarize_btn and url.strip():
        st.session_state.busy_web = True
        clear_error(ErrorSection.URL)
        st.rerun()



has_individual = not st.session_state.results_df.empty
has_master = bool(st.session_state.results_master_summary)
has_website_summary = bool(st.session_state.results_website_summary)

#Results Panel

with col_main2:
    st.header('🧾 Generated Summaries')

    if has_website_summary or has_individual or has_master:
        with st.container(height=container_height, border=True):
            if has_website_summary:
                (tab_web,) = st.tabs(["Website Summary"])
                with tab_web:
                    display_website_summary()
            elif has_individual and has_master:
                tab_individual, tab_master = st.tabs(["Individual Summaries", "Overall Summary"])
                with tab_individual:
                    display_summary_df()
                with tab_master:
                    display_master_summary()
            elif has_individual:
                (tab_individual,) = st.tabs(["Individual Summaries"])
                with tab_individual:
                    display_summary_df()
            elif has_master:
                (tab_master,) = st.tabs(["Overall Summary"])
                with tab_master:
                    display_master_summary()
    else:
        with st.container(height=container_height, border=True, horizontal_alignment="center", 
                          horizontal=True,vertical_alignment="center"):
            with st.container(width=400):
                st.image("assets/summary_placeholder.svg", width=300)
                st.markdown("### Waiting for input...")
                st.caption("Your generated summary will appear here once ready.")

display_toast()

#Execute Summarizing

if st.session_state.busy_file:
    with file_tab:
        try:
            summarize_files(files, sidebar_settings, prompt_settings)
        except Exception as e:
            push_error(f"Failed while summarizing files.", ErrorSection.FILE, e)
        finally:
            st.session_state.busy_file = False
            st.rerun()
elif st.session_state.busy_web:
    with url_tab:
        try:
            st.session_state.results_website_summary = summarize_website(url, sidebar_settings, prompt_settings)
        except Exception as e:
            push_error(f"Failed while summarizing website.", ErrorSection.URL, e)
        finally:
            st.session_state.busy_web = False
            st.rerun()