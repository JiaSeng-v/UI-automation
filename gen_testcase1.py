"""One-off generator: emit TestCase1.csv in the standard ui-auto layout."""
import csv, json, os

HEADER = ["No", "step no", "Main step", "Trigger", "script", "args", "wait_ms",
          "capture", "expect_exit", "expected_contains", "poll_total_ms",
          "poll_interval_ms", "screenshot_pass", "screenshot_fail", "max_iter",
          "Expected"]

ITEMGROUP = (
    "  <ItemGroup>\n"
    "    <PackageReference Include=\"NuGet.Commands\" Version=\"4.0.0\" />\n"
    "    <PackageReference Include=\"NuGet.Packaging\" Version=\"3.5.0\" />\n"
    "  </ItemGroup>\n"
)
WARNINGS = "  <WarningsAsErrors></WarningsAsErrors>\n"

_step = 0


def s():
    global _step
    _step += 1
    return _step


def row(no, main, trigger, script="", args=None, wait="", capture=None,
        expect_exit="", expected="", poll_total="", poll_interval="",
        ss_pass=None, ss_fail=None, max_iter="", note=""):
    return [
        no, s(), main, trigger, script,
        json.dumps(args) if args is not None else "",
        wait,
        json.dumps(capture) if capture is not None else "",
        expect_exit, expected, poll_total, poll_interval,
        json.dumps(ss_pass) if ss_pass is not None else "",
        json.dumps(ss_fail) if ss_fail is not None else "",
        max_iter, note,
    ]


def xy(prefix):
    return {f"vars.{prefix}_x": "$.rows[1].cols[7]",
            f"vars.{prefix}_y": "$.rows[1].cols[8]"}


rows = []
A = rows.append

# Phase 1 - Open Visual Studio (portable launch, no Start-menu / hardcoded path)
A(row("1", "Open Visual Studio",
      "Locate the installed Visual Studio devenv.exe.",
      "scripts/window/find_devenv.py",
      capture={"vars.devenv": "$.cols[0]"},
      note="Resolves devenv.exe via vswhere/registry/filesystem so the case runs "
           "on any machine/edition without a Start-menu search or literal path."))
A(row("1", "", "Launch Visual Studio and wait for its main window; stash hwnd in vars.vs_hwnd.",
      "scripts/window/launch.py",
      ["{vars.devenv}", "--wait-window", "^Microsoft Visual Studio( Insiders)?$",
       "--wait-timeout-ms", "60000", "--poll-ms", "500", "--backend", "uia"],
      capture={"vars.vs_hwnd": "$.cols[1]"},
      note="launch.py polls until the main window title matches; hwnd is column 1 "
           "of the pid/hwnd/left/top/right/bottom/title row."))
A(row("1", "", "Maximize the Visual Studio main window.",
      "scripts/window/maximize_window.py", ["{vars.vs_hwnd}"]))

# Phase 2 - Create a new project
A(row("2", "Create a new project",
      "Find 'Create a new project' button on the Start Window.",
      "scripts/uia/find_control.py",
      ["{vars.vs_hwnd}", "--name", "Create a new project", "--control-type",
       "Button", "--timeout-ms", "10000", "--poll-ms", "400"],
      capture=xy("create_proj")))
A(row("2", "", "Click 'Create a new project'.",
      "scripts/input/click.py", ["{vars.create_proj_x}", "{vars.create_proj_y}"], "3000"))

# Phase 3 - Select the Console App template
A(row("3", "Select Console App template",
      "Find the C# Console App template in the list.",
      "scripts/uia/find_control.py",
      ["{vars.vs_hwnd}", "--name", "Console App", "--control-type", "ListItem",
       "--match", "exact", "--nth", "1", "--timeout-ms", "10000", "--poll-ms", "400"],
      capture=xy("template"),
      note="LIVE-TUNE: with no language filter the first exact 'Console App' "
           "ListItem may be C#, F# or VB; add a search/language filter or bump "
           "--nth if the C# .NET template is not the first match."))
A(row("3", "", "Click the Console App template.",
      "scripts/input/click.py", ["{vars.template_x}", "{vars.template_y}"], "1000"))

# Phase 4 - Next (template page)
A(row("4", "Next (template page)", "Find the Next button (template page).",
      "scripts/uia/find_control.py",
      ["{vars.vs_hwnd}", "--name", "Next", "--control-type", "Button",
       "--timeout-ms", "10000", "--poll-ms", "400"],
      capture=xy("next1")))
A(row("4", "", "Click Next to go to project configuration.",
      "scripts/input/click.py", ["{vars.next1_x}", "{vars.next1_y}"], "3000"))

# Phase 5 - Next (configuration page)
A(row("5", "Next (configuration page)", "Find the Next button (configuration page).",
      "scripts/uia/find_control.py",
      ["{vars.vs_hwnd}", "--name", "Next", "--control-type", "Button",
       "--timeout-ms", "10000", "--poll-ms", "400"],
      capture=xy("next2")))
A(row("5", "", "Click Next to go to Additional Information.",
      "scripts/input/click.py", ["{vars.next2_x}", "{vars.next2_y}"], "3000"))

# Phase 6 - Select the last item in the Framework dropdown
A(row("6", "Select last framework", "Find the target-framework ComboBox.",
      "scripts/uia/find_control.py",
      ["{vars.vs_hwnd}", "--name", "Framework", "--control-type", "ComboBox",
       "--match", "contains", "--timeout-ms", "10000", "--poll-ms", "400"],
      capture=xy("framework"),
      note="LIVE-TUNE: framework ComboBox name/control-type varies by VS version."))
A(row("6", "", "Click the framework ComboBox to open the dropdown.",
      "scripts/input/click.py", ["{vars.framework_x}", "{vars.framework_y}"], "600"))
A(row("6", "", "Move to the last item in the open dropdown (End).",
      "scripts/input/key.py", ["end"], "300",
      note="LIVE-TUNE: 'Select the last item' mapped to End+Enter on the open "
           "combo; confirm End highlights the bottom framework entry."))
A(row("6", "", "Commit the last framework item (Enter).",
      "scripts/input/key.py", ["enter"], "600"))

# Phase 7 - Create the project
A(row("7", "Create project", "Find the Create button.",
      "scripts/uia/find_control.py",
      ["{vars.vs_hwnd}", "--name", "Create", "--control-type", "Button",
       "--timeout-ms", "10000", "--poll-ms", "400"],
      capture=xy("create")))
A(row("7", "", "Click Create to generate the project.",
      "scripts/input/click.py", ["{vars.create_x}", "{vars.create_y}"], "30000",
      note="Console App project is created and loads."))
A(row("7", "", "Re-locate the VS window after project creation.",
      "scripts/window/find_window.py", ["Microsoft Visual Studio", "--backend", "uia"],
      capture={"vars.vs_hwnd": "$.cols[1]"}))
A(row("7", "", "Maximize the VS window after creation.",
      "scripts/window/maximize_window.py", ["{vars.vs_hwnd}"]))
A(row("7", "", "Screenshot after project creation.",
      "scripts/files/screenshot.py", ss_pass=["{ss}_project_created.png"],
      note="Screenshot saved."))

# Phase 8 - Open the .csproj by double-clicking the project node
A(row("8", "Open .csproj", "Find the ConsoleApp project node in Solution Explorer.",
      "scripts/uia/find_control.py",
      ["{vars.vs_hwnd}", "--name", "ConsoleApp", "--control-type", "TreeItem",
       "--match", "contains", "--name-exclude", "Solution", "--timeout-ms",
       "10000", "--poll-ms", "400"],
      capture=xy("proj_node"),
      note="Project node name auto-increments (e.g. 'ConsoleApp1'); "
           "--name-exclude Solution drops the 'Solution ...' node."))
A(row("8", "", "Double-click the project node to open the .csproj editor.",
      "scripts/input/click.py",
      ["{vars.proj_node_x}", "{vars.proj_node_y}", "--double"], "2500",
      note="Double-clicking the project node opens the .csproj in the editor. "
           "The VS WPF editor is UIA-opaque, so edits below are keyboard/clipboard "
           "driven and validated via build status + screenshots."))
A(row("8", "", "Screenshot the opened .csproj.",
      "scripts/files/screenshot.py", ss_pass=["{ss}_csproj_opened.png"],
      note="Screenshot saved."))

# Phase 9 - Write the ItemGroup / PackageReference block at line 9
A(row("9", "Insert ItemGroup at line 9", "Open the Go To Line dialog (Ctrl+G).",
      "scripts/input/key.py", ["ctrl+g"], "600",
      note="LIVE-TUNE: Ctrl+G is 'Go To Line' in the C#/XML editor."))
A(row("9", "", "Type the target line number (9).",
      "scripts/input/type_text.py", ["9"], "200"))
A(row("9", "", "Jump to line 9 and close the dialog (Enter).",
      "scripts/input/key.py", ["enter"], "300"))
A(row("9", "", "Move the caret to the start of line 9 (Home).",
      "scripts/input/key.py", ["home"], "150"))
A(row("9", "", "Put the ItemGroup block on the clipboard.",
      "scripts/files/clipboard.py", ["write", ITEMGROUP], "200"))
A(row("9", "", "Paste the ItemGroup block into the .csproj (Ctrl+V).",
      "scripts/input/key.py", ["ctrl+v"], "500",
      note="LIVE-TUNE: paste inserts the block before the original line 9; "
           "VS smart-indent may reflow it - verify via the screenshot."))
A(row("9", "", "Screenshot the .csproj after inserting the ItemGroup.",
      "scripts/files/screenshot.py", ss_pass=["{ss}_itemgroup_added.png"],
      note="Screenshot saved."))

# Phase 10 - Save (Ctrl+S)
A(row("10", "Save", "Save the .csproj (Ctrl+S).",
      "scripts/input/key.py", ["ctrl+s"], "800", note="File saved."))

# Phase 11 - Build (Ctrl+Shift+B) - expected to succeed (NU1605 is a warning)
A(row("11", "Build", "Build the solution (Ctrl+Shift+B).",
      "scripts/input/key.py", ["ctrl+shift+b"], "1000",
      note="'Ctrl + Shirt + B' in the source is a typo for Ctrl+Shift+B (Build Solution)."))
A(row("11", "", "Validate the build succeeded via the VS status bar.",
      "scripts/uia/find_control.py",
      ["{vars.vs_hwnd}", "--name", "Build succeeded", "--control-type", "Text",
       "--match", "exact"],
      expected="Build succeeded", poll_total="60000", poll_interval="1000",
      note="NU1605 is only a warning at this point, so the build succeeds."))
A(row("11", "", "Screenshot after the first build.",
      "scripts/files/screenshot.py", ss_pass=["{ss}_build1_succeeded.png"],
      note="Screenshot saved."))

# Phase 12 - Write WarningsAsErrors at line 7
A(row("12", "Insert WarningsAsErrors at line 7", "Open the Go To Line dialog (Ctrl+G).",
      "scripts/input/key.py", ["ctrl+g"], "600"))
A(row("12", "", "Type the target line number (7).",
      "scripts/input/type_text.py", ["7"], "200"))
A(row("12", "", "Jump to line 7 and close the dialog (Enter).",
      "scripts/input/key.py", ["enter"], "300"))
A(row("12", "", "Move the caret to the start of line 7 (Home).",
      "scripts/input/key.py", ["home"], "150"))
A(row("12", "", "Put the WarningsAsErrors line on the clipboard.",
      "scripts/files/clipboard.py", ["write", WARNINGS], "200"))
A(row("12", "", "Paste the WarningsAsErrors line into the .csproj (Ctrl+V).",
      "scripts/input/key.py", ["ctrl+v"], "500",
      note="LIVE-TUNE: adds <WarningsAsErrors></WarningsAsErrors> so NU1605 "
           "is promoted to a build error."))
A(row("12", "", "Screenshot the .csproj after inserting WarningsAsErrors.",
      "scripts/files/screenshot.py", ss_pass=["{ss}_warningsaserrors_added.png"],
      note="Screenshot saved."))

# Phase 13 - Save (Ctrl+S)
A(row("13", "Save", "Save the .csproj (Ctrl+S).",
      "scripts/input/key.py", ["ctrl+s"], "800", note="File saved."))

# Phase 14 - Build (Ctrl+Shift+B) - expected to FAIL (NU1605 now an error)
A(row("14", "Build", "Build the solution (Ctrl+Shift+B).",
      "scripts/input/key.py", ["ctrl+shift+b"], "1000"))
A(row("14", "", "Validate the build failed via the VS status bar.",
      "scripts/uia/find_control.py",
      ["{vars.vs_hwnd}", "--name", "Build failed", "--control-type", "Text",
       "--match", "contains"],
      expected="Build failed", poll_total="60000", poll_interval="1000",
      note="LIVE-TUNE: with WarningsAsErrors set, NU1605 is now an error so the "
           "build fails; status-bar text may read 'Build failed' or "
           "'Build: 0 succeeded, 1 failed' - adjust the selector/expected text."))
A(row("14", "", "Screenshot after the failed build.",
      "scripts/files/screenshot.py", ss_pass=["{ss}_build2_failed.png"],
      note="Screenshot saved."))

# Phase 15 - Replace the ItemGroup to add NoWarn="NU1605" on the Packaging reference
A(row("15", "Add NoWarn NU1605", "Open Quick Replace (Ctrl+H).",
      "scripts/input/key.py", ["ctrl+h"], "600",
      note="LIVE-TUNE: Ctrl+H opens Find and Replace with focus in the Find field."))
A(row("15", "", "Type the text to find (the Packaging reference line).",
      "scripts/input/type_text.py",
      ["<PackageReference Include=\"NuGet.Packaging\" Version=\"3.5.0\" />"], "300"))
A(row("15", "", "Tab from the Find field to the Replace field.",
      "scripts/input/key.py", ["tab"], "300",
      note="LIVE-TUNE: number of Tabs to reach the Replace field can vary by VS "
           "version; confirm focus lands in the 'Replace' box."))
A(row("15", "", "Type the replacement text (adds NoWarn=\"NU1605\").",
      "scripts/input/type_text.py",
      ["<PackageReference Include=\"NuGet.Packaging\" Version=\"3.5.0\" NoWarn=\"NU1605\" />"], "300"))
A(row("15", "", "Replace all occurrences (Alt+A).",
      "scripts/input/key.py", ["alt+a"], "600",
      note="LIVE-TUNE: Alt+A is the 'Replace All' accelerator in VS Find/Replace."))
A(row("15", "", "Close the Find and Replace widget (Esc).",
      "scripts/input/key.py", ["esc"], "300"))
A(row("15", "", "Screenshot the .csproj after adding NoWarn.",
      "scripts/files/screenshot.py", ss_pass=["{ss}_nowarn_added.png"],
      note="Screenshot saved."))

# Phase 16 - Save (Ctrl+S)
A(row("16", "Save", "Save the .csproj (Ctrl+S).",
      "scripts/input/key.py", ["ctrl+s"], "800", note="File saved."))

# Phase 17 - Build (Ctrl+Shift+B) - expected to succeed again (NU1605 suppressed)
A(row("17", "Build", "Build the solution (Ctrl+Shift+B).",
      "scripts/input/key.py", ["ctrl+shift+b"], "1000"))
A(row("17", "", "Validate the build succeeded via the VS status bar.",
      "scripts/uia/find_control.py",
      ["{vars.vs_hwnd}", "--name", "Build succeeded", "--control-type", "Text",
       "--match", "exact"],
      expected="Build succeeded", poll_total="60000", poll_interval="1000",
      note="NoWarn=\"NU1605\" suppresses the error, so the build succeeds again."))
A(row("17", "", "Screenshot after the final build.",
      "scripts/files/screenshot.py", ss_pass=["{ss}_build3_succeeded.png"],
      note="Screenshot saved."))
A(row("17", "Close Visual Studio", "Close the Visual Studio window.",
      "scripts/window/close_window.py", ["{vars.vs_hwnd}", "--force"], "1500",
      note="Visual Studio closed."))

out = os.path.join("test_cases", "TestCase1.csv")
DESC = ("Launch Visual Studio; create a C# Console App (selecting the last "
        "target framework); open the .csproj editor and add a NuGet ItemGroup "
        "(NuGet.Commands 4.0.0 + NuGet.Packaging 3.5.0), save and build "
        "(succeeds); add <WarningsAsErrors></WarningsAsErrors>, save and build "
        "(NU1605 now fails the build); then add NoWarn=\"NU1605\" to the "
        "NuGet.Packaging reference, save and build (succeeds again). NOTE: the "
        "template pick, framework 'last item' selection, and all .csproj editor "
        "edits are keyboard/clipboard driven against the UIA-opaque VS editor and "
        "are flagged LIVE-TUNE where VS version / UI language may shift them.")

with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["# CONFIG"])
    w.writerow(["Section", "Key", "Value"])
    w.writerow(["name", "", "TestCase1"])
    w.writerow(["description", "", DESC])
    w.writerow(["artifacts", "screenshot_dir", "screenshots/{timestamp}"])
    w.writerow([])
    w.writerow(["# STEPS"])
    w.writerow(HEADER)
    for r in rows:
        w.writerow(r)

print(f"wrote {out} with {len(rows)} step rows")
