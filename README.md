# ui-auto

Declarative UI-automation toolkit for Windows desktop apps. Drives mouse,
keyboard, screenshots, and UIA-based validation from simple YAML scenarios.

## Install

One PowerShell command on a fresh Windows 10/11 machine:

```powershell
irm https://raw.githubusercontent.com/william051200/UI-automation/main/install.ps1 | iex
```

This installs `uv` + Python + `git` as needed, clones the repo to
`%USERPROFILE%\UI-automation`, and installs all pinned dependencies.

## Run the example

```powershell
cd $HOME\UI-automation
.\run.ps1 test_cases\powershell_echo_loop.yaml
```

(equivalent to `uv run python run_test.py test_cases\powershell_echo_loop.yaml`.)

The example opens PowerShell via Start menu, echoes 4 fixed strings,
validates each via UIA, saves a screenshot per iteration, then closes the
window with a mouse-click on the UIA-located Close button.

Exit codes: `0` pass, `1` assertion failed, `2` runner error.

Add `-q` (or `--quiet`) to suppress per-step echo and successful subcommand
stdout; failures, stderr, and the final RESULT line are always shown.

## Using with Copilot CLI

If you have [GitHub Copilot CLI](https://github.com/github/gh-copilot)
installed, you can drive the toolkit conversationally. Two example prompts:

**Run an existing scenario:**
> Run `.\run.ps1 test_cases\powershell_echo_loop.yaml -q`, then summarize
> pass/fail per iteration and list the screenshot paths.

**Author a new scenario:**
> Create a new test case at `test_cases/notepad_save.yaml` that opens Notepad
> from the Start menu, types `hello from copilot`, saves the file as
> `%TEMP%\copilot_test.txt` via Ctrl+S, validates the file exists, and closes
> Notepad with a mouse click on the Close button. Use UIA selectors and
> follow the spec format in `docs/test-spec-format.md`.

### Token-efficient Copilot usage

Driving the runner through Copilot CLI is convenient but costs LLM tokens
per turn. To keep costs low without changing test behavior:

- **Skip the LLM entirely** for routine runs — invoke `.\run.ps1 <spec>`
  directly. This is the biggest saving (~0 LLM tokens).
- **Pass `-q`** when Copilot does run the scenario; this strips per-step
  echo from the output the model sees.
- **Scope the prompt** so Copilot doesn't speculatively read source files.
  Example: *"Run `.\run.ps1 ... -q`. Report only the exit code and any FAIL
  lines. Do not read `run_test.py` or the YAML."*
- **Batch follow-ups** into one prompt — each new turn replays the whole
  conversation, so 3 small turns cost ~3x one combined turn.

## Documentation

- [File structure](docs/file-structure.md) — what each file and folder in the repo is for.
- [Test-spec format](docs/test-spec-format.md) — YAML keys, step types, placeholders, capture syntax.
- [Authoring scenarios](docs/authoring-scenarios.md) — workflow with Inspect.exe.
- [Reproducibility](docs/reproducibility.md) — how runs stay bit-identical.
- [Troubleshooting](docs/troubleshooting.md) — DPI, multi-monitor, UI language, legacy pip path.

## License

[MIT](LICENSE) © 2026 william051200
