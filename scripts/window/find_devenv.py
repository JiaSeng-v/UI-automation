"""Locate the Visual Studio ``devenv.exe`` for the installed VS, edition-agnostic.

Uses ``vswhere`` (shipped with every VS installer at a fixed, documented path)
to find the latest installation and print its IDE executable. Prints the full
path to ``devenv.exe`` as the first stdout column so a test can capture it via
``$.cols[0]`` and use ``{vars.devenv}`` as a launch executable. Exit codes:
  0 OK   1 vswhere missing   2 no VS install found
"""
import argparse, os, subprocess, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _vswhere_path():
    base = os.environ.get("ProgramFiles(x86)") or r"C:\Program Files (x86)"
    return os.path.join(base, "Microsoft Visual Studio", "Installer", "vswhere.exe")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prerelease", action="store_true",
                   help="include prerelease (preview) installations")
    a = p.parse_args()

    vswhere = _vswhere_path()
    if not os.path.isfile(vswhere):
        print(f"ERROR: vswhere not found at {vswhere}", file=sys.stderr)
        sys.exit(1)

    cmd = [vswhere, "-latest", "-products", "*",
           "-requires", "Microsoft.VisualStudio.Component.CoreEditor",
           "-property", "productPath"]
    if a.prerelease:
        cmd.insert(1, "-prerelease")

    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    path = (r.stdout or "").strip().splitlines()
    path = path[0].strip() if path else ""

    if not path or not os.path.isfile(path):
        print(f"ERROR: no Visual Studio installation found (vswhere returned "
              f"{path!r})", file=sys.stderr)
        sys.exit(2)

    print(path)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
