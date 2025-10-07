import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from core.types import ModelSettings
from utils.config import get_secret
import re
from ftfy import fix_text

OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
LOCAL_API_URL = get_secret("LOCAL_API_URL")
LOCAL_API_SECRET = get_secret("LOCAL_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama" 
)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

instructions = (
    "You are an analytical text assistant. "
    "Your role is to read and process input text, then produce a clear and well-structured output "
    "based on the user’s requested style (summary, critique, suggestions, risks, etc.). "
    "Do not include any conversational remarks, follow-up questions, mentions of chunk summaries or closing statements. "
    "Only return the summary and analysis itself."
)

def extract_text_from_url(url):
    try:
        response = requests.get(url, headers=headers, timeout=100)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching the URL: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    for tag in soup.find_all(["script", "style", "noscript", "footer", "nav", "aside"]):
        tag.decompose()

    text = soup.get_text(separator=' ')
    clean_text = ' '.join(text.split())

    if len(clean_text) < 100:
        print("⚠️ Page content too short. Might be a paywall or broken page.")
        return None

    return clean_text

def strip_thinking(text: str) -> str:
    # Remove <think>...</think> blocks
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def summarize_text(text: str, model_settings: ModelSettings, prompt="Summarize this:"):

    text = fix_text(text)

    if not model_settings.use_local:
        if model_settings.model_name.startswith("gpt-5"):
            response = client.responses.create(
                model=model_settings.model_name,
                instructions=instructions,
                input=f"{prompt}\n\n{text}",
                reasoning={ "effort": model_settings.reasoning },
                text={ "verbosity": model_settings.verbosity },
            )
            return response.output_text
        else:
            response = client.responses.create(
                model=model_settings.model_name,
                instructions=instructions,
                input=f"{prompt}\n\n{text}",
                temperature=model_settings.temperature
            )
            return response.output_text
    else:
        r = requests.post(
            LOCAL_API_URL,
            headers={"Authorization": f"Bearer {LOCAL_API_SECRET}"},
            json={
                "instructions": instructions,
                "text": text,
                "prompt": prompt,
                "max_tokens": 0,
                "model": model_settings.model_name,
                "temperature": model_settings.temperature
            },
            timeout=600
        )
        raw = r.json()["summary"]
        clean = strip_thinking(raw)
        return clean

def main():
    while True:
        url = input("🔗 Enter a URL to summarize: ").strip()

        print("🔎 Fetching article content...")
        article_text = extract_text_from_url(url)

        if not article_text:
            print("⚠️ Unable to extract useful content. Try a different URL.")
        else:
            print("🧠 Summarizing with GPT-4o-mini...")
            summary = summarize_text(article_text)

            if summary:
                print("\n✅ Summary:\n")
                print(summary)
            else:
                print("❌ GPT could not generate a summary.")
        
        while True:
            again = input("\n🔁 Summarize another webpage? (y/n): ").strip().lower()
            if again == 'y':
                break 
            elif again == 'n':
                print("👋 Bye! Thanks for using the summarizer.")
                return 
            else:
                print("❌ Invalid input. Please enter 'y' or 'n'.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Program interrupted. See you next time!")
