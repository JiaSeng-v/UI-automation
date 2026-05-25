"""Find UIA controls inside a window subtree by name / auto_id / control_type / class."""
import argparse, re, sys
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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("hwnd", type=lambda s: int(s, 0))
    p.add_argument("--name", default=None)
    p.add_argument("--auto-id", dest="auto_id", default=None)
    p.add_argument("--control-type", dest="control_type", default=None)
    p.add_argument("--class", dest="cls", default=None)
    p.add_argument("--match", choices=["exact", "contains", "regex"], default="exact")
    p.add_argument("--backend", choices=["uia", "win32"], default="uia")
    p.add_argument("--all", action="store_true", help="print all matches, not just first")
    a = p.parse_args()

    app = Application(backend=a.backend).connect(handle=a.hwnd)
    win = app.window(handle=a.hwnd)
    found = []
    for c in win.descendants():
        try:
            if a.backend == "uia":
                info = c.element_info
                name = info.name or ""
                auto_id = info.automation_id or ""
                ctype = info.control_type or ""
                cls = info.class_name or ""
            else:
                name = c.window_text() or ""
                auto_id = ""
                ctype = c.friendly_class_name() or ""
                cls = c.class_name() or ""
            if not (matches(name, a.name, a.match)
                    and matches(auto_id, a.auto_id, a.match)
                    and matches(ctype, a.control_type, a.match)
                    and matches(cls, a.cls, a.match)):
                continue
            r = c.rectangle()
            cx = (r.left + r.right) // 2
            cy = (r.top + r.bottom) // 2
            found.append((name, auto_id, ctype, r.left, r.top, r.right, r.bottom, cx, cy))
        except Exception:
            continue

    if not found:
        print("no match", file=sys.stderr); sys.exit(1)
    print("name\tauto_id\tcontrol_type\tleft\ttop\tright\tbottom\tcenter_x\tcenter_y")
    for f in (found if a.all else found[:1]):
        print("\t".join(str(x) for x in f))

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(2)
