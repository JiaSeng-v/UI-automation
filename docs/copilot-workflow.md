# Copilot Authoring Workflow

## Purpose

This repository supports a Copilot-assisted UI automation authoring workflow.

Testers describe a UI test scenario in human-readable steps, and Copilot converts that intent into a standard executable CSV test case.

The tester is not expected to understand the internal CSV schema, script paths, JSON arguments, capture syntax, UIA selector strategy, or runner implementation details.

## Core idea

Tester describes intent.

Copilot generates implementation.

The CSV remains the executable source of truth.

## Standard workflow

```text
Tester input
  ↓
Plain English steps / Excel step list / screenshot-based procedure / rough CSV
  ↓
Copilot conversion
  ↓
Standard repository CSV format
  ↓
CSV validation against scripts/csvfmt/csv_schema.py
  ↓
Execution through .\run.ps1 <csv-file>
  ↓
Human-readable result review
```

## Environment Discovery

Testers provide business intent.

Copilot should avoid machine-specific assumptions.

Do not generate test cases that depend on:

- Visual Studio Community
- Visual Studio Enterprise
- Visual Studio Preview
- Visual Studio Insider

unless explicitly requested.

Prefer discovering:

- target windows
- controls
- project names
- framework values

during execution.

Captured values should be reused later for validation.

## Focus Management

UI automation must not assume keyboard focus.

Before keyboard shortcuts:

- Ctrl+Shift+B
- Ctrl+F5
- Ctrl+Alt+L
- Ctrl+A
- Ctrl+C

ensure the target application is active.

Recommended flow:

activate_window.py
→ keyboard action

This reduces failures caused by:

- Windows IME
- Language switchers
- Input Method Editors
- Focus stealing applications