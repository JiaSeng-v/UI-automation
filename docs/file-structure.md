# File structure

A guided tour of every file and folder in this repo, so you can find your way
around quickly.

## Top level

| Path | Purpose |
|---|---|
| `README.md` | Project overview, install command, example invocation, doc index. |
| `AGENTS.md` | Auto-loaded instructions for AI coding agents (Copilot CLI, Codex CLI, Cursor, Aider, Claude Code, …) working in this repo. Follows the [agents.md](https://agents.md/) convention. |
| `LICENSE` | MIT license. |
| `install.ps1` | One-line bootstrap installer for a fresh Windows machine (see [Entry points](#entry-points)). |
| `setup.ps1` | Local convenience wrapper that runs `uv sync` when `uv` is already installed. |
| `run.ps1` | Thin shortcut wrapper: `.\run.ps1 <spec> [-q]` → `uv run python run_test.py <spec> [-q]`. Lets you invoke a scenario without going through an LLM. |
| `run_test.py` | YAML test-spec runner (see [Entry points](#entry-points)). |
| `pyproject.toml` | Project metadata + direct dependencies (`pyautogui`, `pywinauto`, `Pillow`, `PyYAML`). Pins Python to `>=3.10,<3.13`. |
| `requirements.txt` | Human-edited top-level requirements list (mirrors `pyproject.toml` deps). |
| `requirements.lock.txt` | Fully resolved, pinned dependency list for `pip` users. |
| `uv.lock` | `uv`-generated lockfile pinning every transitive dependency with content hashes. |
| `.python-version` | Interpreter version pin used by `uv` to fetch the exact Python build. |
| `.gitignore` | Excludes `.venv/`, `screenshots/`, and other local artifacts from git. |
| `.venv/` | Local virtual environment created by `uv sync` (not committed). |
| `screenshots/` | Per-run screenshot artifacts written under `screenshots/{timestamp}/` (not committed). |
| `docs/` | Markdown documentation — see [docs/](#docs). |
| `scripts/` | Primitive Python helpers invoked by `run_test.py` — see [scripts/](#scripts). |
| `test_cases/` | Declarative YAML scenarios — see [test_cases/](#test_cases). |
| `tests/` | Stdlib `unittest` coverage for `scripts/author_test.py`. Run with `uv run python -m unittest discover -s tests -v`. |

## Entry points

### `install.ps1`
Zero-state bootstrap for a clean Windows 10/11 machine. In order it:

1. Installs `uv` from `astral.sh` if missing.
2. Installs `git` via `winget` if missing.
3. Clones (or `git pull`s) the repo into `%USERPROFILE%\UI-automation`.
4. Runs `uv sync` to fetch the pinned Python interpreter and all dependencies.
5. Prints the example command to run the bundled scenario.

Designed to be invoked via
`irm https://raw.githubusercontent.com/william051200/UI-automation/main/install.ps1 | iex`.

### `setup.ps1`
Lightweight alternative for developers who already have `uv` installed.
`cd`s to the repo, verifies `uv` is on `PATH`, runs `uv sync`, and prints the
example command. Use `install.ps1` instead on a fresh machine.

### `run.ps1`
Thin PowerShell wrapper around `uv run python run_test.py`. Takes the spec
path as its first argument and forwards any remaining flags (e.g. `-q`).
`Set-Location $PSScriptRoot` lets you call it from any working directory,
and it propagates the runner's exit code unchanged.

```powershell
.\run.ps1 test_cases\powershell_echo_loop.yaml
.\run.ps1 test_cases\powershell_echo_loop.yaml -q
```

### `run_test.py`
The test runner. Given a YAML spec, it:

- Parses `inputs`, `artifacts`, `timing`, and `steps` blocks
  (format documented in [`test-spec-format.md`](test-spec-format.md)).
- Enables per-monitor v2 DPI awareness so virtual-pixel clicks line up with
  physical-pixel UIA rectangles on HiDPI displays.
- Walks `steps` in order, dispatching each one by invoking the matching
  `scripts/*.py` as a subprocess (with `args` / `args_expr` substituted from
  captured variables and inputs).
- Captures stdout from helper scripts and stores fields in `vars.*` for later
  steps (see `capture:` clauses).
- Evaluates assertions (`assert_console_contains`, `expect_exit`, etc.) and
  polls where requested.
- Saves screenshots into `artifacts.screenshot_dir`.
- Exits **0** on full pass, **1** on a failed assertion, **2** on runner error
  (bad spec, missing script, etc.).

Pass `-q` / `--quiet` to suppress per-step headers and successful subcommand
stdout — useful when running under an LLM to keep token usage down. Failure
output, stderr, and the final `RESULT` line are always shown.

Usage: `uv run python run_test.py test_cases\<scenario>.yaml [-q]`.

## `scripts/`

Each script is a single-purpose CLI used as a primitive by `run_test.py`. They
can also be invoked directly from a shell for ad-hoc debugging.

### `click.py` — mouse click
Moves the mouse to `(x, y)` and clicks. Defaults to a single left click; flags
allow right-click and double-click.

```
click.py <x> <y> [--right] [--double]
```

### `type_text.py` — type a literal string
Types a text string into the currently focused window (UTF-8). `--interval`
controls per-character delay (default 0.02 s).

```
type_text.py <text> [--interval 0.02]
```

### `key.py` — press a key or hotkey
Presses a single named key (`enter`, `win`, `tab`, …) or a `+`-separated
hotkey combo (`ctrl+s`, `alt+f4`, `win+r`).

```
key.py <combo>
```

### `screenshot.py` — capture PNG
Saves a PNG of the full screen, or of a specified region. Creates the output
directory if needed.

```
screenshot.py <out_path> [--region X Y W H]
```

### `find_window.py` — locate a top-level window
Iterates all desktop windows (via `uia`, `win32`, or `any`, de-duplicating by
handle) and returns those whose title matches a regex (optionally filtered by
class name or owning process id via `--pid`). Results are sorted by `(pid, hwnd)`
so numbered candidate lists are reproducible. Prints tab-separated
`pid hwnd left top right bottom title`. Exits **1** if nothing matches — used
by specs to assert a window is *gone* (`expect_exit: 1`).

```
find_window.py <title_regex> [--class CLASS] [--pid PID] [--backend uia|win32|any]
                              [--all | --nth N]
```

### `find_control.py` — locate a UIA control inside a window
Walks the UIA descendant tree of a window (by `hwnd`) and matches controls by
`name`, `auto_id`, `control_type`, and/or `class`, using `exact` / `contains`
/ `regex` comparison. Prints a header row plus rectangle and computed center
coordinates, ready to feed into `click.py`. With `--name-fallback`, if the
`--auto-id` filter yields zero matches the scan retries without it (name /
type / class still apply) — used by the authoring tool to keep selectors
resilient when AutomationIds churn between app builds.

```
find_control.py <hwnd> [--name N] [--auto-id A] [--control-type T]
                       [--class C] [--match exact|contains|regex]
                       [--backend uia|win32] [--parent-hwnd HWND]
                       [--all | --nth N] [--name-fallback]
```

### `read_console.py` — dump a window's UIA text
Connects to a window by `hwnd` and prints its textual content. Prefers the
`Document` UIA control (where the PowerShell console exposes its buffer),
falling back to legacy properties, then to every visible text node. Used to
validate console output without OCR.

```
read_console.py <hwnd>
```

### `maximize_window.py` — maximize a window (skip if already maximized)
Maximizes a window by `hwnd`. Restores it first if minimised, then maximizes.
If the window is **already maximized** it is left unchanged and `already
maximized hwnd=<n> ...` is printed (still exit 0). Exits 1 if the hwnd does not
exist. Mirrors `activate_window.py`'s pywinauto/`--backend`/`--settle-ms` style.

```
maximize_window.py <hwnd> [--backend uia|win32] [--settle-ms 100]
```

### `assert_file_exists.py` — file existence / content assertions
Asserts a file exists (or, with `--negate`, does not), optionally checking
that it contains a given substring, and optionally deleting it afterwards
(`--delete`). Used by the YAML `assert_file` step type.

```
assert_file_exists.py <path> [--contains TEXT] [--negate] [--delete]
```

### `ui_fingerprint.py` — short hash of the current foreground UI
Prints a 16-char SHA-256 prefix derived from the foreground window's title,
class, process, optional rectangle, and up to 50 direct UIA children sorted
by screen position. `scripts/author_test.py`'s recurrence detector calls
this after each acting step (`click` / `key` / `type_text`) to spot a stuck
UI.

```
ui_fingerprint.py [--verbose] [--no-include-rect]
```

### `author_test.py` — interactive YAML authoring REPL
Builds a runnable YAML spec one compact step line at a time. Each step is
executed live against the real UI, so captured variables (window hwnds,
control coordinates) accumulate as you go. Includes two safety halts:
ambiguous `find_control` selectors and 3-in-a-row identical UI fingerprints.
See [`authoring-scenarios.md`](authoring-scenarios.md) for the workflow.

```
author_test.py <out_yaml>
```

### Web-page helpers (raw Chrome DevTools Protocol)
These drive a Chrome launched normally with only `--remote-debugging-port` (no
automation switches, so `navigator.webdriver` stays `false`), attaching over raw
CDP. Each helper reconnects to the long-running browser, since runner steps are
separate subprocesses. All take `--port` (default `9222`) and optional
`--url-contains` to select a page target.

#### `cdp_client.py` — shared CDP module (not a step)
Connection plumbing imported by the helpers below: `list_targets()`,
`select_page_target()`, `wait_ready()`, and a `CDPSession` websocket wrapper with
`send()`/`evaluate()`. Pure helpers are unit-tested in `tests/test_cdp_client.py`.

#### `browser_launch.py` — start Chrome/Edge with a debug port
Locates the browser (`--browser chrome|edge`), launches it with
`--remote-debugging-port` and a fixed `--user-data-dir` (default
`.browser-profile/` or `.browser-profile-edge/`, gitignored), and polls until the
CDP endpoint answers. `--fresh` wipes the profile dir first for a clean browser.
Launch flags suppress first-run, default-browser, and sign-in/sync prompts so
they don't overlay the page. Prints the launched **pid on its own first line**
(capture via `$.cols[0]`) followed by `port`/`pid`/`endpoint`.

```
browser_launch.py [url] [--browser chrome|edge] [--fresh] [--port 9222] [--user-data-dir DIR] [--chrome PATH]
```

#### `browser_goto.py` — navigate to a URL
`Page.navigate` to a URL, then waits for `document.readyState === 'complete'`.
Prints the final `url` and `title`.

```
browser_goto.py <url> [--port 9222] [--load-timeout-ms 15000]
```

#### `dom_get_html.py` — read page/element HTML
Writes the `outerHTML` (or `--text` `innerText`) of the document or `--selector`
to `--out`, printing `bytes`/`path`. Exit 1 if the selector matches nothing.

```
dom_get_html.py --out PATH [--selector CSS] [--text] [--port 9222]
```

#### `dom_interact.py` — click / type / press on an element
Performs `action` (click/type/set/press/select) on a CSS `--selector` using
trusted CDP `Input.dispatch*` events. Exit 1 if not found/interactable.

```
dom_interact.py <click|type|set|press|select> [--selector CSS] [--value V] [--port 9222]
```

#### `dom_query.py` — validate where to interact
Reports `count`/`visible`/`text`/bounding-box for a `--selector`. Assertion flags
`--expect-min`, `--visible`, `--contains` make it exit 1 on failure.

```
dom_query.py --selector CSS [--expect-min N] [--visible] [--contains TEXT] [--attr NAME] [--port 9222]
```

`--attr NAME` reads an attribute (e.g. `href`) of the first match and prints its
raw value as the **first** output line, so a spec can capture it cleanly with
`$.cols[0]`; the usual `count=...` line follows. `--attr innerText` works too
(non-attribute property names fall back to `el[NAME]`), giving a clean text capture.

#### `dom_eval.py` — evaluate a JS expression on the page
Evaluates `--expr` (a JavaScript expression) on the active CDP page and prints the
result as the **first** output line (capture via `$.cols[0]`); a `type=<js-type>`
line follows. Objects are printed as compact JSON; a `null`/`undefined` result
exits 1. Use it when the value isn't addressable as an element/attribute — e.g. a
field inside `window.__NEXT_DATA__`.

```
dom_eval.py --expr JS [--url-contains S] [--port 9222]
```

#### `write_text.py` — create / write a text file
Writes `--text` (default empty; `\n` becomes a newline) to `--out`, creating parent
dirs, and prints the file's **absolute path** as the first line (capture via
`$.cols[0]`), then `bytes=<n>`. `--append` appends instead of overwriting. Handy for
pre-creating an empty file so a GUI editor (e.g. Notepad) can open it *path-bound*
and save with Ctrl+S (no Save-As dialog to automate).

```
write_text.py --out PATH [--text STR] [--append]
```

## `docs/`

| File | Purpose |
|---|---|
| [`file-structure.md`](file-structure.md) | This document — layout of the repo. |
| [`test-spec-format.md`](test-spec-format.md) | Reference for YAML spec keys, step types, placeholder syntax, and `capture` rules. |
| [`authoring-scenarios.md`](authoring-scenarios.md) | Workflow for writing a new scenario, including using Inspect.exe to discover UIA selectors. |
| [`copilot-cli-test-authoring.md`](copilot-cli-test-authoring.md) | Human-facing workflow for authoring test cases via Copilot CLI / other AI agents. |
| [`reproducibility.md`](reproducibility.md) | Why runs stay bit-identical (pinned inputs, UIA targeting, locked deps). |
| [`troubleshooting.md`](troubleshooting.md) | DPI scaling, multi-monitor, UI-language, and legacy pip path issues. |

## `test_cases/`

Holds the declarative YAML scenarios consumed by `run_test.py`. One file per
scenario; new scenarios drop in here alongside the existing example.

| File | Purpose |
|---|---|
| `powershell_echo_loop.yaml` | Reference scenario: opens PowerShell from the Start menu, echoes four fixed strings, validates each via UIA, screenshots each iteration, then closes the window by clicking the UIA-located Close button. |
| `propertyguru_search_edge.yaml` | Web-automation sample: launches a fresh Microsoft Edge over CDP, loads PropertyGuru (MY), screenshots the home page, searches "Batu Kawan", screenshots the results, opens the first listing, and screenshots its detail page. Targets a live external site, so it is intentionally **not** bit-reproducible. |
