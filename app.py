import streamlit as st
from utils.summarizer import extract_text_from_url, summarize_text
from utils.text_io import extract_text_from_bytes
import pandas as pd
import time
import os
from io import BytesIO
import zipfile

# --- Model capabilities (tune as you need)
OPENAI_MODELS = {
    "gpt-5-nano":       {"context": 400_000},
    "gpt-5-mini":       {"context": 400_000},
    "gpt-5":             {"context": 400_000},
    "gpt-4o-mini": {"context": 128_000},
    "gpt-4o":      {"context": 128_000},
    "gpt-4.1-mini":{"context": 128_000},
    "gpt-4.1":     {"context": 128_000},
    "gpt-3.5-turbo":{"context": 16_000}
}

LOCAL_MODELS = {
    "gpt-oss:20b_16k":       {"context": 16_384},
    "gpt-oss:20b_32k":       {"context": 32_768}
    # "qwen3:32b":       {"context": 4_000}
}

CHUNK_TRIGGER_RATIO = 0.7      # if text_len > 0.7 * chunk_size → chunk
CHUNK_TARGET_RATIO  = 0.60     # chunk_size ≈ 60% of context window
OVERLAP_RATIO       = 0.12     # overlap ≈ 12% of chunk_size
MIN_CHUNK           = 512      # floor to avoid silly tiny chunks
MAX_CHUNK_CAP       = 300_000  # UI safety cap on the slider

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

def default_chunk_size_for(model_name: str, models) -> int:
    ctx = models.get(model_name, {}).get("context", 16_000)
    return max(MIN_CHUNK, int(ctx * CHUNK_TARGET_RATIO))

def default_overlap_for(chunk_size: int) -> int:
    return max(64, int(chunk_size * OVERLAP_RATIO))

def should_chunk(text_len: int, chunk_size: int) -> bool:
    return text_len > int(chunk_size * CHUNK_TRIGGER_RATIO)

if "model_name" not in st.session_state:
    st.session_state.model_name = "gpt-5-nano"
if "chunk_size" not in st.session_state:
    st.session_state.chunk_size = default_chunk_size_for(st.session_state.model_name, OPENAI_MODELS)
if "overlap" not in st.session_state:
    st.session_state.overlap = default_overlap_for(st.session_state.chunk_size)
if "strategy" not in st.session_state:
    st.session_state.strategy = "map-reduce"

def _busy() -> bool:
    """Function to determine if the app should be in a 'in progress' state"""
    return st.session_state.busy_file or st.session_state.busy_web

def _length_instr(choice: str) -> str:
    """Function to determine prompt length from a select box"""
    if choice.startswith("Short"): return "2–3 sentences"
    if choice.startswith("Medium"): return "1–2 paragraphs"
    return "a detailed, multi-section summary"

def _format_instr(fmt:str) -> str:
    return {
        "Bullets": "Use concise bullet points.",
        "Paragraphs": "Use clear paragraphs.",
        "Headings + bullets": "Use section headings followed by bullet points.",
        "Q&A": "Answer as Q&A pairs.",
        "Table (when possible)": "If structure fits, produce a Markdown table."
    }[fmt]

def _tone_instr(tone:str) -> str:
    return {
        "Neutral":"Neutral, plain style.",
        "Executive":"Executive tone with key metrics.",
        "Technical":"Technical register; keep jargon where precise.",
        "Friendly":"Friendly, approachable.",
        "Persuasive":"Persuasive with compelling language."
    }[tone]

def _focus_instr(focus:list[str]) -> str:
    return "Focus on: " + ", ".join(focus) + "." if focus else "Focus on the main ideas."

def _summary_type(type:str) -> str:
    return{
        "Individual": "Summarize the following content in",
        "Overall": "Give a overall summary for the following file content in "
    }[type]

def build_prompt(type:str, length_choice:str, format_choice:str, tone_choice:str, focus_tags: list[str]) -> str:
    return f"""
    {_summary_type(type)} {_length_instr(length_choice)}.
    {_format_instr(format_choice)} {_tone_instr(tone_choice)} {_focus_instr(focus_tags)}

    Content:
    """

def _summarize_website(url: str, model_name: str, use_local:bool,length_choice: str, format_choice: str, tone_choice: str, focus_tags: list[str], 
                       chunk_strategy: int, chunk_size: int, chunk_overlap: int) -> str:
    from utils.chunking import summarize_in_chunks, token_mode
    st.session_state.sel_idx = None
    st.session_state.results_df = pd.DataFrame()
    st.session_state.results_master_summary = None
    with st.spinner("Fetching and summarizing..."):
        article_text = extract_text_from_url(url)
        if not article_text:
            st.session_state.busy_web = False
            st.error("Could not extract webpage content.")
        else:
            # Optional: skip chunking for short inputs
            use_chunking = True
            if token_mode():
                # if text is tiny (e.g., < 70% of chunk size), skip chunking
                use_chunking = should_chunk(len(article_text), chunk_size)
            else:
                use_chunking = should_chunk(len(article_text), chunk_size)

            if use_chunking:
                summary = summarize_in_chunks(
                    full_text=article_text,
                    prompt_builder=build_prompt,
                    model_name=model_name,
                    use_local=use_local,
                    length_choice=length_choice,
                    format_choice=format_choice,
                    tone_choice=tone_choice,
                    focus_tags=focus_tags,
                    summarize_text_fn=summarize_text,   # your existing function
                    strategy=chunk_strategy,       # from a selectbox, or "map-reduce"
                    chunk_size=chunk_size,         # from a slider, or DEFAULT_CHUNK_SIZE
                    overlap=chunk_overlap          # from a slider, or DEFAULT_OVERLAP
                )
            else:
                summary = summarize_text(article_text, model_name, use_local, prompt=build_prompt("Individual", length_choice, format_choice, tone_choice, focus_tags))
            st.session_state.busy_web = False
            return summary
        
    

def _summarize_files(files, progress_bar, model_name: str, use_local:bool, length_choice: str, format_choice: str, tone_choice: str
                     , focus_tags: list[str], chunk_strategy: int, chunk_size: int, chunk_overlap: int):
    from utils.chunking import summarize_in_chunks, token_mode

    
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
            
            # Optional: skip chunking for short inputs
            use_chunking = True
            if token_mode():
                # if text is tiny (e.g., < 70% of chunk size), skip chunking
                use_chunking = should_chunk(len(text), chunk_size)
            else:
                use_chunking = should_chunk(len(text), chunk_size)

            if use_chunking:
                summary = summarize_in_chunks(
                    full_text=text,
                    prompt_builder=build_prompt,
                    model_name=model_name,
                    use_local=use_local,
                    length_choice=length_choice,
                    format_choice=format_choice,
                    tone_choice=tone_choice,
                    focus_tags=focus_tags,
                    summarize_text_fn=summarize_text,   # your existing function
                    strategy=chunk_strategy,       # from a selectbox, or "map-reduce"
                    chunk_size=chunk_size,         # from a slider, or DEFAULT_CHUNK_SIZE
                    overlap=chunk_overlap          # from a slider, or DEFAULT_OVERLAP
                )
            else:
                summary = summarize_text(text, model_name, use_local, prompt=build_prompt("Individual", length_choice, format_choice, tone_choice, focus_tags))

            #prompt = build_prompt("Individual", length_choice, format_choice, tone_choice, focus_tags)
            #summary = summarize_text(text, prompt=prompt)

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
                    
        # Optional: skip chunking for short inputs
        use_chunking = True
        if token_mode():
            # if text is tiny (e.g., < 70% of chunk size), skip chunking
            use_chunking = should_chunk(len(master_summary_prompt), chunk_size)
        else:
            use_chunking = should_chunk(len(master_summary_prompt), chunk_size)

        if use_chunking:
            st.session_state.results_master_summary = summarize_in_chunks(
                full_text=master_summary_prompt,
                prompt_builder=build_prompt,
                model_name=model_name,
                use_local=use_local,
                length_choice=length_choice,
                format_choice=format_choice,
                tone_choice=tone_choice,
                focus_tags=focus_tags,
                summarize_text_fn=summarize_text,   # your existing function
                strategy=chunk_strategy,       # from a selectbox, or "map-reduce"
                chunk_size=chunk_size,         # from a slider, or DEFAULT_CHUNK_SIZE
                overlap=chunk_overlap          # from a slider, or DEFAULT_OVERLAP
            )
        else:
            st.session_state.results_master_summary = summarize_text(master_summary_prompt, model_name, use_local, prompt=build_prompt("Individual", length_choice, format_choice, tone_choice, focus_tags))

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

def _display_website_summary():
    st.subheader("📝 Website Summary")
    st.write(st.session_state.results_website_summary)
    st.download_button(
    "⬇️ Download Website Summary",
    (st.session_state.results_website_summary or "").encode("utf-8"),
    file_name=f"website_summary.txt",
    width='stretch',
    key=f"dl_website_summary",
    )

def _display_summary_df():

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
                        width='stretch',)

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
        on_select="ignore" if _busy() else "rerun",      
        #on_select="rerun",                
        selection_mode="single-row", 
        key="results_table"
    )

    #reset selected index if out of bounds
    if st.session_state.sel_idx is not None and st.session_state.sel_idx >= len(st.session_state.results_df):
        st.session_state.sel_idx = None

    #Prevent reading from no results
    if _busy():
        return

    # 2) Read the selection dict safely
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
    )
    else:
        st.info("Click a row to view its full summary.")

def _display_master_summary():
    st.subheader("📝 Overall Summary")
    st.write(st.session_state.results_master_summary)
    st.download_button(
    "⬇️ Download Overall Summary",
    (st.session_state.results_master_summary or "").encode("utf-8"),
    file_name=f"OVERALL_SUMMARY.txt",
    width='stretch',
    key=f"dl_overall_summary",
    )


# UI interface

st.set_page_config(page_title="🤖 AI Summarizer", layout="wide")

container_height = 800

# Sidebar AI Model and chunking options
with st.sidebar:
    st.title("⚙️ AI Settings") 
    use_local = st.toggle("Use local models?")
    selected_models = OPENAI_MODELS if not use_local else LOCAL_MODELS
    model_name = st.selectbox(
                            "OpenAI Models" if not use_local else "Local Models",
                            options=list(selected_models),
                            key="model_name",
                            disabled=_busy()
                        )
    
        # When model changes, refresh defaults once (but allow user overrides after)
    def _refresh_chunking_defaults():
        st.session_state.chunk_size = default_chunk_size_for(st.session_state.model_name, selected_models)
        st.session_state.overlap    = default_overlap_for(st.session_state.chunk_size)      

    # Run the refresh when selection changed this render
    if model_name != st.session_state.get("_last_model", None):
        _refresh_chunking_defaults()
    st.session_state._last_model = model_name

    def _on_chunk_change():
        max_overlap = int(st.session_state.chunk_size * 0.5)
        st.session_state.overlap = min(st.session_state.overlap, max_overlap)

    chunk_size = st.slider(
        "Chunk size (tokens)",
        min_value=MIN_CHUNK,
        max_value=min(MAX_CHUNK_CAP, selected_models[model_name]["context"]),
        step=128,
        key="chunk_size",
        on_change=_on_chunk_change(),
        disabled=_busy()
        # help="Target tokens per chunk (we default to ~60% of the model's context)."
    )

    overlap = st.slider(
        "Overlap (tokens)",
        min_value=0,
        max_value=int(chunk_size * 0.5),
        step=64,
        key="overlap",
        disabled=_busy()
        # help="Carry-over tokens from the tail of the previous chunk (defaults ~12% of chunk)."
    )

    strategy = st.selectbox(
        "Chunking strategy",
        options=["map-only", "map-reduce", "map-refine"],
        key="strategy",
        help=(
            "map-only: concat per-chunk summaries\n"
            "map-reduce: combine summaries in a final pass (robust default)\n"
            "map-refine: iterative refinement, preserves details"
        ),
        disabled=_busy()
    )


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
                                disabled=_busy())
        with st.container():

            file_summary_length = st.selectbox(
                                    "Select summary length:",
                                    ["Short (2-3 sentences)", "Medium (1-2 paragraphs)", "Detailed (longer summary)"], 
                                    key="file_summary_length",
                                    disabled=_busy()
                                    )
    file_count = len(files)


    with st.container(horizontal=True):
        file_tone_choice = st.selectbox("Tone/Voice", 
                                     ["Neutral","Executive","Technical","Friendly","Persuasive"],
                                    key="file_tone_choice",
                                    disabled=_busy())
        file_format_choice = st.selectbox("Format", 
                                     ["Paragraphs","Bullets","Headings + bullets","Q&A","Table (when possible)"],
                                    key="file_format_choice",
                                    disabled=_busy())
        file_focus_tags = st.multiselect("Focus (optional)", 
                                    ["Key points","Action items","Pros/Cons","Risks","Entities & facts","Numbers & metrics","Quotes"], 
                                    #default=["Key points","Action items"],
                                    key="file_focus_tags"
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
        
#Website Summarizer Tab

with url_tab:
    with st.container(horizontal=True):
        url = st.text_input(label="Enter URL:", disabled=_busy())
        url_summary_length = st.selectbox(
                    "Select summary length:",
                    ["Short (2-3 sentences)", "Medium (1-2 paragraphs)", "Detailed (longer summary)"], 
                    key="url_summary_length",
                    disabled=_busy()
                    )
    with st.container(horizontal=True):

        web_tone_choice = st.selectbox("Tone/Voice",
                                     ["Neutral","Executive","Technical","Friendly","Persuasive"],
                                    key="web_tone_choice",
                                    disabled=_busy())
        web_format_choice = st.selectbox("Format", 
                                     ["Paragraphs","Bullets","Headings + bullets","Q&A","Table (when possible)"],
                                    key="web_format_choice",
                                    disabled=_busy())
        web_focus_tags = st.multiselect("Focus (optional)", 
                    ["Key points","Action items","Pros/Cons","Risks","Entities & facts","Numbers & metrics","Quotes"], 
                    #default=["Key points","Action items"],
                    key="web_focus_tags")
    url_summarize_btn = st.button("Summarize Website", disabled=_busy())
    if url_summarize_btn and not url.strip():
        st.warning("Please enter a valid URL.")
    elif url_summarize_btn and url.strip():
        st.session_state.busy_web = True
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
                    _display_website_summary()
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


#Execute Summarizing

if st.session_state.busy_file and 'progress_bar' in locals():
    with file_tab:
        try:
            _summarize_files(files, progress_bar, model_name, use_local, file_summary_length, file_format_choice, file_tone_choice, file_focus_tags, 
                             strategy, chunk_size, overlap)
        except Exception as e:
            st.error(f"failed while summarizing files: {e}")
        finally:
            st.session_state.busy_file = False
            st.rerun()
elif st.session_state.busy_web:
    with url_tab:
        try:
            st.session_state.results_website_summary = _summarize_website(url, model_name, use_local, url_summary_length, web_format_choice, web_tone_choice, web_focus_tags,
                                                                        strategy, chunk_size, overlap)
        except Exception as e:
            st.error(f"failed while summarizing website: {e}")
        finally:
            st.session_state.busy_web = False
            st.rerun()

