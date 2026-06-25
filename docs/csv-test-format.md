# CSV test-case format

Test cases can be authored as a plain-text **CSV** instead of YAML. CSV is the version-control-friendly, **hand-authored source of truth**: `run.ps1` loads a `.csv` spec directly into the runner (in memory) and runs it — there is no intermediate YAML file.

```powershell
# Run a CSV test case directly
.\run.ps1 test_cases\powershell_echo_loop.csv -q
```

The CSV is laid out for **readability**: steps are grouped into numbered phases with plain-English descriptions on the left, the values needed to run in the middle, and an `Expected` note on the right. Loops are **unrolled** — each iteration is its own set of rows; there is no `foreach`.

Two ways to get a standard-format CSV:

- Copy `test_cases/_template.csv` and fill it in by hand.
- Hand a rough/freeform CSV to the **`csv-test-formatter` skill** (under `.github/skills/`), which reformats it into the standard layout for you.

## File layout

One `.csv` per test, with two marker-delimited sections. The marker is a row whose first cell is `# CONFIG` or `# STEPS` (case-insensitive); each section has its own header row. Sections may have different column counts (CSV ragged rows are fine).

```
# CONFIG
Section,Key,Value
name,,powershell_echo_loop
description,,"Open Windows PowerShell ..."
artifacts,screenshot_dir,screenshots/{timestamp}

# STEPS
No,Main step,Trigger,script,args,wait_ms,capture,expect_exit,expected_contains,poll_total_ms,poll_interval_ms,screenshot_pass,screenshot_fail,Expected
1,Launch powershell,Open Start menu via Win key.,scripts/input/key.py,"[""win""]",700,,,,,,,,
1,,Type 'powershell' into the Start menu.,scripts/input/type_text.py,"[""powershell""]",1200,,,,,,,,
```

### `# CONFIG` section (minimal)

Three columns: `Section | Key | Value`. Only what the runner actually needs:

| Section | Notes |
|---|---|
| `name` | one row; `Value` holds the test name |
| `description` | one row |
| `artifacts` | `screenshot_dir` (uses `{timestamp}`); the runner creates this folder up front |

There is **no** `inputs`, `timing`, or `expected_results` block — those values now live on the step rows (see below). The parsed spec simply omits those optional top-level keys; the runner tolerates their absence.

### `# STEPS` section

One row per runnable step, in execution order. A row with a blank `script` is skipped.

Readable columns (authoring-facing, **ignored on import**):

| Column | Meaning |
|---|---|
| **No** | Phase number. Repeated or left blank to continue within a phase. |
| **Main step** | Phase name, on the first row of each phase only. |
| **Trigger** | Human-readable action — becomes the step's `description`. |
| **Expected** | Expected-result note for that step. Documentation only. |

Runnable columns:

| Column | Maps to YAML | Notes |
|---|---|---|
| `script` | `script` | required for every real step |
| `args` | `args` (JSON list) | always rendered — `{vars...}`, `{timestamp}`, `{a + b}` arithmetic all work |
| `wait_ms` | `wait_after` | **literal milliseconds** (e.g. `700`) |
| `capture` | `capture` | JSON object mapping `vars.x` → a `$.cols[i]` / `$.rows[j].cols[i]` selector |
| `expect_exit` | `expect_exit` | set non-zero to assert the script fails |
| `expected_contains` | `expected_contains_expr` | presence makes the step an `assert_console_contains` |
| `poll_total_ms` / `poll_interval_ms` | same keys | **literal milliseconds** for the assert's polling |
| `screenshot_pass` / `screenshot_fail` | `args_expr_on_pass` / `args_expr_on_fail` | JSON list of filename patterns; the loader prepends `{artifacts.screenshot_dir}/` |
| `max_iter` | `max_iterations` | **`# LOOP` rows only** — safety cap on a conditional `while` loop (see below) |

**No `id`, `type`, or `args_mode` columns** — the loader derives them:

- **`id`** is auto-generated (`step_1`, `step_2`, …); the runner only uses it for log/failure messages.
- **`type`** is inferred: `screenshot_pass` set → `screenshot`; `expected_contains` set → `assert_console_contains`; otherwise the **script basename** (e.g. `key`, `click`, `type_text`, `find_window`, `find_control`).
- **`args` is always rendered**, so there is no `plain`/`expr` distinction — the runner applies `{placeholder}` substitution to every args string.

Screenshots stay their own explicit step rows; use the `{ss}` ordering placeholder in the `screenshot_pass` / `screenshot_fail` filename (e.g. `{ss}.png`) — see [test-spec-format.md](test-spec-format.md). With loops unrolled, the `{ss}` counter runs globally `ss_1..ss_N`.

## Conditional loops (`# LOOP` / `# END LOOP`)

Most repetition should be **unrolled** (write the rows out). When the number of repetitions is **not known ahead of time** — e.g. "keep remediating vulnerable packages until none remain" — use a `# LOOP` block instead. It maps to a runner `while` step.

```
# STEPS
No,Main step,Trigger,script,args,wait_ms,capture,expect_exit,expected_contains,poll_total_ms,poll_interval_ms,screenshot_pass,screenshot_fail,max_iter,Expected
# LOOP,Drain list,While a Vulnerable row exists capture its coords.,scripts/uia/find_control.py,"[""{vars.hwnd}"", ""--name"", ""Vulnerable"", ""--control-type"", ""ListItem""]",,"{""vars.row_x"": ""$.rows[1].cols[7]"", ""vars.row_y"": ""$.rows[1].cols[8]""}",0,,,,,,10,Loop while a vulnerable row exists.
2,,Click the captured row.,scripts/input/click.py,"[""{vars.row_x}"", ""{vars.row_y}""]",200,,,,,,,,,
2,,Press enter to update it.,scripts/input/key.py,"[""enter""]",200,,,,,,,,,
# END LOOP,,,,,,,,,,,,,,
```

Rules:

- A row whose **first cell (`No` column)** is `# LOOP` opens the block; the matching `# END LOOP` row closes it. The rows in between are the loop **body** (ordinary step rows).
- The `# LOOP` row itself is the loop **condition**: its `script` + `args` are run before every pass. The loop **continues while the condition's exit code equals `expect_exit`** (default `0`) and **stops** otherwise. With `find_control` (exit `0` = found, `1` = not found), the loop runs while a matching control still exists.
- The `# LOOP` row may carry a `capture` mapping — applied to the condition's stdout each pass — so the probe can capture the current target's coordinates for the body to act on.
- `max_iter` (on the `# LOOP` row) caps the iteration count as a safety net against an infinite loop. If omitted, a built-in default applies (`run_test.WHILE_MAX_ITERATIONS`).
- `{ss}` is continuous across the whole run; it does **not** reset at the start of each iteration, so loop screenshots keep counting up (`ss_7`, `ss_8`, ...).

## Loader and skill

| Component | Purpose |
|---|---|
| `scripts\csvfmt\csv_loader.py` | Parses a standard-format CSV into the spec dict the runner executes. `run_test.py` calls `load()` for any `.csv` spec, so CSV runs directly. Run `uv run python scripts\csvfmt\csv_loader.py <file.csv>` to print the parsed spec as JSON for debugging. |
| `scripts\csvfmt\csv_schema.py` | Defines the shared section markers and column layout. |
| `.github\skills\csv-test-formatter\SKILL.md` | Copilot CLI skill that reformats a rough/freeform CSV into this standard layout. |
| `test_cases\_template.csv` | Standard-format skeleton to copy when authoring by hand. |

## Caveats

- `No`, `Main step`, and `Expected` are CSV-only annotations — they never appear in the parsed spec.
- Complex cell values (`args`, `capture`, screenshot patterns) are stored as JSON so they stay lossless and inspectable; the `csv` module quotes/escapes them safely.
- `wait_ms` / `poll_*_ms` are raw integer milliseconds. (The runner also still accepts a `timing`-key name there for hand-written YAML, but the CSV format uses literal numbers.)
