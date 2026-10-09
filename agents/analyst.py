import re

from agents.base import run_agent

SYSTEM = """You are a business/systems analyst. Turn the user's app idea into a concise design:
1. Goal (1-2 sentences)
2. Actors
3. Use cases (numbered, each with a short flow)
4. Data entities (only if persistence is needed)
5. Scope notes / assumptions
Keep it small and buildable as a simple web app. Do not write code.
The final line of your answer MUST be exactly `NEEDS_BACKEND: yes` or `NEEDS_BACKEND: no`
(yes only if the app needs a server or a database; no if a browser-only app is enough)."""


def run_analyst(request: str, previous_design: str = "", feedback: str = "") -> tuple[str, bool]:
    task = f"App idea:\n{request}"
    if feedback:
        task += f"\n\nPrevious design:\n{previous_design}\n\nUser feedback to address:\n{feedback}"
    text = run_agent(SYSTEM, task)
    match = re.search(r"NEEDS_BACKEND:\s*(yes|no)", text, re.IGNORECASE)
    needs_backend = bool(match and match.group(1).lower() == "yes")
    design = re.sub(r"\n?\s*NEEDS_BACKEND:.*", "", text, flags=re.IGNORECASE).strip()
    return design, needs_backend
