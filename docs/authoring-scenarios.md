# Authoring a new scenario

Test cases are authored as plain-text **CSV**. CSV is the version-control-friendly, hand-authored source of truth: `run.ps1` loads a `.csv` spec directly into the runner (in memory) and runs it — there is no intermediate YAML file. See [csv-test-format.md](csv-test-format.md) for the full column reference.

## Two ways to get a CSV

- Copy [`test_cases/_template.csv`](../test_cases/_template.csv) and fill it in by hand. It already has the `# CONFIG` / `# STEPS` markers, the header row, and a few example step rows to adapt.
- Hand a rough/freeform CSV to the **`csv-test-formatter` skill** (under `.github/skills/`), which reformats it into the standard layout for you.

Keep `name`/`description` and all step values **literal** — no randomness — so reruns are bit-for-bit reproducible.

## Run the scenario

```powershell
.\run.ps1 test_cases\my_scenario.csv -q
```

Iterate on the `wait_ms` / `poll_*_ms` columns if you see flaky waits. [`test_cases/powershell_echo_loop.csv`](../test_cases/powershell_echo_loop.csv) is a complete worked example.

## Discovering selectors

Use **Inspect.exe** (ships with the Windows SDK, typically at `C:\Program Files (x86)\Windows Kits\10\bin\<version>\x64\Inspect.exe`) to discover UIA selectors for the controls you'll target:

- window title
- control `Name` / `AutomationId` / `ControlType`
- any other property you'll match against

## Selector convention

Prefer the **AutomationId + Name** pattern so the CSV survives small UI changes. Pass both into `find_control.py` via the step's `args`, and always give it a captured parent window hwnd:

```text
scripts/uia/find_control.py  ["{vars.hwnd}", "--auto-id", "CloseButton", "--name", "Close", "--name-fallback", "--control-type", "Button"]
```

When both `--auto-id` and `--name` are present, add `--name-fallback`: `scripts/uia/find_control.py` tries AutomationId first and, if it yields zero matches, retries with the auto_id filter dropped (name / type / class still apply). This makes scenarios resilient to AutomationId churn between app builds.

Capture the located control's coordinates with a `capture` mapping on that step (e.g. `{"vars.close_x": "$.rows[1].cols[7]", "vars.close_y": "$.rows[1].cols[8]"}`) and reference them as `{vars.close_x}` in later rows.

## Conditional loops

Most repetition should be **unrolled** — write each iteration as its own rows. When the number of repetitions is not known ahead of time (e.g. "keep remediating vulnerable packages until none remain"), use a `# LOOP` / `# END LOOP` block instead; it maps to a runner `while` step. See the "Conditional loops" section of [csv-test-format.md](csv-test-format.md).

## See also

- [csv-test-format.md](csv-test-format.md) — full CSV column and section reference.
- [test-spec-format.md](test-spec-format.md) — step types, placeholders, and capture syntax.
- [scripts-reference.md](scripts-reference.md) — catalog of every step script under `scripts/`.

## Running tests

Unit tests for the loader and runner live in `tests/`:

```powershell
uv run python -m unittest discover -s tests -v
```
