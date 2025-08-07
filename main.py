from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sympy import symbols, Eq, solve, sympify
import re, os, openai

app = FastAPI()

# ────────────────────────────── CORS ──────────────────────────────
# While you’re testing, let any domain call your API.
# Later you can restrict allow_origins to your own website/app.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# ───────────────────────────────────────────────────────────────────

# ─── helpers ───────────────────────────────────────────────────────
def is_equation(q: str) -> bool:
    return "=" in q

def sympy_solve(q: str):
    # normalise symbols coming from phone keyboards
    q = q.replace("÷", "/")
    q = q.replace("−", "-").replace("–", "-").replace("—", "-")    # long minus → "-"
    if is_equation(q):
        var = re.findall(r"[a-zA-Z]", q)[0]           # first letter = variable
        lhs, rhs = q.split("=", 1)
        expr = sympify(lhs) - sympify(rhs)
        sol  = solve(expr, symbols(var))
        return f"{var} = {sol}"
    # plain expression (no =) → numeric evaluation
    return str(sympify(q).evalf())

def gpt_fallback(q: str):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return "GPT fallback disabled (no key)."
    openai.api_key = key
    chat = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role":"system","content":"You are a WAEC maths tutor."},
            {"role":"user","content":f"Solve step-by-step: {q}"}
        ]
    )
    return chat.choices[0].message.content.strip()

# ─── API route ─────────────────────────────────────────────────────
class Q(BaseModel):
    question: str

@app.post("/solve")
async def solve_q(data: Q):
    try:
        ans = sympy_solve(data.question)
        return {"source": "sympy", "answer": ans}
    except Exception:
        ans = gpt_fallback(data.question)
        return {"source": "gpt4o", "answer": ans}
