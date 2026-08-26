---
name: csv-test-formatter
description: Convert a rough, hand-authored CSV or Markdown test case into the standard ui-auto CSV layout that runs directly via run.ps1. Use when the user has a messy or freeform CSV or Markdown file describing a UI-automation scenario and wants a runnable standard-format CSV.
---

# CSV test formatter

Convert one rough CSV or Markdown file into one canonical CSV. This skill does not run the UI test.

Follow `AGENTS.md` for authoring behavior. Use `scripts/csvfmt/csv_schema.py` for the exact columns, `test_cases/_template.csv` for the starter layout, and `docs/csv-test-format.md` for syntax details.

## Input and output

- Default input: `test_cases\drafts\<name>.csv` or `test_cases\drafts\<name>.md`.
- Default output: `test_cases\<name>.csv`, using the same base filename regardless of the input extension.
- An explicit user-provided output path overrides the default.
- If the user provides one unambiguous draft path, infer the output path automatically. Ask only when the source or destination is ambiguous.

## Markdown input

Recognize rough Markdown test cases with this structure:

- The first level-1 heading is the test-case name.
- A `Prerequisites` section describes setup requirements and constraints; preserve it in the test description or implement it with existing setup/assertion scripts when executable.
- A `Test steps` section contains the scenario. Ordered-list nesting groups phases and substeps but does not change their order.
- Sentences beginning with actions such as **Create**, **Open**, **Click**, **Select**, **Change**, **Add**, **Save**, **Return**, **Right-click**, **Update**, or **Remove** are executable actions.
- Sentences beginning with **Verify** are assertions and must become executable checks when an existing script supports them.
- A fenced code block belongs to the immediately preceding action or verification. Preserve its contents exactly, including XML, source code, commands, paths, names, and versions.
- A `replacing` / `with` pair of fenced blocks describes one edit: replace the first literal block with the second.
- Markdown formatting such as bold text and inline code conveys literal UI labels, names, values, or paths; remove the formatting markers without changing the content.

## Workflow

1. Resolve the source and output paths using the convention above.
2. Read the rough CSV or interpret the Markdown using the rules above. Preserve its prerequisites, actions, expected results, literal values, code blocks, screenshots, hierarchy, and repetition.
3. Read `scripts/csvfmt/csv_schema.py`, `test_cases/_template.csv`, `docs/csv-test-format.md`, and the relevant scripts under `scripts\`. Do not search for or read existing converted test cases unless the user explicitly names one as a reference.
4. Map every action to an existing script. Ask instead of inventing a script or schema capability.
5. Write `# CONFIG` with `name`, `description`, and `artifacts` → `screenshot_dir`.
6. Write `# STEPS` using the exact `STEPS_COLUMNS` order from `csv_schema.py`.
7. Populate a global sequential `step no` for every executable row, including `# LOOP` conditions and loop bodies.
8. JSON-encode `args`, `capture`, `screenshot_pass`, and `screenshot_fail`.
9. Unroll known-count repetition. Use `# LOOP` / `# END LOOP` with `max_iter` only when the count is unknown.
10. Write the output CSV.
11. Validate it:

```powershell
uv run python scripts\csvfmt\csv_loader.py test_cases\<name>.csv
```

12. Fix every validation error before finishing.

## Output rule

When returning CSV in chat, output one complete CSV block without surrounding explanation unless the user asks for it.
