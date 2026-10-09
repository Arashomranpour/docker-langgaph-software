import os
from pathlib import Path

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", Path(__file__).parent / "workspace"))
MAX_FIX_ATTEMPTS = int(os.getenv("MAX_FIX_ATTEMPTS", "2"))
AGENT_MAX_STEPS = int(os.getenv("AGENT_MAX_STEPS", "15"))
TOOL_OUTPUT_LIMIT = 4000
