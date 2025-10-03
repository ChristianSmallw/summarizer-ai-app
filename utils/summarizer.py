import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from utils.config import get_secret
import re
import time
from ftfy import fix_text

OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
# OLLAMA_API = "http://localhost:11434/api/chat"
client = OpenAI(api_key=OPENAI_API_KEY)
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama" 
)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

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


def summarize_text(text, model_name, is_local, prompt="Summarize this:"):
    temp = 1 if model_name.startswith("gpt-5") else 0.2
    text = fix_text(text)

    if not is_local:
        response = client.responses.create(
            model=model_name,
            #model="qwen3:32b",
            instructions="You are an assistant that analyzes text and provides a summary, ignoring text that might be navigation related.",
            input=f"{prompt}\n\n{text}",
            temperature=temp
        )
        return response.output_text
    else:
        r = requests.post(
            "https://reese-shingly-johnetta.ngrok-free.dev/summarize",
            json={
                "text": text,
                "prompt": prompt,
                "max_tokens": 0,
                "model": model_name,
                "temperature": 0.2
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
