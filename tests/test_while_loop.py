"""Execution tests for the runner's `while` step type (run_test.exec_step)."""
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import run_test  # noqa: E402


# A condition script that exits 0 while a shared counter file's value is below a
# threshold, then exits 1. It also prints a find_control-style tab row so the
# loop's `capture` has something to parse.
_COND_SRC = '''\
import sys
counter_file, limit = sys.argv[1], int(sys.argv[2])
try:
    with open(counter_file) as f:
        n = int(f.read() or "0")
except FileNotFoundError:
    n = 0
if n >= limit:
    print("no match", file=sys.stderr)
    sys.exit(1)
print("name\\tauto_id\\tcontrol_type\\tleft\\ttop\\tright\\tbottom\\tcenter_x\\tcenter_y")
print("Vulnerable\\t\\tListItem\\t0\\t0\\t10\\t10\\t5\\t5")
sys.exit(0)
'''

# A body script that increments the shared counter file by one.
_BODY_SRC = '''\
import sys
counter_file = sys.argv[1]
try:
    with open(counter_file) as f:
        n = int(f.read() or "0")
except FileNotFoundError:
    n = 0
with open(counter_file, "w") as f:
    f.write(str(n + 1))
'''


class WhileStepTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.counter = os.path.join(self.tmp, "counter.txt")
        self.cond = os.path.join(self.tmp, "cond.py")
        self.body = os.path.join(self.tmp, "body.py")
        with open(self.cond, "w") as f:
            f.write(_COND_SRC)
        with open(self.body, "w") as f:
            f.write(_BODY_SRC)
        run_test.QUIET = True

    def _make_ctx(self):
        spec = {"name": "t", "artifacts": {"screenshot_dir": self.tmp}, "steps": []}
        return run_test.Ctx(spec)

    def test_while_loops_until_condition_false(self):
        ctx = self._make_ctx()
        step = {
            "id": "loop",
            "type": "while",
            "condition": {"script": self.cond, "args": [self.counter, "3"],
                          "expect_exit": 0},
            "body": [{"id": "b", "type": "key", "script": self.body,
                      "args": [self.counter]}],
        }
        run_test.exec_step(step, ctx, {})
        # body ran exactly 3 times (counter reached the limit, then cond exits 1)
        with open(self.counter) as f:
            self.assertEqual(int(f.read()), 3)

    def test_while_max_iterations_failure_when_not_converged(self):
        ctx = self._make_ctx()
        step = {
            "id": "loop",
            "type": "while",
            # condition limit is high, so it never goes false; max_iterations caps
            # the loop at 2 and then fails because the loop did not converge.
            "condition": {"script": self.cond, "args": [self.counter, "999"],
                          "expect_exit": 0},
            "max_iterations": 2,
            "body": [{"id": "b", "type": "key", "script": self.body,
                      "args": [self.counter]}],
        }
        with self.assertRaises(AssertionError):
            run_test.exec_step(step, ctx, {})
        # body still ran exactly max_iterations (2) times before failing
        with open(self.counter) as f:
            self.assertEqual(int(f.read()), 2)

    def test_while_condition_capture_populates_vars(self):
        ctx = self._make_ctx()
        step = {
            "id": "loop",
            "type": "while",
            "condition": {"script": self.cond, "args": [self.counter, "1"],
                          "expect_exit": 0,
                          "capture": {"vars.row_x": "$.rows[1].cols[7]",
                                      "vars.row_y": "$.rows[1].cols[8]"}},
            "body": [{"id": "b", "type": "key", "script": self.body,
                      "args": [self.counter]}],
        }
        run_test.exec_step(step, ctx, {})
        self.assertEqual(ctx.vars.get("row_x"), "5")
        self.assertEqual(ctx.vars.get("row_y"), "5")


if __name__ == "__main__":
    unittest.main()
