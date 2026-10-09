"""File and shell tools scoped to a single project workspace directory."""
import os
import shlex
import subprocess
from pathlib import Path

from langchain_core.tools import tool

from config import TOOL_OUTPUT_LIMIT

ALLOWED_COMMANDS = {"python", "python3", "pytest", "node", "pip"}
SECRET_ENV = {"GROQ_API_KEY", "SERPER_API_KEY"}
COMMAND_TIMEOUT = 90


def _safe_path(root: Path, rel: str) -> Path:
    path = (root / rel).resolve()
    if path != root.resolve() and root.resolve() not in path.parents:
        raise ValueError("Path escapes the workspace")
    return path


def make_read_tools(root: Path) -> list:
    root.mkdir(parents=True, exist_ok=True)

    @tool
    def list_files() -> str:
        """List all files in the project workspace (relative paths)."""
        files = sorted(
            str(p.relative_to(root)).replace("\\", "/")
            for p in root.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts
        )
        return "\n".join(files) or "(workspace is empty)"

    @tool
    def read_file(path: str) -> str:
        """Read a text file from the project workspace."""
        try:
            return _safe_path(root, path).read_text(encoding="utf-8")[:TOOL_OUTPUT_LIMIT * 3]
        except Exception as e:
            return f"Error: {e}"

    return [list_files, read_file]


def make_write_tool(root: Path):
    @tool
    def write_file(path: str, content: str) -> str:
        """Create or overwrite a file in the project workspace. Parent folders are created."""
        try:
            target = _safe_path(root, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"Wrote {path} ({len(content)} chars)"
        except Exception as e:
            return f"Error: {e}"

    return write_file


def make_shell_tool(root: Path):
    @tool
    def run_command(command: str) -> str:
        """Run a command inside the project workspace.

        Allowed programs: python, pytest, node, pip. Example: 'pytest -q' or 'node tests/ui.test.js'.
        Runs with a timeout; do not start long-running servers (use FastAPI TestClient in tests).
        """
        try:
            args = shlex.split(command)
        except ValueError as e:
            return f"Error: {e}"
        if not args or args[0] not in ALLOWED_COMMANDS:
            return f"Error: only {sorted(ALLOWED_COMMANDS)} are allowed."
        env = {k: v for k, v in os.environ.items() if k not in SECRET_ENV}
        try:
            proc = subprocess.run(
                args, cwd=root, env=env, capture_output=True, text=True, timeout=COMMAND_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            return f"Error: command timed out after {COMMAND_TIMEOUT}s"
        except Exception as e:
            return f"Error: {e}"
        out = f"exit code: {proc.returncode}\n{proc.stdout}\n{proc.stderr}"
        return out[-TOOL_OUTPUT_LIMIT:]

    return run_command
