"""Set a UIA CheckBox to a desired toggle state by name / auto_id / control_type.

Uses the UIA Toggle pattern (`.toggle()` / `.get_toggle_state()`) rather than a
coordinate click, so it reliably ticks check boxes whose clickable square is at
the edge of a wide row (e.g. the project rows in the Visual Studio Reference
Manager) where clicking the control's geometric centre lands on empty space or
the label and never toggles the box.

Selector model mirrors find_control.py: pass the parent window's hwnd plus any
combination of --name / --auto-id / --control-type / --class to locate the
descendant check box. Exit 0 on success (prints the final state), exit 1 if no
matching control is found, exit 2 on error.
"""
import argparse, re, sys, time
from pywinauto import Application

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def matches(value, target, mode):
    if target is None:
        return True
    if value is None:
        return False
    if mode == "exact":
        return value == target
    if mode == "contains":
        return target.lower() in value.lower()
    if mode == "regex":
        return re.search(target, value) is not None
    return False


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("hwnd", type=lambda s: int(s, 0),
                   help="parent window handle (decimal or 0x-hex)")
    p.add_argument("--name", default=None)
    p.add_argument("--auto-id", dest="auto_id", default=None)
    p.add_argument("--control-type", dest="control_type", default="CheckBox")
    p.add_argument("--class", dest="cls", default=None)
    p.add_argument("--match", choices=["exact", "contains", "regex"], default="exact")
    p.add_argument("--state", choices=["check", "uncheck", "toggle"], default="check",
                   help="desired result: check (default), uncheck, or flip once")
    a = p.parse_args()

    try:
        app = Application(backend="uia").connect(handle=a.hwnd)
        win = app.window(handle=a.hwnd)
    except Exception as e:
        print(f"ERROR: could not connect to hwnd {a.hwnd}: {e}", file=sys.stderr)
        sys.exit(2)

    target = None
    for c in win.descendants():
        try:
            info = c.element_info
            if (matches(info.name or "", a.name, a.match)
                    and matches(info.automation_id or "", a.auto_id, a.match)
                    and matches(info.control_type or "", a.control_type, a.match)
                    and matches(info.class_name or "", a.cls, a.match)):
                target = c
                break
        except Exception:
            continue

    if target is None:
        print("no match", file=sys.stderr)
        sys.exit(1)

    def state():
        try:
            return int(target.get_toggle_state())
        except Exception:
            return None

    want = {"check": 1, "uncheck": 0}.get(a.state)
    cur = state()

    if a.state == "toggle":
        target.toggle()
    elif cur is None:
        # Toggle pattern unreadable; click it once as a best effort.
        target.toggle()
    elif cur != want:
        target.toggle()

    # Confirm the desired state committed (UI may react asynchronously).
    final = cur
    for _ in range(10):
        final = state()
        if a.state == "toggle" or final is None or final == want:
            break
        time.sleep(0.1)

    print(f"toggle_state={final}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(2)
