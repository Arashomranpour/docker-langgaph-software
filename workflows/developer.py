import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from agents.analyst import run_analyst
from agents.backend import run_backend
from agents.docs import run_docs
from agents.frontend import run_frontend
from agents.tester import run_tester
from config import MAX_FIX_ATTEMPTS, WORKSPACE_DIR


class DevState(TypedDict, total=False):
    thread_id: str
    request: str
    design: str
    needs_backend: bool
    feedback: str
    backend_summary: str
    frontend_summary: str
    test_report: str
    test_passed: bool
    attempts: int
    report: str
    log: Annotated[list, operator.add]  # [{"agent": str, "text": str}]


def _root(state: DevState):
    return WORKSPACE_DIR / state["thread_id"]


def analyst(state: DevState):
    design, needs_backend = run_analyst(
        state["request"], state.get("design", ""), state.get("feedback", "")
    )
    return {
        "design": design,
        "needs_backend": needs_backend,
        "log": [{"agent": "Analyst", "text": design}],
    }


def human_review(state: DevState) -> Command:
    decision = interrupt({"design": state["design"], "needs_backend": state["needs_backend"]})
    if decision.get("approved"):
        goto = "backend" if state["needs_backend"] else "frontend"
        return Command(goto=goto, update={"feedback": ""})
    feedback = decision.get("feedback") or "Please improve the design."
    return Command(
        goto="analyst",
        update={"feedback": feedback, "log": [{"agent": "You", "text": f"Requested changes: {feedback}"}]},
    )


def backend(state: DevState):
    summary = run_backend(_root(state), state["design"], state.get("test_report", ""))
    return {"backend_summary": summary, "log": [{"agent": "Backend developer", "text": summary}]}


def frontend(state: DevState):
    summary = run_frontend(
        _root(state), state["design"], state.get("backend_summary", ""), state.get("test_report", "")
    )
    return {"frontend_summary": summary, "log": [{"agent": "Frontend developer", "text": summary}]}


def tester(state: DevState):
    report, passed = run_tester(_root(state), state["design"], state["needs_backend"])
    return {
        "test_report": report,
        "test_passed": passed,
        "attempts": state.get("attempts", 0) + 1,
        "log": [{"agent": "Tester", "text": report}],
    }


def after_test(state: DevState) -> str:
    if state["test_passed"] or state["attempts"] > MAX_FIX_ATTEMPTS:
        return "docs"
    return "backend" if state["needs_backend"] else "frontend"


def docs(state: DevState):
    report = run_docs(
        _root(state),
        state["request"],
        state["design"],
        state["needs_backend"],
        state.get("backend_summary", ""),
        state.get("frontend_summary", ""),
        state["test_report"],
        state["test_passed"],
    )
    (_root(state) / "REPORT.md").write_text(report, encoding="utf-8")
    return {"report": report, "log": [{"agent": "Doc generator", "text": report}]}


def build_developer_graph():
    builder = StateGraph(DevState)
    builder.add_node("analyst", analyst)
    builder.add_node("human_review", human_review)
    builder.add_node("backend", backend)
    builder.add_node("frontend", frontend)
    builder.add_node("tester", tester)
    builder.add_node("docs", docs)

    builder.add_edge(START, "analyst")
    builder.add_edge("analyst", "human_review")
    # human_review routes itself with Command(goto=...)
    builder.add_edge("backend", "frontend")
    builder.add_edge("frontend", "tester")
    builder.add_conditional_edges("tester", after_test, ["backend", "frontend", "docs"])
    builder.add_edge("docs", END)
    return builder.compile(checkpointer=MemorySaver())
