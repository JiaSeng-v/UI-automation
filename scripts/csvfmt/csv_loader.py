"""Load a combined CSV test case into a runnable spec dict (in memory).

`run_test.py` calls :func:`load` directly for ``.csv`` specs, so a CSV runs
straight from disk with no intermediate YAML file. The returned dict is the
same structure ``run_test.py`` gets from ``yaml.safe_load`` for a ``.yaml``
spec.

Run a CSV test case via the runner:

    .\\run.ps1 test_cases\\powershell_echo_loop.csv -q

For debugging you can print the parsed spec as JSON:

    python scripts/csvfmt/csv_loader.py <file.csv>
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csv_schema as S  # noqa: E402


def _split_sections(rows):
    """Return (config_rows, steps_rows) split on the section markers."""
    config_rows, steps_rows = [], []
    target = None
    for row in rows:
        if not row or all(S.blank(c) for c in row):
            continue
        if S.is_marker(row, S.CONFIG_MARKER):
            target = config_rows
            continue
        if S.is_marker(row, S.STEPS_MARKER):
            target = steps_rows
            continue
        if target is not None:
            target.append(row)
    return config_rows, steps_rows


def _cell(row, i):
    return row[i] if i < len(row) else None


def _int(value):
    s = str(value).strip()
    return int(s) if s.lstrip("-").isdigit() else value


def _infer_type(cells, script):
    """Type is no longer a column; derive it from the row.

    - a screenshot pattern  -> screenshot
    - an expected_contains   -> assert_console_contains
    - otherwise the script's basename (key, click, type_text, find_window, ...)
    """
    if not S.blank(cells.get("screenshot_pass")) or \
            not S.blank(cells.get("screenshot_fail")):
        return "screenshot"
    if not S.blank(cells.get("expected_contains")):
        return "assert_console_contains"
    if script:
        return os.path.splitext(os.path.basename(script))[0]
    return "run"


def _row_to_step(cells, step_id, screenshot_dir):
    def g(name):
        return cells.get(name)

    script = None if S.blank(g("script")) else g("script")
    step = {"id": step_id, "type": _infer_type(cells, script)}
    if not S.blank(g("Trigger")):
        step["description"] = g("Trigger")
    if script is not None:
        step["script"] = script

    if not S.blank(g("args")):
        step["args"] = S.loads_list(g("args"))

    if not S.blank(g("wait_ms")):
        step["wait_after"] = _int(g("wait_ms"))
    if not S.blank(g("capture")):
        step["capture"] = S.loads_obj(g("capture"))
    if not S.blank(g("expect_exit")):
        step["expect_exit"] = int(g("expect_exit"))
    if not S.blank(g("expected_contains")):
        step["expected_contains_expr"] = g("expected_contains")
    if not S.blank(g("poll_total_ms")):
        step["poll_total_ms"] = _int(g("poll_total_ms"))
    if not S.blank(g("poll_interval_ms")):
        step["poll_interval_ms"] = _int(g("poll_interval_ms"))
    if not S.blank(g("screenshot_pass")):
        step["args_expr_on_pass"] = _shot_paths(g("screenshot_pass"), screenshot_dir)
    if not S.blank(g("screenshot_fail")):
        step["args_expr_on_fail"] = _shot_paths(g("screenshot_fail"), screenshot_dir)
    return step


def _shot_paths(cell, screenshot_dir):
    """Prepend the configured screenshot dir to each filename pattern."""
    names = S.loads_list(cell)
    if not screenshot_dir:
        return names
    return [f"{screenshot_dir}/{n}" for n in names]


def _build_while(cells, loop_id, body):
    """Build a `while` step from a `# LOOP` condition row plus its body steps."""
    def g(name):
        return cells.get(name)

    condition = {"script": g("script")}
    if not S.blank(g("args")):
        condition["args"] = S.loads_list(g("args"))
    if not S.blank(g("capture")):
        condition["capture"] = S.loads_obj(g("capture"))
    if not S.blank(g("expect_exit")):
        condition["expect_exit"] = int(g("expect_exit"))

    step = {"id": loop_id, "type": "while", "condition": condition, "body": body}
    if not S.blank(g("max_iter")):
        step["max_iterations"] = int(g("max_iter"))
    return step


def _build_steps(steps_rows, screenshot_dir):
    """Each row with a `script` is one step (flat list, in order).

    `# LOOP` / `# END LOOP` marker rows (in the `No` column) delimit a
    conditional while-loop: the `# LOOP` row carries the loop condition and the
    rows up to `# END LOOP` form the loop body (a nested step list).

    The readable `No` / `Main step` / `Expected` columns are authoring
    annotations and are ignored here. Step ids are auto-generated.
    """
    if not steps_rows:
        return []
    header = [str(h).strip() for h in steps_rows[0]]

    def cells_for(raw):
        return {header[i]: _cell(raw, i) for i in range(len(header))}

    def marker(raw):
        return raw[0].strip().upper() if raw and raw[0] else ""

    steps = []
    n = 0
    body_rows = steps_rows[1:]
    idx = 0
    while idx < len(body_rows):
        raw = body_rows[idx]
        if marker(raw) == S.LOOP_START_MARKER:
            n += 1
            loop_id = f"step_{n}"
            cond_cells = cells_for(raw)
            inner = []
            idx += 1
            while idx < len(body_rows) and marker(body_rows[idx]) != S.LOOP_END_MARKER:
                inner_cells = cells_for(body_rows[idx])
                if not S.blank(inner_cells.get("script")):
                    n += 1
                    inner.append(_row_to_step(inner_cells, f"step_{n}", screenshot_dir))
                idx += 1
            steps.append(_build_while(cond_cells, loop_id, inner))
            idx += 1  # skip the # END LOOP row
            continue
        cells = cells_for(raw)
        if not S.blank(cells.get("script")):
            n += 1
            steps.append(_row_to_step(cells, f"step_{n}", screenshot_dir))
        idx += 1
    return steps


def _coerce(value):
    """CSV stores everything as text; restore ints for numeric cells."""
    if isinstance(value, str):
        s = value.strip()
        if s and (s.isdigit() or (s[0] == "-" and s[1:].isdigit())):
            return int(s)
    return value


def _build_config(config_rows):
    spec = {}
    inputs = {}
    expected = []
    # skip the Section/Key/Value header row if present
    start = 1 if config_rows and config_rows[0] and \
        config_rows[0][0].strip().lower() == "section" else 0
    for raw in config_rows[start:]:
        section = raw[0] if len(raw) > 0 else None
        key = raw[1] if len(raw) > 1 else None
        value = raw[2] if len(raw) > 2 else None
        if S.blank(section):
            continue
        section = section.strip()
        if section == "name":
            spec["name"] = value
        elif section == "description":
            spec["description"] = value
        elif section == "inputs":
            inputs.setdefault(key, []).append(value)
        elif section in S.CONFIG_MAP_SECTIONS:
            spec.setdefault(section, {})[key] = _coerce(value)
        elif section == "expected_results":
            expected.append(value)
    if inputs:
        spec["inputs"] = {
            k: (v if len(v) > 1 else v[0]) for k, v in inputs.items()
        }
    if expected:
        spec["expected_results"] = expected
    return spec


def load(csv_path):
    """Parse a standard-format CSV test case into a runnable spec dict."""
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    config_rows, steps_rows = _split_sections(rows)
    spec = _build_config(config_rows)
    spec["steps"] = _build_steps(steps_rows, "{artifacts.screenshot_dir}")
    ordered = {k: spec[k] for k in S.SPEC_KEY_ORDER if k in spec}
    for k, v in spec.items():
        if k not in ordered:
            ordered[k] = v
    return ordered


# Backwards-compatible alias.
convert = load


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv")
    a = ap.parse_args()
    spec = load(a.csv)
    json.dump(spec, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
