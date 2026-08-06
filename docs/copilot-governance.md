# Copilot Governance

This document defines ownership boundaries for AI customization files in this repository.

The goal is to avoid duplicated rules, conflicting instructions, and inconsistent Copilot output.

## Core Principle

This repository uses AI to help convert human-authored UI test scenarios into executable CSV automation test cases.

Testers describe test intent.

Copilot generates the implementation CSV.

The CSV schema remains the executable contract.

## Ownership Model

### AGENTS.md

Purpose:

- Repository-wide mandatory rules.
- Runtime assumptions.
- CSV contract constraints.
- Script usage constraints.
- Reproducibility requirements.
- General rules for AI coding agents working in this repository.

Should contain:

- What this repo is.
- Authoritative references.
- Hard rules for authoring or editing test cases.
- Failure iteration rules.
- Running test commands.
- Environment assumptions.
- Markdown style rules.

Should not contain:

- Long user tutorials.
- Full CSV specification.
- Full script reference.
- Prompt file content.
- Detailed tester authoring workflow.

## .github/copilot-instructions.md

Purpose:

- Copilot-specific guidance.
- Tell Copilot how to navigate this repository.
- Explain the standard authoring workflow.
- Point Copilot to the correct source-of-truth files.

Should contain:

- Project purpose.
- Tester input model.
- Copilot responsibility.
- Source-of-truth order.
- Test case generation rules.
- Validation expectations.

Should not contain:

- Full CSV specification.
- Full script documentation.
- Duplicate AGENTS.md content.
- Duplicate SKILL.md procedure.
- Long examples.

## .github/skills

Purpose:

- Reusable task procedures.
- Step-by-step workflow for a specific AI task.
- Example: convert rough tester steps into standard CSV.
- Example: repair a failing CSV test case.
- Example: validate a generated test case.

Should contain:

- When to use the skill.
- Required inputs.
- Required outputs.
- Step-by-step procedure.
- Validation procedure.
- Relevant references.

Should not contain:

- Repository-wide policy.
- Full duplicate CSV schema.
- Rules already owned by AGENTS.md.
- Rules already owned by csv_schema.py.
- Many unrelated workflows in one skill.

## .github/prompts

Purpose:

- Standard entry points for team members.
- Reusable Copilot prompts.
- Thin wrappers that invoke repository docs, skills, and validation steps.

Examples:

- generate-ui-test-case.prompt.md
- repair-ui-test-case.prompt.md
- validate-ui-test-case.prompt.md
- summarize-ui-test-result.prompt.md

Should contain:

- User-facing task description.
- Required input format.
- Expected output format.
- Which docs or skills to follow.
- Validation command to run.

Should not contain:

- Full implementation details.
- Full CSV schema.
- Full script reference.
- Duplicated skill procedure.

Prompts should call or reference skills and docs instead of becoming another source of truth.

## docs

Purpose:

- Human-readable documentation.
- Explanation, rationale, examples, troubleshooting.
- Help testers and contributors understand how to use the repository.

Should contain:

- CSV format explanation.
- Copilot authoring workflow.
- Script reference.
- Troubleshooting guidance.
- Reproducibility guidance.
- Remote running guidance.
- File structure explanation.

Should not contain:

- Hidden mandatory rules that exist nowhere else.
- CSV definitions that disagree with csv_schema.py.
- Examples that disagree with test_cases/_template.csv.

If documentation conflicts with the executable schema, the schema wins.

## scripts/csvfmt/csv_schema.py

Purpose:

- Executable CSV contract.
- Defines CSV markers and column layout.
- Defines the schema that the loader and runner expect.

This is the highest authority for CSV columns.

If docs, skills, prompts, AGENTS.md, or examples conflict with this file, this file wins.

Should contain:

- Section marker constants.
- Step column list.
- Config column list.
- CSV parsing helper behavior.

Should not contain:

- Tester-facing workflow guidance.
- Copilot prompt instructions.
- Long documentation prose.

## test_cases/_template.csv

Purpose:

- Canonical starter CSV template.
- Practical example of the schema expected by the runner.
- Reference layout for generated CSV files.

If documentation examples conflict with this template, update the documentation examples.

Should contain:

- # CONFIG section.
- # STEPS section.
- Canonical headers matching csv_schema.py.
- Minimal runnable example rows.

Should not contain:

- Experimental columns.
- Product-specific scenario logic.
- Long explanation.

## Source of Truth Order

When files disagree, use this order:

1. scripts/csvfmt/csv_schema.py
2. test_cases/_template.csv
3. AGENTS.md
4. docs/csv-test-format.md
5. .github/copilot-instructions.md
6. .github/skills/*/SKILL.md
7. .github/prompts/*.prompt.md
8. README.md and other explanatory docs

## CSV Contract Rule

The CSV contract must not be redefined in many places.

The executable schema lives in:

- scripts/csvfmt/csv_schema.py

The canonical example lives in:

- test_cases/_template.csv

Other files may explain or reference the CSV contract, but must not define a different schema.

## Copilot Authoring Rule

The standard AI-assisted authoring flow is:

Tester input

↓  
Plain English steps, Excel step list, screenshots, manual procedure, or draft CSV.

Copilot conversion

↓  
Copilot maps tester intent to existing scripts and generates canonical CSV.

CSV validation

↓  
Generated CSV is checked against scripts/csvfmt/csv_schema.py and parsed by csv_loader.py.

Execution

↓  
Runnable CSV is executed through run.ps1 when the target environment is available.

Review

↓  
Copilot summarizes generated files, validation result, execution result, screenshots, assumptions, and remaining manual review items.

## Tester Responsibility

Testers should provide:

- Application under test.
- Numbered manual steps.
- Expected result for important validations.
- Values that should be remembered and reused later.
- Screenshot requirements.
- Known environment assumptions.

Testers should not need to provide:

- CSV column names.
- Script paths.
- JSON args.
- Capture syntax.
- UIA selector strategy.
- Runner implementation details.

## Copilot Responsibility

Copilot should:

- Read repository rules before generating or editing test cases.
- Follow csv_schema.py and _template.csv.
- Preserve tester intent.
- Reuse existing scripts.
- Generate deterministic CSV.
- Keep step numbers sequential.
- Avoid hardcoded user-specific paths.
- Validate generated CSV before final response.
- Report assumptions and review-needed items clearly.

Copilot must not:

- Invent new CSV columns.
- Invent new step types.
- Invent script paths.
- Randomize values.
- Hardcode user profile paths.
- Change schema without explicit instruction.
- Rewrite unrelated files.
- Treat parse validation and live UI execution as the same thing.

## Change Governance

Changing CSV schema requires updating:

- scripts/csvfmt/csv_schema.py
- test_cases/_template.csv
- docs/csv-test-format.md
- Related skill documentation
- Related tests
- Existing scenario compatibility plan

Changing AI workflow requires updating:

- docs/copilot-workflow.md
- .github/copilot-instructions.md
- Related skills or prompts

Changing a skill requires checking:

- Whether the behavior duplicates AGENTS.md.
- Whether the behavior duplicates docs.
- Whether the behavior conflicts with csv_schema.py.
- Whether the skill still serves one clear workflow.

## Review Checklist

Before accepting AI-generated changes, verify:

- CSV follows canonical schema.
- CSV headers match csv_schema.py.
- Generated CSV matches _template.csv layout.
- Every real step has a valid script path.
- JSON cells are valid.
- Step numbers are sequential.
- Required validation points are represented.
- Screenshot requirements are represented.
- No user-specific hardcoded paths are added.
- No unrelated files are modified.
- Parse validation passes.
- Live execution result is clearly marked as passed, failed, or not run.

## Design Principle

Keep the runner boring.

Keep scripts small.

Keep CSV deterministic.

Keep tester input simple.

Let Copilot handle conversion.

Let validation enforce correctness.

## Automation Reliability Rules

Generated test cases should prefer:

- discovery
- capture
- validation

over hardcoded values.

Avoid:

- exact Visual Studio edition names
- exact project names
- exact framework versions
- machine-specific AutomationIds
- machine-specific window titles

Discovery-based automation is preferred.