# ui-auto

Declarative UI-automation toolkit for Windows desktop apps. Drives mouse,
keyboard, screenshots, and UIA-based validation from simple YAML scenarios.

## Install — one PowerShell command

On a fresh Windows 10/11 machine, paste this into PowerShell:

```powershell
irm https://raw.githubusercontent.com/william051200/UI-automation/main/install.ps1 | iex
```

That's it. The script will:

1. Install **uv** (Astral) if missing — a single ~10 MB binary that manages
   Python and dependencies. No admin needed.
2. Install **git** via `winget` if missing.
3. Clone this repo to `%USERPROFILE%\UI-automation`.
4. Run `uv sync` — downloads Python 3.12 (managed by uv) and installs all
   pinned dependencies from `uv.lock`.
5. Print the command to run the example scenario.

> If your execution policy blocks the script, run:
> ```powershell
> powershell -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/william051200/UI-automation/main/install.ps1 | iex"
> ```

## Run a scenario

```powershell
cd $HOME\UI-automation
uv run python run_test.py test_cases\powershell_echo_loop.yaml
```

The example opens PowerShell via Start menu, echoes 4 fixed strings,
validates each via UIA, saves a screenshot per iteration, then closes the
window with a mouse-click on the UIA-located Close button.

Exit codes: `0` pass, `1` assertion failed, `2` runner error.

## Layout

```
ui-auto/
├── install.ps1                 # one-line bootstrap (fetched by the installer command)
├── setup.ps1                   # local convenience (assumes uv already installed)
├── pyproject.toml              # project metadata + dependencies (uv-managed)
├── .python-version             # pins Python 3.12
├── uv.lock                     # exact pinned versions for reproducibility
├── run_test.py                 # declarative test runner (consumes a YAML spec)
├── scripts/                    # generic CLI primitives — no scenario knowledge
│   ├── screenshot.py
│   ├── click.py
│   ├── type_text.py
│   ├── key.py
│   ├── find_window.py
│   ├── read_console.py
│   └── find_control.py
├── test_cases/                 # declarative YAML scenarios
│   └── powershell_echo_loop.yaml
├── requirements.txt            # (legacy pip path) loose declarations
├── requirements.lock.txt       # (legacy pip path) frozen pip versions
└── screenshots/<timestamp>/    # (generated) per-run artifacts
```

## Test-case spec format

A test case is a YAML file with these top-level keys:

| Key | Purpose |
|---|---|
| `name`, `description` | Human-readable identity. |
| `inputs` | Fixed values used by the scenario. **Do not randomize** — reproducibility requires identical inputs every run. |
| `artifacts` | Output paths; `{timestamp}` is substituted at run start (UTC). |
| `timing` | Named delay/poll constants (ms). Steps reference these by name (e.g. `wait_after: after_enter_ms`). |
| `steps` | Ordered list of actions. Each step has an `id`, `type`, and `description`. |
| `expected_results` | Human-readable pass criteria. |

### Step types

| `type` | Calls | Notes |
|---|---|---|
| `key`, `type_text`, `click`, `screenshot`, `find_window`, `find_control` | matching `scripts/*.py` | `expect_exit` defaults to 0. |
| `assert_console_contains` | `read_console.py` with polling | Asserts `expected_contains_expr` appears within `poll_total_ms`. |
| `foreach` | n/a | Iterates `items` (e.g. `inputs.echo_texts`), exposing `var` and `index_var` to nested `body` steps. |

### Placeholders

`{path.to.value}` resolves against `inputs`, `artifacts`, `vars` (captured
from earlier steps), and loop locals. Simple integer arithmetic works:
`{vars.win_left + 100}`.

### Capturing values from script output

```yaml
capture:
  vars.hwnd: "$.cols[1]"               # column 1 of the first output line
  vars.close_x: "$.rows[1].cols[7]"    # row 1, column 7 (skip header)
```

### Pass / fail screenshot variants

`screenshot` accepts `args_expr_on_pass` and `args_expr_on_fail`, so failed
iterations are saved under a different filename.

## Authoring a new scenario

1. Use **Inspect.exe** (Windows SDK) to discover UIA selectors.
2. Copy `test_cases/powershell_echo_loop.yaml`.
3. Replace `inputs`, `steps`, `expected_results`. Keep `inputs` literal.
4. Run the spec; iterate on `timing` if you see flaky waits.

## Reproducibility notes

- All inputs are pinned (no random generation at run time).
- Window/control targeting via UIA names/ids; mouse-click coordinates derive
  from UIA-reported rectangles.
- Console validation uses UIA text — independent of fonts, themes, OCR.
- `uv.lock` pins every transitive dependency with content hashes.

## Known machine-specific gotchas

- **Display scaling**: `run_test.py` sets per-monitor v2 DPI awareness.
- **Multi-monitor**: target UI must open on the primary monitor.
- **UI language**: on non-English Windows, swap `--name Close` for
  `--auto-id Close` (locale-invariant) in scenarios.
- **Focus stealers**: a popup that grabs focus mid-run will break typing.

## Legacy pip workflow

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe run_test.py test_cases\powershell_echo_loop.yaml
```
