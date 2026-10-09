from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from config import AGENT_MAX_STEPS, TOOL_OUTPUT_LIMIT
from llm import get_llm


def run_agent(system: str, task: str, tools: list | None = None) -> str:
    """Run a small tool-calling loop and return the agent's final text answer."""
    tools = tools or []
    llm = get_llm()
    if tools:
        llm = llm.bind_tools(tools)
    by_name = {t.name: t for t in tools}

    messages = [SystemMessage(system), HumanMessage(task)]
    ai = None
    for _ in range(AGENT_MAX_STEPS):
        ai = llm.invoke(messages)
        messages.append(ai)
        if not ai.tool_calls:
            return ai.content
        for call in ai.tool_calls:
            try:
                out = by_name[call["name"]].invoke(call["args"])
            except Exception as e:
                out = f"Error: {e}"
            messages.append(
                ToolMessage(content=str(out)[:TOOL_OUTPUT_LIMIT], tool_call_id=call["id"])
            )
    return (ai.content if ai else "") + "\n\n(Stopped: step limit reached.)"
