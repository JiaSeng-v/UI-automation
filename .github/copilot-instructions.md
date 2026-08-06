# UI Automation Repository Instructions

## Project Purpose

This repository converts human-authored UI test scenarios into executable CSV automation test cases.

Testers provide:
- Plain English test steps
- Excel step lists
- Screenshots of test procedures
- Draft CSV files

Copilot is responsible for:
- Understanding user intent
- Mapping intent to existing scripts
- Generating canonical CSV format
- Validating against csv_schema.py
- Producing runnable test cases

## Source of Truth

When generating or modifying test cases, always follow:

1. AGENTS.md
2. docs/csv-test-format.md
3. scripts/csvfmt/csv_schema.py
4. test_cases/_template.csv

If conflicts exist:
- csv_schema.py takes precedence
- _template.csv must match csv_schema.py
- Documentation should follow the schema

## Test Case Generation Rules

- Never invent new CSV columns
- Never invent new script names
- Never invent new step types
- Reuse existing scripts whenever possible
- Preserve tester intent
- Keep outputs deterministic
- Do not randomize values

## Authoring Workflow

Tester Input
→ Copilot Conversion
→ Standard CSV
→ csv_loader validation
→ Execution via run.ps1

Testers describe intent.

Copilot generates implementation.

## Validation Requirements

Before finalizing a generated test case:

- Verify CSV structure matches csv_schema.py
- Verify referenced scripts exist
- Verify step numbers are sequential
- Verify required fields are populated
- Verify output can be executed by run.ps1

## UI Automation Guidance

Prefer environment discovery over hardcoded assumptions.

Do not assume:

- Visual Studio edition
- Window titles
- Project names
- Framework versions
- AutomationIds discovered from a single machine

Prefer:

- dynamic window discovery
- dynamic control discovery
- captured values
- reusable variables

Before keyboard-based actions always ensure the target application is foreground focused.

Examples:

- Ctrl+Shift+B
- Ctrl+F5
- Ctrl+Alt+L
- Ctrl+A
- Ctrl+C

Use scripts/window/activate_window.py when required.
