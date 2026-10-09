LABELS = {
    "analyst": "Analyst",
    "review": "Human review",
    "backend": "Backend dev",
    "frontend": "Frontend dev",
    "tester": "Tester",
    "docs": "Doc generator",
}

DONE, WORKING, WAITING, PENDING = "#c8e6c9", "#ffcc80", "#90caf9", "#eceff1"


def workflow_dot(done: set, working: str | None, waiting_review: bool, needs_backend) -> str:
    def style(node: str) -> str:
        if node == working:
            return f'fillcolor="{WORKING}", penwidth=3, color="#ef6c00"'
        if node == "review" and waiting_review:
            return f'fillcolor="{WAITING}", penwidth=3, color="#1565c0"'
        if node in done:
            return f'fillcolor="{DONE}"'
        if node == "backend" and needs_backend is False:
            return f'fillcolor="white", style="dashed,filled", fontcolor="#9e9e9e", color="#9e9e9e"'
        return f'fillcolor="{PENDING}"'

    lines = [
        "digraph G {",
        "rankdir=TB; bgcolor=transparent;",
        'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, color="#78909c"];',
        'edge [color="#78909c", fontname="Helvetica", fontsize=9];',
        'start [label="Start", shape=circle, fillcolor="white"];',
        'end [label="End", shape=doublecircle, fillcolor="white"];',
    ]
    for node, label in LABELS.items():
        lines.append(f'{node} [label="{label}", {style(node)}];')
    lines += [
        "start -> analyst;",
        "analyst -> review;",
        'review -> analyst [label="changes", style=dashed];',
        'review -> backend [label="approve"];',
        "backend -> frontend;",
        "frontend -> tester;",
        'tester -> backend [label="fail", style=dashed];',
        'tester -> frontend [label="fail", style=dashed];',
        'tester -> docs [label="pass"];',
        "docs -> end;",
        "}",
    ]
    return "\n".join(lines)
