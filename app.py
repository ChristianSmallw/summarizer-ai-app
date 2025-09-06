import streamlit as st
from summarizer import extract_text_from_url, summarize_text  # Import your existing functions
from io import StringIO


# UI interface

st.set_page_config(page_title="GPT Article Summarizer")

st.title("📰 GPT Article Summarizer")

st.header('Upload a file or enter URL to summarize.')

length = st.selectbox(
    "📝 Select summary length:",
    ["Short (2-3 sentences)", "Medium (1-2 paragraphs)", "Detailed (longer summary)"]
)

col_input1, col_input2 = st.columns(2)

with col_input1:
    file = st.file_uploader(label="📁 File Upload:", type=["txt", "md", "log"]) #

with col_input2:
    url = st.text_input(label="🔗 Enter URL:", disabled=file is not None)
    summarize_btn = st.button("Summarize")


#Summarize code event

if summarize_btn:
    if file is not None:
        with st.spinner("Fetching and summarizing..."):
            file_text = StringIO(file.getvalue().decode("utf-8")).read()
            st.write(file_text)
            prompt = f"Summarize the following text in a {length.lower()}:"
            summary = summarize_text(file_text, prompt=prompt)
            st.subheader("📝 Summary")
            st.write(summary)
    elif url.strip():
        with st.spinner("Fetching and summarizing..."):
            article_text = extract_text_from_url(url)
            if not article_text:
                st.error("Could not extract webpage content.")
            else:
                prompt = f"Summarize this page in a {length.lower()}:"
                summary = summarize_text(article_text, prompt=prompt)
                # st.subheader("📄 Cleaned Article Text")
                # st.write(article_text[:3000])  # show first 3000 characters
                st.subheader("📝 Summary")
                st.write(summary)
    elif not url.strip():
        st.warning("Please enter a valid URL.")