"""Put one of three .csproj document states onto the clipboard for the NU1605 scenario.

Used by test_cases/vs_nu1605_build.csv. The whole project file is retyped (via
Ctrl+A / Ctrl+V) at each stage because the VS WPF editor text is not UIA-readable,
so line-number edits are too brittle. Keeping the XML here (rather than inline in the
CSV) avoids nested JSON/CSV quote escaping.

States (matching the decoded TestCase1.xlsx flow):
  1  add the ItemGroup with the conflicting NuGet.* PackageReferences
     (NuGet.Commands 4.0.0 depends on NuGet.Packaging >= 4.x, but 3.5.0 is pinned
      -> NU1605 package-downgrade warning). Build succeeds.
  2  state 1 + <WarningsAsErrors>NU1605</WarningsAsErrors> so NU1605 becomes an
     error. Build fails. (TestCase1 wrote an empty <WarningsAsErrors></WarningsAsErrors>;
     an empty value suppresses nothing and would not fail the build, so NU1605 is set
     explicitly to satisfy the confirmed 'build 2 fails' outcome.)
  3  state 2 + NoWarn="NU1605" on the NuGet.Packaging reference so the warning is
     suppressed and is therefore no longer promoted to an error. Build succeeds.

Exit 0 on success (prints the number of chars written), exit 1 on error.
"""
import argparse, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "files"))
import clipboard  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def build_doc(state: int, framework: str) -> str:
    warnings_line = "    <WarningsAsErrors>NU1605</WarningsAsErrors>\n" if state >= 2 else ""
    nowarn_attr = ' NoWarn="NU1605"' if state >= 3 else ""
    return (
        '<Project Sdk="Microsoft.NET.Sdk">\n'
        "\n"
        "  <PropertyGroup>\n"
        "    <OutputType>Exe</OutputType>\n"
        f"    <TargetFramework>{framework}</TargetFramework>\n"
        "    <ImplicitUsings>enable</ImplicitUsings>\n"
        "    <Nullable>enable</Nullable>\n"
        f"{warnings_line}"
        "  </PropertyGroup>\n"
        "\n"
        "  <ItemGroup>\n"
        '    <PackageReference Include="NuGet.Commands" Version="4.0.0" />\n'
        f'    <PackageReference Include="NuGet.Packaging" Version="3.5.0"{nowarn_attr} />\n'
        "  </ItemGroup>\n"
        "\n"
        "</Project>\n"
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", type=int, required=True, choices=[1, 2, 3])
    p.add_argument("--framework", default="net8.0",
                   help="target framework moniker, e.g. net8.0 / net10.0")
    a = p.parse_args()
    doc = build_doc(a.state, a.framework)
    clipboard.write_clipboard(doc)
    print(f"state {a.state} csproj ({a.framework}) -> clipboard, {len(doc)} chars")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(1)
