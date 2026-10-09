from datetime import date

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from llm import get_llm
from tools.search import web_search
from tools.utility import calculator, get_current_time

TOOLS = [web_search, calculator, get_current_time]

SYSTEM = """You are a helpful, concise assistant. Today's date is {today}.
If you are not sure about something, or it may have changed recently (news, prices, versions, people, events),
use the web_search tool before answering instead of guessing, and mention the source briefly.
Use calculator for arithmetic. Answer directly when you already know the answer."""


def build_chat_graph():
    llm = get_llm().bind_tools(TOOLS)

    def agent(state: MessagesState):
        system = SystemMessage(SYSTEM.format(today=date.today().isoformat()))
        return {"messages": [llm.invoke([system] + state["messages"])]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=MemorySaver())
