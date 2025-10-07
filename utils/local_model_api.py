from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

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

def _summarize(instructions, text, model_name, temp, prompt="Summarize this:"):
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": f"{prompt}\n\n{text}"}
        ],
        
        temperature=temp
    )
    return response.choices[0].message.content

class SumReq(BaseModel):
    instructions: str
    text: str
    prompt: str
    max_tokens: int = 512
    model: str
    temperature: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/summarize")
def summarize(req: SumReq):

    if not req.text or len(req.text) < 20:
        raise HTTPException(400, "text too short")

    try:
        out = _summarize(req.instructions, req.text, req.model, req.temperature, req.prompt)
    except Exception as e:
        raise HTTPException(500, f"backend error: {e}")
    return {"summary": out}
