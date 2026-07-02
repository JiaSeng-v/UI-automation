import time
from pywinauto import Application
hwnd = 723798
app = Application(backend="uia").connect(handle=hwnd)
win = app.window(handle=hwnd)
# find the status TextCompartment once
comp = None
for c in win.descendants():
    try:
        if (c.element_info.automation_id or "") == "TextCompartment":
            comp = c; break
    except Exception:
        pass
print("found compartment:", comp is not None, flush=True)
last = None
for i in range(40):
    try:
        n = comp.element_info.name
    except Exception as e:
        n = f"<err {e}>"
    if n != last:
        print(f"{i:2d}s: {n!r}", flush=True)
        last = n
    time.sleep(1)
