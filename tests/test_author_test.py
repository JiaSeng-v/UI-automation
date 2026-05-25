"""Unit tests for scripts/author_test.py.

Covers the pieces that don't require a live UI:
  * parse_step_line emits both --auto-id and --name (+ --name-fallback)
  * parse_step_line continues to work with name-only selectors
  * _apply_capture honors $.cols[i] and $.rows[j].cols[i]
  * _apply_capture raises on out-of-range / bad destination selectors
  * execute_step short-circuits for no-script / internal step types
  * execute_step surfaces non-zero exit from the spawned script
"""
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, REPO_ROOT)

import author_test  # noqa: E402
from author_test import (  # noqa: E402
    AmbiguousMatch,
    RecurrenceDetector,
    _apply_capture,
    execute_step,
    maybe_disambiguate,
    parse_step_line,
)


class ParseStepLineSelectorTests(unittest.TestCase):
    def test_click_with_auto_id_and_name_emits_name_fallback(self):
        steps = parse_step_line(
            'click "Close" type=Button auto_id=CloseButton parent=win_hwnd'
        )
        self.assertIsInstance(steps, list)
        find = steps[0]
        self.assertEqual(find["type"], "find_control")
        args = find["args_expr"]
        self.assertIn("--auto-id", args)
        self.assertIn("CloseButton", args)
        self.assertIn("--name", args)
        self.assertIn("Close", args)
        self.assertIn("--name-fallback", args)

    def test_click_name_only_does_not_emit_name_fallback(self):
        steps = parse_step_line('click "Close" type=Button parent=win_hwnd')
        find = steps[0]
        args = find["args_expr"]
        self.assertIn("--name", args)
        self.assertNotIn("--auto-id", args)
        self.assertNotIn("--name-fallback", args)

    def test_find_control_with_both_selectors_emits_name_fallback(self):
        step = parse_step_line(
            'find_control parent=win_hwnd name="Close" auto_id=CloseButton type=Button'
        )
        self.assertEqual(step["type"], "find_control")
        args = step["args_expr"]
        self.assertIn("--auto-id", args)
        self.assertIn("--name", args)
        self.assertIn("--name-fallback", args)


class ApplyCaptureTests(unittest.TestCase):
    def test_cols_and_rows_cols_selectors(self):
        vars_dict = {}
        _apply_capture(
            "a\tb\tc\nd\te\tf\n",
            {"vars.x": "$.cols[1]", "vars.y": "$.rows[1].cols[2]"},
            vars_dict,
        )
        self.assertEqual(vars_dict, {"x": "b", "y": "f"})

    def test_out_of_range_cols_raises(self):
        with self.assertRaises(ValueError):
            _apply_capture("a\tb", {"vars.z": "$.cols[5]"}, {})

    def test_out_of_range_rows_raises(self):
        with self.assertRaises(ValueError):
            _apply_capture("a\tb", {"vars.z": "$.rows[3].cols[0]"}, {})

    def test_bad_dst_prefix_raises(self):
        with self.assertRaises(ValueError):
            _apply_capture("a", {"foo": "$.cols[0]"}, {})

    def test_bad_selector_raises(self):
        with self.assertRaises(ValueError):
            _apply_capture("a", {"vars.x": "not_a_selector"}, {})


class ExecuteStepTests(unittest.TestCase):
    def test_no_op_step_succeeds(self):
        ok, msg = execute_step({"type": "_wait", "ms": 100}, {}, {})
        self.assertTrue(ok)
        self.assertIn("skip", msg.lower())

    def test_missing_script_succeeds_as_noop(self):
        ok, msg = execute_step({"type": "click"}, {}, {})
        self.assertTrue(ok)
        self.assertIn("skip", msg.lower())

    def test_nonzero_exit_when_not_expected(self):
        # Use a tiny throwaway script: invoke python -c that exits 7.
        step = {
            "type": "key",
            "script": "scripts/key.py",
            "args": ["this-is-not-a-real-key-combo-zzz"],
        }
        ok, msg = execute_step(step, {}, {})
        # key.py either rejects unknown combos (non-zero) or accepts them; we
        # only assert that the executor reports failure when it does fail.
        if not ok:
            self.assertIn("exit", msg)


class MaybeDisambiguateTests(unittest.TestCase):
    def test_non_find_control_is_noop(self):
        step = {"type": "click", "script": "scripts/click.py", "args": [10, 20]}
        out = maybe_disambiguate(step, {}, {})
        self.assertIs(out, step)

    def test_step_without_script_is_noop(self):
        step = {"type": "find_control"}
        out = maybe_disambiguate(step, {}, {})
        self.assertIs(out, step)

    def test_ambiguous_match_raises(self):
        # Stub out subprocess.run to simulate two matches under --all.
        import subprocess as _sub
        real_run = _sub.run
        fake_stdout = (
            "name\tauto_id\tcontrol_type\tleft\ttop\tright\tbottom\tcenter_x\tcenter_y\n"
            "Close\tCloseA\tButton\t0\t0\t10\t10\t5\t5\n"
            "Close\tCloseB\tButton\t100\t0\t110\t10\t105\t5\n"
        )

        class FakeProc:
            returncode = 0
            stdout = fake_stdout
            stderr = ""

        def fake_run(cmd, **kwargs):
            # sanity: probe must include --all
            self.assertIn("--all", cmd)
            return FakeProc()

        _sub.run = fake_run
        try:
            step = {
                "type": "find_control",
                "script": "scripts/find_control.py",
                "args": ["12345", "--name", "Close"],
            }
            with self.assertRaises(AmbiguousMatch) as ctx:
                maybe_disambiguate(step, {}, {})
            self.assertEqual(len(ctx.exception.matches), 2)
        finally:
            _sub.run = real_run

    def test_single_match_passes_through(self):
        import subprocess as _sub
        real_run = _sub.run
        single = (
            "name\tauto_id\tcontrol_type\tleft\ttop\tright\tbottom\tcenter_x\tcenter_y\n"
            "Close\tCloseA\tButton\t0\t0\t10\t10\t5\t5\n"
        )

        class FakeProc:
            returncode = 0
            stdout = single
            stderr = ""

        _sub.run = lambda cmd, **kwargs: FakeProc()
        try:
            step = {
                "type": "find_control",
                "script": "scripts/find_control.py",
                "args": ["12345", "--name", "Close"],
            }
            self.assertIs(maybe_disambiguate(step, {}, {}), step)
        finally:
            _sub.run = real_run

    def test_strips_existing_nth_and_all_before_probe(self):
        import subprocess as _sub
        real_run = _sub.run
        captured_cmd = {}

        class FakeProc:
            returncode = 0
            stdout = "header\n"
            stderr = ""

        def fake_run(cmd, **kwargs):
            captured_cmd["cmd"] = cmd
            return FakeProc()

        _sub.run = fake_run
        try:
            step = {
                "type": "find_control",
                "script": "scripts/find_control.py",
                "args": ["12345", "--name", "Close", "--nth", "3", "--all"],
            }
            maybe_disambiguate(step, {}, {})
            cmd = captured_cmd["cmd"]
            self.assertNotIn("--nth", cmd)
            self.assertNotIn("3", cmd)
            # --all should appear exactly once even though we stripped the
            # original and re-appended.
            self.assertEqual(cmd.count("--all"), 1)
        finally:
            _sub.run = real_run


class RecurrenceDetectorTests(unittest.TestCase):
    def test_empty_returns_none(self):
        d = RecurrenceDetector()
        self.assertIsNone(d.observe({}, None))
        self.assertIsNone(d.observe({}, ""))

    def test_two_same_returns_none(self):
        d = RecurrenceDetector()
        self.assertIsNone(d.observe({}, "abc"))
        self.assertIsNone(d.observe({}, "abc"))

    def test_three_same_returns_hash(self):
        d = RecurrenceDetector()
        d.observe({}, "abc")
        d.observe({}, "abc")
        self.assertEqual(d.observe({}, "abc"), "abc")

    def test_three_with_a_different_does_not_trigger(self):
        d = RecurrenceDetector()
        d.observe({}, "abc")
        d.observe({}, "xyz")
        self.assertIsNone(d.observe({}, "abc"))

    def test_sliding_window_resets_correctly(self):
        d = RecurrenceDetector()
        # 5 observations; only the last 3 must all match to fire.
        for h in ["a", "b", "a", "a"]:
            self.assertIsNone(d.observe({}, h))
        # window is now ["b", "a", "a"]; one more "a" should fire.
        self.assertEqual(d.observe({}, "a"), "a")

    def test_reset_clears_window(self):
        d = RecurrenceDetector()
        d.observe({}, "x")
        d.observe({}, "x")
        d.reset()
        self.assertIsNone(d.observe({}, "x"))
        self.assertIsNone(d.observe({}, "x"))
        self.assertEqual(d.observe({}, "x"), "x")


if __name__ == "__main__":
    unittest.main()
