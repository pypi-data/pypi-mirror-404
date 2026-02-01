from textual.app import ComposeResult
from textual.containers import Horizontal, Center
from textual.reactive import reactive
from textual.widgets import (
    ProgressBar,
    Digits,
    Static,
    Label,
    Collapsible,
    Markdown,
)
from textual.widget import Widget
from algoflex.questions import questions as q
from algoflex.db import get_db
from algoflex.utils import time_ago, fmt_secs
from tinydb import Query
from heapq import nlargest, nsmallest

KV = Query()
attempts = get_db()


class Dashboard(Widget):
    show_dashboard = reactive(False)
    # get completed questions per level
    docs, breezy, steady, edgy = attempts.all(), set(), set(), set()
    for k, v in q.items():
        if v["level"] == "Breezy":
            breezy.add(k)
        elif v["level"] == "Steady":
            steady.add(k)
        else:
            edgy.add(k)
    total = len(breezy) + (len(steady) * 2) + (len(edgy) * 4)

    DEFAULT_CSS = """
    Dashboard {
        overflow-y: auto;
        width: 52vw;
        border-left: vkey $boost;
        border-right: vkey $boost;
        padding: 1 2;
        layer: dashboard; 
        align-horizontal: center;
        dock: top;
        offset-x: 100vw;
        transition: offset 100ms;  
        &.-visible {
            offset-x: 48vw;
        }

        Bar {
            & > .bar--bar {
                color: $markdown-h1-color;
            }
        }

        #breezy {
            color: green 90%;
        }

        #steady {
            color: orange 70%;
        }

        #edgy {
            color: red 70%;
        }


        #title {
            height: 4;
            color: $markdown-h1-color;
            content-align: center middle;
        }

        #counts {
            height: 7;
        }

        Digits {
            text-align: center;
        }

        #progress {
            height: 3;
        }
    }
    """

    def compose(self) -> ComposeResult:
        with Center(id="dashboard"):
            yield Static("Dashboard", id="title")
            with Horizontal(id="counts"):
                with Center(id="breezy"):
                    yield Center(Label("Breezy"))
                    yield Digits("0", id="d_breezy")
                    yield Center(Label(f"of {len(self.breezy)}"))
                with Center(id="steady"):
                    yield Center(Label("Steady"))
                    yield Digits("0", id="d_steady")
                    yield Center(Label(f"of {len(self.steady)}"))
                with Center(id="edgy"):
                    yield Center(Label("Edgy"))
                    yield Digits("0", id="d_edgy")
                    yield Center(Label(f"of {len(self.edgy)}"))
            with Center(id="progress"):
                yield ProgressBar(total=self.total, show_eta=False, id="all")
            with Collapsible(title="Recent attempts", collapsed=False):
                yield Markdown(id="recent")
            with Collapsible(title="Speedy Solves"):
                yield Markdown(id="best")
            with Collapsible(title="Slow Solves"):
                yield Markdown(id="worst")

    def watch_show_dashboard(self) -> None:
        ids = ["#d_breezy", "#d_steady", "#d_edgy"]
        if self.show_dashboard:
            docs = attempts.all()
            breezy, steady, edgy = self.get_complete(docs)
            self.update_digits(ids, [breezy, steady // 2, edgy // 4])
            self.update_progress(breezy + steady + edgy)
            self.update_md(docs)

    def update_digit(self, id, value):
        self.query_one(f"{id}", Digits).update(f"{value}")

    def md_table(self, headers, rows):
        if not rows:
            return "\n\nNo records yet\n\n"
        sep = "|" + "|".join(["---"] * len(headers)) + "|"
        head = "|" + "|".join(headers) + "|"
        body = "\n".join("|" + "|".join(map(str, r)) + "|" for r in rows)
        return "\n".join([head, sep, body])

    def get_complete(self, docs):
        passed = set([doc["problem_id"] for doc in docs if doc["passed"]])
        breezy = len(self.breezy.intersection(passed))
        steady = len(self.steady.intersection(passed))
        edgy = len(self.edgy.intersection(passed))
        return breezy, steady * 2, edgy * 4

    def get_stats(self, docs):
        # get recent, frequent, fast and forever.
        latest, best, worst = {}, {}, {}
        for d in docs:
            pid = d["problem_id"]
            latest[pid] = max(d["created_at"], latest.get(pid, (0, 0))[0]), d["passed"]
            if d["passed"]:
                level = q.get(pid, {}).get("level", "")
                if (
                    (level == "Breezy" and d["elapsed"] <= 15 * 60)
                    or (level == "Steady" and d["elapsed"] <= 25 * 60)
                    or (level == "Edgy" and d["elapsed"] <= 35 * 60)
                ):
                    best[pid] = min(d["elapsed"], best.get(pid, float("inf")))
                else:
                    worst[pid] = min(d["elapsed"], worst.get(pid, float("inf")))
        fast = [
            (
                "🟢 " + q.get(id, {}).get("title", ""),
                q.get(id, {}).get("level", ""),
                fmt_secs(tm),
            )
            for id, tm in nsmallest(6, best.items(), key=lambda x: x[1])
        ]
        forever = [
            (
                "🟢 " + q.get(id, {}).get("title", ""),
                q.get(id, {}).get("level", ""),
                fmt_secs(tm),
            )
            for id, tm in nlargest(6, worst.items(), key=lambda x: x[1])
        ]
        recent = [
            (
                ("🟢 " if passed else "🔴 ") + q.get(id, {}).get("title", ""),
                q.get(id, {}).get("level", ""),
                time_ago(tm),
            )
            for id, (tm, passed) in nlargest(6, latest.items(), key=lambda x: x[1][0])
        ]
        return recent, fast, forever

    def update_md(self, docs) -> None:
        recent, fast, forever = self.get_stats(docs)
        latest = self.md_table(["Question", "Level", "When"], recent)
        best = self.md_table(["Question", "Level", "Best time"], fast)
        worst = self.md_table(["Question", "Level", "Best time"], forever)
        self.query_one("#recent", Markdown).update(latest)
        self.query_one("#best", Markdown).update(best)
        self.query_one("#worst", Markdown).update(worst)

    def update_digits(self, ids, values):
        for id, val in zip(ids, values):
            self.update_digit(id, val)

    def update_progress(self, value):
        self.query_one(ProgressBar).update(progress=value)
