from textual.screen import ModalScreen
from textual.widgets import RichLog, Static, Footer
from algoflex.questions import questions
from algoflex.db import get_db
from algoflex.utils import fmt_secs
from tinydb import Query
from pathlib import Path
import tempfile
import os
import time
import asyncio

KV = Query()


class ResultModal(ModalScreen):
    BINDINGS = [("s", "dismiss", "dismiss")]
    DEFAULT_CSS = """
    ResultModal {
        &>* {
            max-width: 90;
        }
        align: center middle;
        RichLog {
            width: 1fr;
            height: 12;
            padding: 1 0;
            padding-left: 2;
            overflow-x: auto;
            background: $boost;
        }
    }
    """
    TEST_CODE = """
import sys

def run_tests():
    total, passed = len(test_cases), 0
    for i, [input, expected] in enumerate(test_cases):
        try:
            if input == expected:
                print(f"[green][b]✓[/] test case {i+1} passed![/]")
                passed += 1
            else:
                print(f"[red][b]x[/] test case {i+1} failed![/]\\n\\t[b]got[/]: [red]{input}[/]\\n\\t[b]expected[/]: [green]{expected}[/]")
                return 1
        except Exception as e:
            print(f"[red][b]x[/] test case {i+1} error![/]\\n\\t[b]error[/]: {e}")
            return 1
    if passed == total:
        print(f"\\n{passed}/{total} passed!")
        return 0
    if passed < total:
        print(f"\\n {total - passed} failing.")
    return 1

if __name__ == "__main__":
    sys.exit(run_tests())
    """

    def __init__(self, problem_id, user_code, elapsed, best):
        super().__init__()
        self.problem_id = problem_id
        self.user_code = user_code
        self.elapsed = elapsed
        self.best = best

    def on_mount(self) -> None:
        asyncio.create_task(self.run_user_code())

    def compose(self):
        yield RichLog(markup=True, wrap=True, max_lines=1_000)
        yield Footer()

    async def run_user_code(self) -> None:
        attempts = get_db()
        now = time.time()
        passed = False

        output_log = self.query_one(RichLog)
        output_log.loading = True

        user_code = self.user_code.strip()
        question = questions.get(self.problem_id, {})
        test_cases = question.get("test_cases", [])
        test_code = question.get("test_code", self.TEST_CODE)
        full_code = f"{user_code}\n\n{test_cases}\n\n{test_code}"

        tmp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".py",
                mode="w",
                encoding="utf-8",
            ) as f:
                f.write(full_code)
                tmp_path = f.name

            # spawn async subprocess
            proc = await asyncio.create_subprocess_exec(
                "python",
                tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            async def stream(pipe, is_err=False):
                while True:
                    line = await pipe.readline()
                    if not line:
                        break
                    text = line.decode().rstrip()
                    if is_err:
                        output_log.write(f"[red]{text}[/]", animate=True)
                    else:
                        output_log.write(text, animate=True)

            # stream output with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        stream(proc.stdout),
                        stream(proc.stderr, is_err=True),
                    ),
                    timeout=9,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                output_log.write(
                    "[red]Execution timed out[/]\n\tYour solution must run within 9 seconds"
                )
                return

            rc = await proc.wait()

            if rc == 0:
                passed = True
                if not self.best or self.elapsed < self.best:
                    self.new_best()

        except Exception as e:
            output_log.write(f"[red]Error running code[/]\n\t{e}")

        finally:
            if tmp_path and Path(tmp_path).exists():
                os.remove(tmp_path)
            output_log.loading = False

            attempts.insert(
                {
                    "problem_id": self.problem_id,
                    "passed": passed,
                    "elapsed": self.elapsed,
                    "created_at": now,
                    "code": user_code if passed else "",
                }
            )

    def new_best(self):
        widget = Static(f"[b]New best time! --> {fmt_secs(self.elapsed)}[/]")
        widget.styles.height = 3
        widget.styles.content_align = ("center", "middle")
        widget.styles.background = "#303134"
        self.mount(widget)
