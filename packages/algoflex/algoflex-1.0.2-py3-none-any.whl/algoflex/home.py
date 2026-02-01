from textual.app import App
from textual.screen import Screen
from textual.containers import Horizontal, Vertical, VerticalScroll, HorizontalScroll
from textual.widgets import Footer, Markdown, Static
from textual.binding import Binding
from textual.reactive import reactive
from algoflex.questions import questions
from algoflex.attempt import AttemptScreen
from algoflex.custom_widgets import Title, Problem
from algoflex.dashboard import Dashboard
from algoflex.db import get_db
from algoflex.utils import time_ago, fmt_secs
from random import shuffle
from tinydb import Query

KV = Query()


class StatScreen(Vertical):
    DEFAULT_CSS = """
    Horizontal {
        Vertical {
            background: $boost;
            padding: 1;
            margin: 1 0;
        }
        #passed, #last, #best, #level {
            padding-top: 1;
        }
    }
    """

    def compose(self):
        with Horizontal():
            with Vertical():
                yield Static("[b]Passed[/]")
                yield Static("...", id="passed")
            with Vertical():
                yield Static("[b]Best time[/]")
                yield Static("...", id="best")
            with Vertical():
                yield Static("[b]Last attempt[/]")
                yield Static("...", id="last")
            with Vertical():
                yield Static("[b]Level[/]")
                yield Static("...", id="level")


class HomeScreen(App):
    BINDINGS = [
        Binding("a", "attempt", "attempt", tooltip="Attempt this question"),
        Binding("p", "previous", "previous", tooltip="Previous question"),
        Binding("n", "next", "next", tooltip="Next question"),
        Binding("d", "dashboard", "dashboard", tooltip="Show dashboard"),
    ]
    DEFAULT_CSS = """
    HomeScreen {
        Problem {
            &>*{ max-width: 100; }
            align: center middle;
            margin-top: 1;
        }
        StatScreen {
            height: 7;
            &>* {max-width: 100; }
            align: center middle;
        }
    }

    Screen {
        layers: dashboard;
    }
    """
    problem_id = reactive(0, always_update=True)
    index = reactive(0, bindings=True)
    show_dashboard: reactive[bool] = reactive(False)
    PROBLEMS_COUNT = len(questions.keys())
    PROBLEMS = [i for i in range(PROBLEMS_COUNT)]

    def compose(self):
        yield Title()
        with VerticalScroll():
            yield Dashboard().data_bind(HomeScreen.show_dashboard)
            yield Problem("")
            yield StatScreen()
        yield Footer()

    def on_mount(self):
        shuffle(self.PROBLEMS)
        self.problem_id = self.PROBLEMS[self.index]

    def watch_problem_id(self, id):
        p = questions.get(id, {})
        problem, level = p.get("markdown", ""), p.get("level", "Breezy")
        attempts = get_db()
        docs = attempts.search(KV.problem_id == id)
        total_attempts = len(docs)
        passed_attempts = [doc for doc in docs if doc.get("passed")]
        passed = len(passed_attempts)
        best_elapsed = (
            "..."
            if not passed_attempts
            else fmt_secs(min(doc.get("elapsed", "...") for doc in passed_attempts))
        )
        last_at = "..."
        if docs:
            last = sorted(docs, key=lambda x: x["created_at"], reverse=True)[0]
            last_at = ("🟢 " if last["passed"] else "🔴 ") + time_ago(
                last["created_at"]
            )
        problem_widget = self.query_one(Problem)
        problem_widget.query_one(Markdown).update(markdown=problem)
        problem_widget.scroll_home()
        self.query_one("#passed", Static).update(
            f"[$primary]{str(passed)}/{str(total_attempts)}[/]"
        )
        last, best = self.query_one("#last", Static), self.query_one("#best", Static)
        last.update(f"[$primary]{last_at}[/]")
        best.update(f"[$primary]{best_elapsed}[/]")
        self.update_level(level)

    def update_level(self, level):
        target = self.query_one("#level", Static)
        colors = {"Breezy": "green 90%", "Steady": "orange 70%", "Edgy": "red 70%"}
        target.update(f"[{colors.get(level, '$primary')}]{level}[/]")

    def watch_show_dashboard(self, show_dashboard) -> None:
        dashboard = self.query_one(Dashboard)
        dashboard.set_class(show_dashboard, "-visible")

    def action_attempt(self):
        if self.show_dashboard:
            self.show_dashboard = False

        def update(_id):
            self.problem_id = self.PROBLEMS[self.index]

        self.push_screen(AttemptScreen(self.problem_id), update)

    def action_next(self):
        if self.show_dashboard:
            self.show_dashboard = False
        if self.index + 1 < self.PROBLEMS_COUNT:
            self.index += 1
        self.problem_id = self.PROBLEMS[self.index]

    def action_previous(self):
        if self.show_dashboard:
            self.show_dashboard = False
        if self.index > 0:
            self.index -= 1
        self.problem_id = self.PROBLEMS[self.index]

    def action_dashboard(self):
        self.show_dashboard = not self.show_dashboard

    def check_action(self, action, parameters):
        if not self.screen.id == "_default":
            if (
                action == "attempt"
                or action == "next"
                or action == "previous"
                or action == "dashboard"
            ):
                return False
        if self.index == self.PROBLEMS_COUNT - 1 and action == "next":
            return
        if self.index == 0 and action == "previous":
            return
        return True
