import re
from pathlib import Path

from agents.base import run_agent
from tools.workspace import make_read_tools, make_shell_tool, make_write_tool

SYSTEM = """You are a QA engineer testing the generated app inside a sandboxed environment.
Available: python, pytest, node, pip (via run_command). Files are in the workspace.
Steps:
1. list_files and read the code.
2. If `backend/requirements.txt` exists, run `pip install -r backend/requirements.txt` (plus `pytest httpx` if missing).
3. Backend: write tests under `tests/` using FastAPI's TestClient (set env DB_PATH to a temp file inside the test), run `pytest -q`.
4. Frontend: run `node --check frontend/app.js`; write a small node script under `tests/` that tests the exported pure logic; run it.
5. Do NOT modify files under backend/ or frontend/ - only report problems.
Final answer: a short report of what was tested and the results, and the LAST line exactly
`VERDICT: PASS` or `VERDICT: FAIL`. If FAIL, list precise problems (file, error) before the verdict."""


def run_tester(root: Path, design: str, needs_backend: bool) -> tuple[str, bool]:
    task = (
        f"Approved design:\n{design}\n\nBackend present: {'yes' if needs_backend else 'no'}."
        " Test the app now."
    )
    tools = make_read_tools(root) + [make_write_tool(root), make_shell_tool(root)]
    report = run_agent(SYSTEM, task, tools)
    match = re.search(r"VERDICT:\s*(PASS|FAIL)", report, re.IGNORECASE)
    return report, bool(match and match.group(1).upper() == "PASS")
