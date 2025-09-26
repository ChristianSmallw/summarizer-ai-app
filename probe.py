def main():
    from openai import OpenAI
    from utils.config import get_secret
    OPENAI_API_KEY = get_secret("OPENAI_API_KEY")

    client = OpenAI(api_key=OPENAI_API_KEY)

    def probe(model: str):
        try:
            r = client.responses.create(
                model=model,
                #model="qwen3:32b",
                instructions="you are a cat, please meow all the time.",
                input=f"hi wassup!"
            )
            return True, r.output_text
        except Exception as e:
            return False, str(e)

    for m in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]:
        ok, msg = probe(m)
        print(m, "OK" if ok else "NO", "->", msg[:200])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Program interrupted. See you next time!")