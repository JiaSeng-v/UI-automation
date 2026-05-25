# Test-case spec format

A test case is a YAML file with these top-level keys:

| Key | Purpose |
|---|---|
| `name`, `description` | Human-readable identity. |
| `inputs` | Fixed values used by the scenario. **Do not randomize** — reproducibility requires identical inputs every run. |
| `artifacts` | Output paths; `{timestamp}` is substituted at run start (UTC). |
| `timing` | Named delay/poll constants (ms). Steps reference these by name (e.g. `wait_after: after_enter_ms`). |
| `steps` | Ordered list of actions. Each step has an `id`, `type`, and `description`. |
| `expected_results` | Human-readable pass criteria. |

## Step types

| `type` | Calls | Notes |
|---|---|---|
| `key`, `type_text`, `click`, `screenshot`, `find_window`, `find_control` | matching `scripts/*.py` | `expect_exit` defaults to 0. Set to a non-zero value to assert failure (e.g. `find_window` after closing a window). |
| `assert_file` | `assert_file_exists.py` | Asserts a file exists (or, with `--negate`, does not). Optional `--contains` checks a substring; `--delete` removes the file after the check. |
| `assert_console_contains` | `read_console.py` with polling | Asserts `expected_contains_expr` appears within `poll_total_ms`. |
| `foreach` | n/a | Iterates `items` (e.g. `inputs.echo_texts`), exposing `var` and `index_var` to nested `body` steps. |

## Placeholders

`{path.to.value}` resolves against `inputs`, `artifacts`, `vars` (captured
from earlier steps), and loop locals. Simple integer arithmetic works:

```yaml
args_expr: ["{vars.win_left + 100}", "{vars.win_top + 60}"]
```

## Capturing values from script output

```yaml
capture:
  vars.hwnd: "$.cols[1]"               # column 1 of the first output line
  vars.close_x: "$.rows[1].cols[7]"    # row 1, column 7 (skip header)
```

## Pass / fail screenshot variants

`screenshot` accepts `args_expr_on_pass` and `args_expr_on_fail`, so failed
iterations are saved under a different filename:

```yaml
- id: snapshot
  type: screenshot
  script: scripts/screenshot.py
  args_expr_on_pass: ["{artifacts.screenshot_dir}/iter_{n}.png"]
  args_expr_on_fail: ["{artifacts.screenshot_dir}/iter_{n}_FAIL.png"]
```

See [`test_cases/powershell_echo_loop.yaml`](../test_cases/powershell_echo_loop.yaml)
for a complete worked example.
