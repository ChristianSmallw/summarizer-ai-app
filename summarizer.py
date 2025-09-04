import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

def extract_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
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

def summarize_text(text, prompt="Summarize this article:"):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            #{"role": "system", "content": "You are a helpful but very sassy and aloof cat that summarizes articles in a feline way. Use cat puns, end some lines with 'meow~', and throw in a random nap reference if possible."},
            {"role": "system", "content": "You are an assistant that analyzes the contents of a website and provides a short summary, ignoring text that might be navigation related."},
            {"role": "user", "content": f"{prompt}\n\n{text}"}
        ],
        
        temperature=0.8,
        max_tokens=500
    )
    return response.choices[0].message.content

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
            again = input("\n🔁 Summarize another article? (y/n): ").strip().lower()
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
