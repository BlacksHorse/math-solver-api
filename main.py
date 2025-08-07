from fastapi import FastAPI
from pydantic import BaseModel
from sympy import symbols, Eq, solve, sympify
import re, os, openai

app = FastAPI()

# ---- helpers -------------------------------------------------
def is_equation(q: str) -> bool:
    return "=" in q

def sympy_solve(q: str):
    q = q.replace("÷", "/")
    if is_equation(q):
        var = re.findall(r"[a-zA-Z]", q)[0]
        lhs, rhs = q.split("=", 1)
        expr = sympify(lhs) - sympify(rhs)
        sol  = solve(expr, symbols(var))
        return f"{var} = {sol}"
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
        ])
    return chat.choices[0].message.content.strip()

# ---- API route -----------------------------------------------
class Q(BaseModel):
    question: str

@app.post("/solve")
async def solve_q(data: Q):
    try:
        ans = sympy_solve(data.question)
        return {"source":"sympy", "answer": ans}
    except Exception:
        ans = gpt_fallback(data.question)
        return {"source":"gpt4o", "answer": ans}
