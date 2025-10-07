# ֎ AI Summarizer

A **Streamlit app** that uses local or cloud AI models to summarize batch documents, web pages, or text.

<img width="1919" height="918" alt="Summarizer_app_picture" src="https://github.com/user-attachments/assets/2a1a1a1c-2572-4da7-aa22-be13416f99d0" />

---

## 🚀 Features
- **Multiple Input Modes:** Upload files (`.txt`, `.pdf`, `.docx`, `.json`, `.csv`, etc.), fetch from URL, or paste text.  
- **Master and per-file summaries:** Generate both individual summaries and a master summary of all files.
- **Model Options:** Choose between OpenAI or local models (via Ollama).  
- **Customizable Summaries:** Adjust summary length, tone, language, format, focus, verbosity, reasoning depth, temperature.  
- **Chunking Control:** Token-aware splitting with adjustable chunk size, overlap, and strategy (`map-reduce` or sequential).  

## 🧩 Tech Stack
- **Frontend:** Streamlit  
- **Backend:** FastAPI (optional for API access)  
- **Language:** Python 3.10+  
- **Libraries:** `openai`, `streamlit`, `fastapi`, `pandas`, `pypdf`, `python-docx`, `tiktoken`, `beautifulsoup4`, etc."

## 🔗 Live Demo

👉 [**Try it on Streamlit Cloud**](https://summarizer-ai-app-ggkyt5pqyjmy4ghudryohu.streamlit.app)

## 🖥️ Running Locally
```bash
# 1. Clone the repo
git clone https://github.com/ChristianSmallw/summarizer-ai-app.git
cd summarizer-ai-app

# 2. (Optional but recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows
# or
source venv/bin/activate  # On macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file in the project root and add your OpenAI API key
# Example:
echo OPENAI_API_KEY=your_openai_api_key_here > .env

# 5. Run Streamlit app
streamlit run app.py
