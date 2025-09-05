import streamlit as st
from summarizer import extract_text_from_url, summarize_text  # Import your existing functions

st.set_page_config(page_title="GPT Article Summarizer")

st.title("📰 GPT Article Summarizer")

length = st.selectbox(
    "📝 Select summary length:",
    ["Short (2-3 sentences)", "Medium (1-2 paragraphs)", "Detailed (longer summary)"]
)

url = st.text_input("🔗 Enter the article URL:")

if st.button("Summarize"):
    if not url.strip():
        st.warning("Please enter a valid URL.")
    else:
        with st.spinner("Fetching and summarizing..."):
            article_text = extract_text_from_url(url)
            if not article_text:
                st.error("Could not extract article content.")
            else:
                prompt = f"Summarize this article in a {length.lower()}."
                summary = summarize_text(article_text, prompt=prompt)
                # st.subheader("📄 Cleaned Article Text")
                # st.write(article_text[:3000])  # show first 3000 characters
                st.subheader("📝 Summary")
                st.write(summary)
