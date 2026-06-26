# Test cases

Catalog of the declarative scenarios under [`test_cases/`](../test_cases), consumed by `run_test.py`. One CSV file per scenario; new scenarios drop in alongside the existing ones.

| Scenario | Purpose |
|---|---|
| `powershell_echo_loop` | Opens PowerShell from the Start menu, echoes four fixed strings (validating each via UIA), screenshots each iteration, then closes the window. |
| `vs_nuget` | Launches Visual Studio, creates a C# WinForms (.NET Framework) app plus a VB .NET Standard class library with a project reference, installs `EasyPost.NetStandard` via NuGet PM, loops updating vulnerable packages to latest stable, then builds and verifies `Build succeeded`. VS-version / UI-language dependent, so **not** bit-reproducible. |
