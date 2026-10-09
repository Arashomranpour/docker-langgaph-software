from pathlib import Path

from agents.base import run_agent
from tools.workspace import make_read_tools, make_write_tool

SYSTEM = """You are a frontend developer. Implement the UI for the approved design in plain JavaScript (no build step, no frameworks).
Rules:
- Put everything under `frontend/`: `index.html`, `app.js`, `style.css`.
- Keep logic that does not touch the DOM in functions that are exported with
  `if (typeof module !== 'undefined') module.exports = {...}` so it can be tested with node.
- If a backend exists, call it with fetch using `const API_BASE = window.API_BASE || 'http://localhost:8000'`
  and follow the endpoint list you are given exactly (you may read backend files).
  If there is no backend, persist data in localStorage.
- Make the UI clean and usable on mobile.
- Use the write_file tool for every file. Do not paste code in your answer.
Final answer: a short summary of the files and features."""


def run_frontend(
    root: Path, design: str, backend_summary: str = "", test_report: str = ""
) -> str:
    task = f"Approved design:\n{design}"
    task += f"\n\nBackend summary:\n{backend_summary}" if backend_summary else "\n\nThere is no backend."
    if test_report:
        task += f"\n\nThe tester found problems. Fix the frontend files accordingly:\n{test_report}"
    return run_agent(SYSTEM, task, make_read_tools(root) + [make_write_tool(root)])
