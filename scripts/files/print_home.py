"""Print the current user's home directory (profile) as the first stdout column.

Resolves ``~`` to the real profile path on this machine, which may live on any
drive (e.g. ``C:\\Users\\name`` or ``D:\\Users\\name``). A test captures it via
``$.cols[0]`` and uses ``{vars.home}`` to build absolute, machine-portable paths.
"""
import os, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main():
    print(os.path.expanduser("~"))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
