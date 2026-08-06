# UI-automation

Declarative UI-automation toolkit for Windows desktop apps. Drives mouse, keyboard, screenshots, and UIA-based validation from simple CSV scenarios.

## Install

One PowerShell command on a fresh Windows 10/11 machine:

```powershell
irm https://raw.githubusercontent.com/william051200/UI-automation/main/install.ps1 | iex
```

This installs `uv` + Python + `git` as needed, clones the repo to `%USERPROFILE%\UI-automation`, and installs all pinned dependencies.

## Run the example

```powershell
cd $HOME\UI-automation
.\run.ps1 test_cases\powershell_echo_loop.csv
```

(equivalent to `uv run python run_test.py test_cases\powershell_echo_loop.csv`.)

Scenarios are authored as readable CSV files — `run.ps1` loads the `.csv` directly:

```powershell
.\run.ps1 test_cases\powershell_echo_loop.csv -q
```

See [CSV test-case format](docs/csv-test-format.md) for the file layout, the in-memory loader, and the `csv-test-formatter` skill.

The example opens PowerShell via Start menu, echoes 4 fixed strings, validates each via UIA, saves a screenshot per iteration, then closes the window with a mouse-click on the UIA-located Close button.

Exit codes: `0` pass, `1` assertion failed, `2` runner error.

Add `-q` (or `--quiet`) to suppress per-step echo and successful subcommand stdout; failures, stderr, and the final RESULT line are always shown.

## Author a new scenario

Describe your scenario as plain numbered steps and let an AI agent convert it into a runnable CSV test case — you don't need to know which script implements each action or its arguments:

```text
1. Open Notepad from the Start menu.
2. Type "hello from copilot".
3. Save as %TEMP%\out.txt with Ctrl+S.
4. Assert the file exists.
5. Close Notepad.
```

> Convert these steps into `test_cases/notepad_save.csv` and validate it by running `.\run.ps1 test_cases\notepad_save.csv -q`.

See [`docs/authoring-scenarios.md`](docs/authoring-scenarios.md) for the full workflow and more example prompts.

## Run the tests

```powershell
uv run python -m unittest discover -s tests -v
```

37 stdlib `unittest` cases covering the helper scripts and the CSV loader — no extra dev dependencies required.

## Run remotely on a DevBox (self-hosted runner)

Testers can trigger tests on any registered DevBox from the browser — no RDP
needed for the run itself. **Every tester works on their own fork** and
registers runners against it.

**One-time laptop setup:** fork <https://github.com/william051200/UI-automation>,
then enable Actions: your fork → Settings → Actions → General → "Allow all
actions" → Save.

**One-time DevBox setup** (RDP in, admin PowerShell — replace `<your-handle>`):

```powershell
cd $HOME
git clone https://github.com/<your-handle>/UI-automation.git
cd $HOME\UI-automation
irm https://astral.sh/uv/install.ps1 | iex
$env:Path = "$HOME\.local\bin;$env:Path"
uv sync
.\scripts\setup-runner.ps1 -Label ZY-30072026-1 -TesterName "Zun Yang" -OpenPR   # <INITIALS>-<DDMMYYYY>-<N>
```

**Day-to-day (browser only):** Open your fork's Actions tab
(`https://github.com/<your-handle>/UI-automation/actions/workflows/run-ui-tests.yml`) →
**Run workflow** → pick a CSV + your DevBox label.

Full guide, including the label convention, per-run cleanup behaviour, and
troubleshooting: [`docs/REMOTE_RUNNING.md`](docs/REMOTE_RUNNING.md).

## Using with Copilot CLI

If you have [GitHub Copilot CLI](https://github.com/github/gh-copilot) (or any other agent that reads `AGENTS.md`) installed, you can drive the toolkit conversationally. The repo's [`AGENTS.md`](AGENTS.md) is auto-loaded and contains the rules the agent must follow when authoring or editing test cases. For the human-facing workflow and example prompts, see [`docs/authoring-scenarios.md`](docs/authoring-scenarios.md).

### Standard Copilot prompts

Replace the placeholder paths before submitting a prompt.

#### 1. Convert a rough test case

- `<SOURCE_FILE>`: rough CSV to convert
- `<OUTPUT_FILE>`: standard CSV to create
- Skill: `csv-test-formatter`
- Rules: `AGENTS.md` → `docs/csv-test-format.md` → `scripts/csvfmt/csv_schema.py` → `test_cases/_template.csv`

```text
Use the csv-test-formatter skill.

Source file: <SOURCE_FILE>
Output file: <OUTPUT_FILE>

Requirements:
1. Follow AGENTS.md, docs/csv-test-format.md, scripts/csvfmt/csv_schema.py, and test_cases/_template.csv in that precedence order.
2. Preserve the tester's intent.
3. Use only existing scripts and schema fields.
4. Keep values deterministic and paths machine-portable.
5. Populate sequential step numbers.
6. Validate the output with scripts/csvfmt/csv_loader.py.
```

**Example**

- `<SOURCE_FILE>` = `test_cases\drafts\notepad.csv`
- `<OUTPUT_FILE>` = `test_cases\notepad.csv`

#### 2. Run and automatically repair a test case

- `<TEST_CASE_FILE>`: standard CSV to run and repair
- `<REPORT_FILE>`: HTML repair report to create
- Skill: `test-case-repair`
- Command: `.\run.ps1 <TEST_CASE_FILE> -q`

```text
Use the test-case-repair skill.

Test case file: <TEST_CASE_FILE>
Report file: <REPORT_FILE>
Run command: .\run.ps1 <TEST_CASE_FILE> -q

Requirements:
1. Follow AGENTS.md and the CSV schema rules.
2. Diagnose each failed step.
3. Apply the smallest safe deterministic repair.
4. Validate the CSV after each repair.
5. Rerun until the test passes or is blocked.
6. Generate the report in the same format as test_cases\console_app_repair_report.html.
```

**Example**

- `<TEST_CASE_FILE>` = `test_cases\notepad.csv`
- `<REPORT_FILE>` = `test_cases\notepad_repair_report.html`

### Install the Copilot CLI

Don't have it yet? Run the bundled installer. It sets up **both** the standalone agentic `copilot` CLI and the `gh copilot` extension (whichever is missing), then walks you through login:

```powershell
.\install-copilot.ps1
```

Or one-line, straight from GitHub:

```powershell
irm https://raw.githubusercontent.com/william051200/UI-automation/main/install-copilot.ps1 | iex
```

Pass `-NoLogin` to install without the interactive sign-in prompts.

### Token-efficient Copilot usage

Driving the runner through Copilot CLI is convenient but costs LLM tokens per turn. To keep costs low without changing test behavior:

- **Skip the LLM entirely** for routine runs — invoke `.\run.ps1 <spec>` directly. This is the biggest saving (~0 LLM tokens).
- **Pass `-q`** when Copilot does run the scenario; this strips per-step echo from the output the model sees.
- **Scope the prompt** so Copilot doesn't speculatively read source files. Example: *"Run `.\run.ps1 ... -q`. Report only the exit code and any FAIL lines. Do not read `run_test.py` or the CSV spec."*
- **Batch follow-ups** into one prompt — each new turn replays the whole conversation, so 3 small turns cost ~3x one combined turn.

## Documentation

- [File structure](docs/file-structure.md) — what each file and folder in the repo is for.
- [CSV test-case format](docs/csv-test-format.md) — author/run test cases as `.csv`; spec layout, step types, placeholders, capture syntax. The `csv-test-formatter` skill tidies rough CSV into the standard layout.
- [Authoring scenarios with AI](docs/authoring-scenarios.md) — describe plain steps to an agent and get a runnable CSV.
- [Remote DevBox execution](docs/REMOTE_RUNNING.md) — register a DevBox as a self-hosted runner; trigger runs from the browser.
- [`AGENTS.md`](AGENTS.md) — auto-loaded instructions for AI coding agents working in this repo.
- [Reproducibility](docs/reproducibility.md) — how runs stay bit-identical.
- [Troubleshooting](docs/troubleshooting.md) — DPI, multi-monitor, UI language, legacy pip path.

## License

[MIT](LICENSE) © 2026 william051200
