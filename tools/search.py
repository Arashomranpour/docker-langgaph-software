import os

import requests
from langchain_core.tools import tool

SERPER_URL = "https://google.serper.dev/search"


@tool
def web_search(query: str) -> str:
    """Search the web (Google via Serper) for current or unknown information.

    Use this when the answer may be recent, niche, or something you are not sure about.
    """
    key = os.getenv("SERPER_API_KEY")
    if not key:
        return "Error: SERPER_API_KEY is not set."
    try:
        resp = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": 5},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Search failed: {e}"

    lines = []
    box = data.get("answerBox")
    if box:
        lines.append("Answer box: " + (box.get("answer") or box.get("snippet") or box.get("title") or ""))
    for item in data.get("organic", [])[:5]:
        lines.append(f"- {item.get('title')}\n  {item.get('snippet', '')}\n  {item.get('link')}")
    return "\n".join(lines) or "No results found."
