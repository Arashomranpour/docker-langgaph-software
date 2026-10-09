from pathlib import Path

from agents.base import run_agent
from tools.workspace import make_read_tools

SYSTEM = """You are a technical writer. Write the final project report in Markdown with these sections:
1. Overview (what was built)
2. Design summary (use cases)
3. What each agent did (Analyst, Backend developer, Frontend developer, Tester)
4. Project structure (use list_files)
5. How to run locally (backend: uvicorn command; frontend: open index.html or any static server)
6. Test results (from the tester report; be honest about failures)
7. Deploying to Netlify: suggestions only, no commands are executed. Frontend (static `frontend/` folder) can be
   deployed with a `netlify.toml` (publish = "frontend") via Git integration or `netlify deploy --prod`.
   The FastAPI backend cannot run on Netlify as-is: suggest hosting it on a Python host (Render, Fly.io, Railway)
   or rewriting endpoints as Netlify Functions; mention setting API_BASE and CORS. Skip backend advice if no backend.
Be concise and accurate; read files if you need details."""


def run_docs(
    root: Path,
    request: str,
    design: str,
    needs_backend: bool,
    backend_summary: str,
    frontend_summary: str,
    test_report: str,
    test_passed: bool,
) -> str:
    task = f"""Original request: {request}

Design:
{design}

Backend present: {needs_backend}
Backend summary: {backend_summary or 'n/a'}
Frontend summary: {frontend_summary}
Tester report (passed={test_passed}):
{test_report}"""
    return run_agent(SYSTEM, task, make_read_tools(root))
