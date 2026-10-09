import io
import uuid
import zipfile

import streamlit as st
from langgraph.types import Command

from config import MAX_FIX_ATTEMPTS, WORKSPACE_DIR
from ui.graph_view import workflow_dot

LABELS = {
    "analyst": "Analyst",
    "review": "Your review",
    "backend": "Backend developer",
    "frontend": "Frontend developer",
    "tester": "Tester",
    "docs": "Doc generator",
}
AGENT_TO_NODE = {
    "Analyst": "analyst",
    "Backend developer": "backend",
    "Frontend developer": "frontend",
    "Tester": "tester",
    "Doc generator": "docs",
}
FOLLOWS = {"backend": "frontend", "frontend": "tester"}  # tester/analyst are decided dynamically
OPEN_BY_DEFAULT = {"Analyst", "Tester", "Doc generator"}


def _tracker_md(done: set, working: str | None, needs_backend, waiting_review: bool) -> str:
    lines = []
    for node, label in LABELS.items():
        if node == "backend" and needs_backend is False:
            continue
        if node == working:
            lines.append(f"🔄 **{label}** is working...")
        elif node == "review" and waiting_review:
            lines.append(f"🙋 **{label}** — waiting for you")
        elif node in done:
            lines.append(f"✅ {label} is done")
        else:
            lines.append(f"⏳ <span style='opacity:.55'>{label}</span>")
    return "\n\n".join(lines)


def _show_tracker(slots, *args):
    """slots = (main-page placeholder, sidebar graph placeholder); args = done, working, needs_backend, waiting."""
    page_slot, graph_slot = slots
    done, working, needs_backend, waiting_review = args
    page_slot.markdown(_tracker_md(*args), unsafe_allow_html=True)
    graph_slot.graphviz_chart(
        workflow_dot(done, working, waiting_review, needs_backend), use_container_width=True
    )


def _done_nodes(values: dict) -> set:
    done = {AGENT_TO_NODE[e["agent"]] for e in values.get("log", []) if e["agent"] in AGENT_TO_NODE}
    if done & {"backend", "frontend", "tester", "docs"}:
        done.add("review")
    return done


def _show_entry(entry: dict):
    with st.expander(f"{entry['agent']}", expanded=entry["agent"] in OPEN_BY_DEFAULT):
        st.markdown(entry["text"])


def _next_node(node: str, update: dict, needs_backend: bool):
    if node == "analyst":
        return "review"
    if node == "tester":
        if update.get("test_passed") or update.get("attempts", 0) > MAX_FIX_ATTEMPTS:
            return "docs"
        return "backend" if needs_backend else "frontend"
    return FOLLOWS.get(node)


def _advance(graph, payload, config, tracker, live) -> bool:
    """Stream the graph, updating the tracker and showing each agent's output as it finishes."""
    values = graph.get_state(config).values
    needs_backend = values.get("needs_backend")
    done = _done_nodes(values)

    working = "analyst"
    if isinstance(payload, Command) and payload.resume.get("approved"):
        working = "backend" if needs_backend else "frontend"
        done.add("review")

    with live:
        status = st.status(f"{LABELS[working]} is working...", expanded=False)
    _show_tracker(tracker, done - {working}, working, needs_backend, False)

    try:
        for chunk in graph.stream(payload, config, stream_mode="updates"):
            for node, update in chunk.items():
                if node not in LABELS or node == "review" or not update:
                    continue
                if node == "analyst":
                    needs_backend = update["needs_backend"]
                done.add(node)
                with live:
                    for entry in update.get("log", []):
                        _show_entry(entry)
                nxt = _next_node(node, update, needs_backend)
                working = nxt if nxt != "review" else None
                if nxt == "review":
                    status.update(label="Design ready - waiting for your review", state="complete")
                elif nxt:
                    status.update(label=f"{LABELS[nxt]} is working...")
                _show_tracker(tracker, done - {working}, working, needs_backend, nxt == "review")
        status.update(label="Paused for your review" if working is None else "Finished", state="complete")
        return True
    except Exception as e:
        status.update(label=f"{LABELS.get(working, 'Agent')} failed", state="error")
        st.error(f"{type(e).__name__}: {e}")
        return False


def _zip_workspace(thread_id: str) -> bytes:
    root = WORKSPACE_DIR / thread_id
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in root.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts:
                zf.write(p, p.relative_to(root))
    return buf.getvalue()


def render_developer(graph):
    if st.sidebar.button("New project"):
        st.session_state.pop("dev_thread", None)
        st.session_state.pop("dev_pending", None)
        st.rerun()

    st.sidebar.markdown("**Workflow**")
    graph_slot = st.sidebar.empty()

    if "dev_thread" not in st.session_state:
        graph_slot.graphviz_chart(workflow_dot(set(), None, False, None), use_container_width=True)
        request = st.text_area("Describe the app you want built", height=120)
        if st.button("Start", type="primary", disabled=not request.strip()):
            thread_id = str(uuid.uuid4())[:8]
            st.session_state.dev_thread = thread_id
            st.session_state.dev_pending = {"thread_id": thread_id, "request": request.strip()}
            st.rerun()
        return

    thread_id = st.session_state.dev_thread
    config = {"configurable": {"thread_id": thread_id}}
    pending = st.session_state.pop("dev_pending", None)
    state = graph.get_state(config)
    values = state.values
    review = next((i for t in state.tasks for i in t.interrupts), None)

    tracker = (st.empty(), graph_slot)
    _show_tracker(tracker, _done_nodes(values), None, values.get("needs_backend"), review is not None)

    for entry in values.get("log", []):
        _show_entry(entry)

    if pending is not None:
        live = st.container()
        ok = _advance(graph, pending, config, tracker, live)
        if ok:
            st.rerun()
        return

    if review:
        st.subheader("Review the design")
        st.info("Approve to start development, or tell the analyst what to change.")
        feedback = st.text_area("Feedback for the analyst", key=f"fb_{len(values.get('log', []))}")
        col1, col2 = st.columns(2)
        if col1.button("Approve", type="primary"):
            st.session_state.dev_pending = Command(resume={"approved": True})
            st.rerun()
        if col2.button("Request changes", disabled=not feedback.strip()):
            st.session_state.dev_pending = Command(
                resume={"approved": False, "feedback": feedback.strip()}
            )
            st.rerun()
    elif values.get("report"):
        if values.get("test_passed"):
            st.success("All done - tests passed.")
        else:
            st.warning("Finished, but the tester reported failures. See the report above.")
        st.download_button(
            "Download project (zip)",
            _zip_workspace(thread_id),
            file_name=f"project_{thread_id}.zip",
            mime="application/zip",
        )
