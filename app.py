import streamlit as st
from utils.summarizer import extract_text_from_url, summarize_text
from utils.text_io import extract_text_from_bytes


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
    file = st.file_uploader(label="📁 File Upload:", type=["txt", "md", "log", "json", "csv", "html", "htm", "pdf", "docx"])

with col_input2:
    url = st.text_input(label="🔗 Enter URL:", disabled=file is not None)
    summarize_btn = st.button("Summarize")

#internal function

def _length_instr(choice: str) -> str:
    if choice.startswith("Short"): return "2–3 sentences"
    if choice.startswith("Medium"): return "1–2 paragraphs"
    return "a detailed summary for as long as you can. When you stop making sense, start screaming and begging to be set free"

#Summarize code event

if summarize_btn:
    if file is not None:
        data = file.getvalue()
        try:
            with st.spinner("Extracting text from file…"):
                text, meta = extract_text_from_bytes(file.name, data)
        except Exception as e:
            st.error(str(e))
            st.stop()
        st.caption(f"{meta['filename']} • {meta['type']} • {meta['size_bytes']:,} bytes")
        prompt = f"Summarize the following text in {_length_instr(length)}:"
        with st.spinner("Summarizing…"):
            summary = summarize_text(text, prompt=prompt)
        # st.subheader("🔍 Preview")
        # st.write(text[:1000])
        st.subheader("📝 Summary")
        st.write(summary)
    elif url.strip():
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
    elif not url.strip():
        st.warning("Please enter a valid URL.")