from textual import on
from textual.app import App
from textual.widgets import TextArea, Footer, TabbedContent, Button, Markdown, Static
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.binding import Binding
from algoflex.custom_widgets import Title, Problem
from algoflex.result import ResultModal
from algoflex.questions import questions
from algoflex.db import get_db
from algoflex.utils import time_ago, fmt_secs
from tinydb import Query
from time import monotonic

KV = Query()
attempts = get_db()


class AttemptScreen(Screen):
    BINDINGS = [
        Binding("a", "back", "back", tooltip="Go to home"),
        Binding("s", "submit", "submit", tooltip="Submit your solution"),
        Binding("m", "maximize", "max/min editor", tooltip="maximize/minimize editor"),
    ]
    DEFAULT_CSS = """
    Horizontal {
        Problem {
            margin: 0 1;
            height: 1fr;
            width: 1fr;
        }
        TabbedContent {
            width: 1fr;
        }
    }

    TextArea {
        margin-right: 1;
    }

    Vertical {
        Horizontal {
            height: 4;
            align: center middle;
            background: $boost;
            border-top: hkey $background;
            margin-right: 1;
        }
    }

    #timeline {
        padding: 1 2;
        border-left: vkey $boost;
    }

    Markdown {
        border-left: vkey $boost;
        height: 1fr;
        overflow-y: auto;
    }
    """

    def __init__(self, problem_id):
        super().__init__()
        self.problem_id = problem_id
        self.test_time = monotonic()
        self.best = None

    def compose(self):
        question = questions.get(self.problem_id, {})
        description = question.get("markdown", "")
        code = question.get("code", "")

        yield Title()
        with Horizontal():
            yield Problem(description)
            with TabbedContent("Attempt", "Timeline", "Past solutions", id="editor"):
                with Vertical():
                    yield TextArea(
                        code,
                        id="code",
                        show_line_numbers=True,
                        language="python",
                        compact=True,
                        tab_behavior="indent",
                    )
                    with Horizontal():
                        yield Button(id="submit", label="Submit", flat=True)
                yield ScrollableContainer(Static(id="timeline"))
                yield Markdown(id="solutions")
        yield Footer()

    def on_mount(self):
        self.update()

    def update(self):
        docs = attempts.search(KV.problem_id == self.problem_id)
        self.update_timeline(docs)
        self.update_solutions(docs)

    @on(Button.Pressed, "#submit")
    def submit_code(self):
        self.attempt()

    def attempt(self):
        def update(_id):
            self.update()

        code = self.query_one("#code", TextArea)
        elapsed = monotonic() - self.test_time
        self.app.push_screen(
            ResultModal(self.problem_id, code.text, elapsed, self.best), update
        )

    def update_timeline(self, docs):
        md = ""
        timeline = sorted(docs, key=lambda x: x["created_at"], reverse=True)
        elapsed = [doc["elapsed"] for doc in docs if doc["passed"]]
        self.best = min(elapsed) if elapsed else None
        for doc in timeline:
            md += f"\n|- {('🟢' if doc['passed'] else '🔴')} {time_ago(doc['created_at'])}   ({fmt_secs(doc['elapsed'])})"
            if doc["passed"] and doc["elapsed"] == self.best:
                md += "\t<--- best"
            md += "\n|"
        self.query_one("#timeline", Static).update(md.rstrip("|"))

    def update_solutions(self, docs):
        passed = sorted(
            (doc for doc in docs if doc["passed"]),
            key=lambda x: x["created_at"],
            reverse=True,
        )
        md = ""
        for doc in passed:
            md += f"### {time_ago(doc['created_at'])}\n```python\n{doc['code']}\n```\n"
        self.query_one("#solutions", Markdown).update(md)

    def action_back(self):
        self.dismiss()

    def action_submit(self):
        self.attempt()

    def action_maximize(self) -> None:
        editor = self.query_one("#editor", TabbedContent)
        if not editor.is_maximized:
            self.maximize(editor)
        else:
            self.minimize()
