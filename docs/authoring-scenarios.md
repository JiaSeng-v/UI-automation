# Authoring a new scenario

1. Use **Inspect.exe** (ships with the Windows SDK, typically at
   `C:\Program Files (x86)\Windows Kits\10\bin\<version>\x64\Inspect.exe`) to
   discover UIA selectors for the controls you'll target:
   - window title
   - button `Name` / `AutomationId` / `ControlType`
   - any other property you'll match against
2. Copy [`test_cases/powershell_echo_loop.yaml`](../test_cases/powershell_echo_loop.yaml)
   as a starting point.
3. Replace `inputs`, `steps`, and `expected_results`. Keep `inputs` literal —
   no randomness — so reruns are bit-for-bit reproducible.
4. Run the spec:
   ```powershell
   uv run python run_test.py test_cases\my_scenario.yaml
   ```
5. Iterate on the `timing:` constants if you see flaky waits.

See [test-spec-format.md](test-spec-format.md) for the full YAML reference.
