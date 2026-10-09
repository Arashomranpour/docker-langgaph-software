# LangGraph Assistant

A Streamlit app built on [LangGraph](https://langchain-ai.github.io/langgraph/) and [Groq](https://groq.com/) with two modes:

- **Chat mode** - a tool-using chat agent. It answers directly, and uses Google search (via [Serper](https://serper.dev/)) when it doesn't know something or the answer may be recent. It also has a calculator and a clock.
- **Developer mode** - a multi-agent team that builds a small web app from your description:

  1. **Analyst** writes the use cases and decides whether a backend is needed.
  2. **Human review** - you approve the design or send feedback; the analyst revises until you approve.
  3. **Backend developer** (only if needed) - FastAPI + SQLite.
  4. **Frontend developer** - plain JavaScript, HTML, CSS.
  5. **Tester** - runs pytest / node in a sandboxed container. On failure the developers get up to 2 fix rounds.
  6. **Doc generator** - writes a report of what each agent did plus Netlify deployment suggestions (text only; nothing is deployed).

The sidebar shows a live workflow graph so you can see which agent is active.

## Run with Docker

```bash
cp .env.example .env        # then fill in your keys (no quotes around values)
docker build -t langgraph-chat .
docker run -p 8501:8501 --env-file .env -v "$(pwd)/workspace:/app/workspace" langgraph-chat
```

Open http://localhost:8501. Generated projects are written to `workspace/<project-id>/` (and can be downloaded as a zip from the UI).

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | yes | Groq API key |
| `SERPER_API_KEY` | for web search | Serper API key |
| `GROQ_MODEL` | no | Defaults to `openai/gpt-oss-120b` |
| `MAX_FIX_ATTEMPTS` | no | Tester -> developer fix rounds (default 2) |

## Project layout

```
app.py                 Streamlit entry point, mode switch
config.py, llm.py      Settings and the Groq model factory
workflows/             LangGraph graphs: chat.py, developer.py
agents/                analyst, backend, frontend, tester, docs (+ base tool loop)
tools/                 web search, utilities, sandboxed workspace file/shell tools
ui/                    Streamlit views: chat, developer, workflow graph
```

To add an agent, create a file in `agents/` and add a node to `workflows/developer.py`.

## Notes

- The tester can only run `python`, `pytest`, `node` and `pip` inside the container, with API keys removed from the command's environment. Treat the container as the sandbox.
- Groq's free tier has rate limits; long Developer-mode runs may hit them.
