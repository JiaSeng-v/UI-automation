---
name: test-case-repair
description: Run a ui-auto CSV test case, repair each failing step with the smallest safe CSV change, rerun until it passes or is blocked, and write an HTML repair report matching test_cases/console_app_repair_report.html.
---

# Test case repair

Repair one existing CSV test case automatically. Follow `AGENTS.md` for authoring rules and use `scripts/csvfmt/csv_loader.py` for strict validation.

## Input and output

- Required input: the CSV path.
- Report path: replace `.csv` with `_repair_report.html` unless the user provides a path.
- If no CSV path is provided, ask for it instead of guessing.

## Workflow

1. Run the complete test:

```powershell
.\run.ps1 test_cases\<name>.csv -q
```

2. If it passes, create an empty repair report with final result `PASS`.
3. If it fails, record the attempt, failed step, failure, and exact fix.
4. Inspect the failed row, dependent rows, stderr, and relevant artifacts.
5. Make the smallest deterministic CSV change supported by observed evidence.
6. Do not weaken assertions, change tester intent, or guess unknown selectors.
7. Validate the edited CSV:

```powershell
uv run python scripts\csvfmt\csv_loader.py test_cases\<name>.csv
```

8. Rerun the complete test.
9. Repeat while failures provide evidence for a safe repair.
10. Stop with `BLOCKED` when progress requires unavailable software, credentials, permissions, user intent, or a new script or schema capability.
11. Always write the HTML report.

## Report

Use `test_cases/console_app_repair_report.html` as the format. Write standalone UTF-8 HTML, escape inserted text, list one row per failed attempt, and show final result `PASS` or `BLOCKED`. Do not add a row for the final successful run.

## Final response

State the final result, repaired CSV path, and report path. If blocked, state the single blocking reason.
