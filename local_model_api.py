from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama" 
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

def _summarize(text, model_name, temp, prompt="Summarize this:"):
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are an assistant that analyzes text and provides a summary, ignoring text that might be navigation related."},
            {"role": "user", "content": f"{prompt}\n\n{text}"}
        ],
        
        temperature=temp
    )
    return response.choices[0].message.content

class SumReq(BaseModel):
    text: str
    prompt: str
    max_tokens: int = 512
    model: str = "qwen3:32b"  # example; change to what you run
    temperature: float = 0.2

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/summarize")
def summarize(req: SumReq):
    # simple bearer check
    # if API_TOKEN and authorization != f"Bearer {API_TOKEN}":
    #     raise HTTPException(status_code=401, detail="Unauthorized")

    if not req.text or len(req.text) < 20:
        raise HTTPException(400, "text too short")

    try:
        out = _summarize(req.text, req.model, req.temperature, req.prompt)
    except Exception as e:
        raise HTTPException(500, f"backend error: {e}")
    return {"summary": out}
