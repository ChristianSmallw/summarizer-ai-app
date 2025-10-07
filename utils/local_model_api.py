from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from utils.config import get_secret

LOCAL_API_SECRET = get_secret("LOCAL_API_KEY")

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

def _verify_token(authorization: str = Header(...)):
    """
    Expected header:
    Authorization: Bearer <LOCAL_API_SECRET>
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    if token != LOCAL_API_SECRET:
        raise HTTPException(status_code=403, detail="Invalid or missing token")

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
def summarize(req: SumReq, auth: None = Depends(_verify_token)):

    if not req.text or len(req.text) < 20:
        raise HTTPException(400, "text too short")

    try:
        out = _summarize(req.instructions, req.text, req.model, req.temperature, req.prompt)
    except Exception as e:
        raise HTTPException(500, f"backend error: {e}")
    
    return {"summary": out}
