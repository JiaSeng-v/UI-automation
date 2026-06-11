"""Launch a Chromium browser (Chrome or Edge) with a remote-debugging port.

Starts a normally-configured browser (no automation switches, so
``navigator.webdriver`` stays ``false``) with ``--remote-debugging-port`` and a
fixed ``--user-data-dir``, then polls the CDP endpoint until it answers. Prints
the launched process id on its own first line (for clean capture via
``$.cols[0]``) followed by ``port=<n>\\tpid=<n>\\tendpoint=<url>`` (tab-separated)
so a spec can capture the port for later DOM steps. ``--fresh`` wipes the profile
dir first for a clean browser (no cookies/login). Edge is Chromium, so the same
CDP helpers apply.

Exit codes:
  0  browser launched and the CDP endpoint is ready
  1  browser executable not found, or the endpoint never became ready
  3  bad usage / unexpected error
"""
import argparse
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp_client  # noqa: E402

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_BROWSER_CANDIDATES = {
    "chrome": [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ],
    "edge": [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ],
}

# Default profile dir per browser (gitignored), so Chrome and Edge don't clash.
_DEFAULT_PROFILE = {
    "chrome": os.path.join(_REPO_ROOT, ".browser-profile"),
    "edge": os.path.join(_REPO_ROOT, ".browser-profile-edge"),
}


def find_browser(browser, explicit=None):
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    for path in _BROWSER_CANDIDATES.get(browser, []):
        if path and os.path.isfile(path):
            return path
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url", nargs="?", default="about:blank",
                   help="initial URL to open (default about:blank)")
    p.add_argument("--browser", choices=["chrome", "edge"], default="chrome",
                   help="which Chromium browser to launch (default chrome)")
    p.add_argument("--port", type=int, default=9222,
                   help="remote-debugging port (default 9222)")
    p.add_argument("--user-data-dir", dest="user_data_dir", default=None,
                   help="profile dir (default .browser-profile[-edge] in repo root)")
    p.add_argument("--fresh", action="store_true",
                   help="delete the profile dir before launch for a clean browser")
    p.add_argument("--chrome", default=None, dest="exe",
                   help="explicit path to the browser executable")
    p.add_argument("--ready-timeout-ms", dest="ready_timeout_ms", type=int, default=15000)
    a = p.parse_args()

    exe = find_browser(a.browser, a.exe)
    if not exe:
        print(f"ERROR: {a.browser} executable not found; pass --chrome <path>",
              file=sys.stderr)
        sys.exit(1)

    profile = a.user_data_dir or _DEFAULT_PROFILE[a.browser]
    if a.fresh and os.path.isdir(profile):
        shutil.rmtree(profile, ignore_errors=True)
    os.makedirs(profile, exist_ok=True)

    cmd = [
        exe,
        f"--remote-debugging-port={a.port}",
        f"--user-data-dir={profile}",
        # Chromium M111+ rejects DevTools websocket connections with HTTP 403
        # unless the connecting origin is explicitly allowed.
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        # Suppress the fresh-profile sign-in/sync confirmation dialog
        # (edge://sync-confirmation-dialog) that otherwise overlays the page.
        "--disable-sync",
        "--disable-features=msImplicitSignin",
        a.url,
    ]
    try:
        proc = subprocess.Popen(cmd)
    except OSError as e:
        print(f"ERROR: failed to launch {a.browser}: {e}", file=sys.stderr); sys.exit(1)

    try:
        cdp_client.wait_ready(a.port, timeout_s=a.ready_timeout_ms / 1000.0)
    except cdp_client.CDPError as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(1)

    # Bare pid on its own first line for clean capture via $.cols[0],
    # followed by the human-readable port/pid/endpoint summary.
    print(proc.pid)
    print(f"port={a.port}\tpid={proc.pid}\tendpoint=http://127.0.0.1:{a.port}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(3)
