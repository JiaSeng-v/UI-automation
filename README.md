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
uv run python run_test.py test_cases\powershell_echo_loop.yaml
```

The example opens PowerShell via Start menu, echoes 4 fixed strings,
validates each via UIA, saves a screenshot per iteration, then closes the
window with a mouse-click on the UIA-located Close button.

Exit codes: `0` pass, `1` assertion failed, `2` runner error.

## Layout

```
ui-auto/
├── install.ps1               # one-line bootstrap
├── setup.ps1                 # local convenience (uv already installed)
├── pyproject.toml            # uv-managed project metadata + deps
├── uv.lock                   # exact pinned versions
├── run_test.py               # declarative test runner
├── scripts/                  # generic CLI primitives
├── test_cases/               # declarative YAML scenarios
└── docs/                     # reference docs (see below)
```

## Documentation

- [Test-spec format](docs/test-spec-format.md) — YAML keys, step types, placeholders, capture syntax.
- [Authoring scenarios](docs/authoring-scenarios.md) — workflow with Inspect.exe.
- [Reproducibility](docs/reproducibility.md) — how runs stay bit-identical.
- [Troubleshooting](docs/troubleshooting.md) — DPI, multi-monitor, UI language, legacy pip path.

## License

[MIT](LICENSE) © 2026 william051200
