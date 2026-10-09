from pathlib import Path

from agents.base import run_agent
from tools.workspace import make_read_tools, make_write_tool

SYSTEM = """You are a backend developer. Implement the backend and database for the approved design.
Stack (fixed): Python FastAPI + SQLite via the standard `sqlite3` module.
Rules:
- Put everything under `backend/`: `backend/main.py` exposes `app = FastAPI()`, with CORS enabled for all origins.
- Create the DB schema on startup. Database file path comes from env `DB_PATH` (default `app.db`).
- Create `backend/requirements.txt`.
- Keep it small, no authentication unless the design requires it.
- Use the write_file tool for every file. Do not paste code in your answer.
Final answer: a short summary with the list of HTTP endpoints (method, path, request/response JSON)
so the frontend developer can use them."""


def run_backend(root: Path, design: str, test_report: str = "") -> str:
    task = f"Approved design:\n{design}"
    if test_report:
        task += f"\n\nThe tester found problems. Fix the backend files accordingly:\n{test_report}"
    return run_agent(SYSTEM, task, make_read_tools(root) + [make_write_tool(root)])
