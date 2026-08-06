---
name: test-case-repair
description: Run a ui-auto CSV test case, repair each failing step with the smallest safe CSV change, rerun until it passes or is blocked, and write an HTML repair report matching test_cases/console_app_repair_report.html. Use when the user asks Copilot to run, fix, repair, or automatically repair a test case.
---

# Test case repair

Run and repair one existing CSV test case. Work automatically: inspect each failure, apply the smallest fix, rerun from the test case, and finish by writing an HTML repair report.

> **Markdown style:** do not hard-wrap prose in this file. Write one paragraph (and one list item) per line and let the editor soft-wrap. See [`AGENTS.md`](../../../AGENTS.md).

## Standard request

Treat a request such as the following as the complete instruction:

```text
Run and repair test_cases\<name>.csv automatically. For each failed step, diagnose the runner output, make the smallest safe change to the CSV, and rerun until the test passes or cannot continue. At the end, create test_cases\<name>_repair_report.html using the same format as test_cases\console_app_repair_report.html.
```

If the user does not provide a CSV path, ask for it. Do not choose a test case by guessing.

## Authoritative references

Before editing a test case, follow these sources in order:

1. `AGENTS.md`
2. `docs/csv-test-format.md`
3. `scripts/csvfmt/csv_schema.py`
4. `test_cases/_template.csv`

Never invent CSV columns, config keys, step types, script paths, selectors, or values. Verify every referenced script exists under `scripts\`.

## Repair workflow

1. Set the report path to the test case path with `.csv` replaced by `_repair_report.html`.
2. Run the test case from the repository root:

```powershell
.\run.ps1 test_cases\<name>.csv -q
```

3. If it passes, create the report with an empty repair table and final result `PASS`.
4. If it fails, record the attempt number, failed step id, concise failure reason, and the exact fix applied.
5. Inspect the failing CSV row, nearby dependent rows, runner stderr, and generated artifacts. Do not change unrelated steps.
6. Prefer repairing stale discovery and focus before changing user intent:
   - Re-discover windows or controls after launches and major UI transitions.
   - Capture refreshed handles and reuse captured values.
   - Activate the target window before keyboard input.
   - Replace guessed selectors with selectors supported by discovery output.
   - Prefer polling over increasing fixed waits.
7. Apply the smallest deterministic CSV change that addresses the observed failure. Preserve sequential `step no` values and portable paths.
8. Validate the edited CSV:

```powershell
uv run python scripts\csvfmt\csv_loader.py test_cases\<name>.csv
```

9. Rerun the full test case. Repeat only when the new failure provides actionable evidence for another safe repair.
10. Stop and report `BLOCKED` instead of guessing when repair requires unknown user intent, unavailable software, credentials, permissions, or a new script/schema capability.
11. Always write the HTML report after the final run, including failed attempts even when the final result is `BLOCKED`.

## Repair rules

- Edit the CSV only unless the failure proves an existing runner script is defective and the user asked to repair code too.
- Do not weaken assertions merely to make the test pass.
- Do not delete intended actions unless runner output proves the action is redundant, as with an auto-filtered UI.
- Do not randomize values or hardcode machine-specific paths, versions, titles, handles, or user names.
- Do not hide failures with broad matches that can select unrelated windows or controls.
- Keep screenshots and other run artifacts out of the repair report; summarize only evidence relevant to the repair.

## HTML report

Write a standalone UTF-8 HTML file using this exact structure and styling. HTML-escape all inserted text. Use one table row per failed run; do not add a row for the final successful run.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TEST_TITLE Repair Report</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #24292f; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #d0d7de; padding: 0.75rem; text-align: left; vertical-align: top; }
    th { background: #f6f8fa; }
    .pass { color: #1a7f37; font-weight: 700; }
    .blocked { color: #cf222e; font-weight: 700; }
  </style>
</head>
<body>
  <h1>TEST_TITLE Repair Report</h1>
  <p><strong>Test case:</strong> <code>TEST_CASE_PATH</code></p>
  <p><strong>Final result:</strong> <span class="RESULT_CLASS">FINAL_RESULT</span></p>
  <table>
    <thead>
      <tr>
        <th>Attempt</th>
        <th>Failed step</th>
        <th>Failure</th>
        <th>Fix applied</th>
      </tr>
    </thead>
    <tbody>
      REPAIR_ROWS
    </tbody>
  </table>
</body>
</html>
```

Replace:

- `TEST_TITLE` with the test case name converted to readable title case.
- `TEST_CASE_PATH` with the repository-relative Windows path.
- `FINAL_RESULT` with `PASS` or `BLOCKED`.
- `RESULT_CLASS` with `pass` or `blocked`.
- `REPAIR_ROWS` with rows in chronological order:

```html
      <tr>
        <td>ATTEMPT_NUMBER</td>
        <td><code>FAILED_STEP_ID</code></td>
        <td>FAILURE_SUMMARY</td>
        <td>FIX_SUMMARY</td>
      </tr>
```

For a first-run pass, leave `<tbody>` empty. For a blocked attempt where no fix was safe, write `No change applied; repair requires USER_OR_ENVIRONMENT_REQUIREMENT.` in the final `Fix applied` cell.

## Final response

State the final result, repaired CSV path, and report path. If blocked, state the single blocking reason. Do not paste the full report or narrate every rerun.
