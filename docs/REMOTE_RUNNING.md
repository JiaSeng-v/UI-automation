# Remote UI Test Execution — DevBox Runner Guide

Run the CSV-driven UI tests on a Microsoft DevBox by clicking a button in
your laptop browser. No RDP needed during the run itself.

> **Legend:** **🖥️ DEVBOX** = the RDP'd Windows machine · **💻 LAPTOP** = your local browser

---

## Architecture at a glance

```
   💻 LAPTOP browser              GitHub                   🖥️ DEVBOX
  ┌────────────────┐         ┌─────────────┐         ┌────────────────────┐
  │ Click          │         │ Actions     │         │ Self-hosted runner │
  │ "Run workflow" │ ──────► │ dispatcher  │ ──job──►│  → uv sync         │
  └────────────────┘         └─────────────┘         │  → run.ps1 <csv>   │
                                   ▲                 │  → screenshots     │
                                   │ artifacts       └────────────────────┘
       artifacts download ─────────┘
```

**How it stays scalable:** each DevBox registers as a distinct runner with
a unique label (e.g. `ZY-24072026-1`). The workflow's `target_devbox` input
picks which label to run on. Adding testers = registering more DevBoxes +
adding one line to the workflow's choice list.

---

## Part A — Register your DevBox as a runner (one-time)

Run these steps ONCE on your DevBox. After this, day-to-day usage is entirely
browser-driven from your laptop.

### Step 1 — 🖥️ DEVBOX: RDP in and open an admin PowerShell

`Win + X` → **Windows PowerShell (Admin)** → `Yes` to the UAC prompt.

> ⚠️ Do NOT `cd C:\Windows\System32`. Work from `$HOME`.
> ```powershell
> cd $HOME
> ```

### Step 2 — 🖥️ DEVBOX: Install the toolchain and clone the repo

The `install.ps1` script handles uv + git + repo clone in one shot:

```powershell
irm https://raw.githubusercontent.com/william051200/UI-automation/main/install.ps1 | iex
```

That leaves the repo at `$HOME\UI-automation`. **You must `cd` into it before
running the next step** — the setup script lives in the repo:

```powershell
cd $HOME\UI-automation
```

### Step 3 — 🖥️ DEVBOX: Get a runner registration token from GitHub

In your **laptop** browser, open:

```
https://github.com/william051200/UI-automation/settings/actions/runners/new?arch=x64&os=win
```

Copy the token value that appears next to `./config.cmd --token ...`. Tokens
expire in one hour — grab it right before the next step.

### Step 4 — 🖥️ DEVBOX: Register the runner

Pick your label using the convention:

```
<INITIALS>-<DDMMYYYY>-<N>
```

- `<INITIALS>` — your initials (e.g. `ZY`, `WN`, `YH`, `HS`)
- `<DDMMYYYY>` — the date you're provisioning the DevBox
- `<N>` — 1 for your first DevBox, 2 for your second, etc.

Then run (in the same admin PowerShell):

```powershell
# Edit locally; print the git commands to publish it yourself
.\scripts\setup-runner.ps1 -Label ZY-24072026-1 -TesterName "Zun Yang"

# Or: let the script push and open the PR for you (needs `gh auth login`)
.\scripts\setup-runner.ps1 -Label ZY-24072026-1 -TesterName "Zun Yang" -OpenPR
```

Paste the token when prompted. The script will:

1. Verify uv / git / python.
2. Download the latest GitHub Actions runner.
3. Register it against the repo with your label.
4. Install it as a **Windows service** so it survives reboots.
5. **Add your label to `.github/workflows/run-ui-tests.yml`** under
   `target_devbox.options` (with your name as a YAML comment).
6. If `-OpenPR` was passed, commit + push + open the PR via `gh`.
   Otherwise, print the exact `git`/`gh` commands to run yourself.

When it finishes, verify at
<https://github.com/william051200/UI-automation/settings/actions/runners> that
your runner shows status **Idle**, and merge the PR so your label appears
in the workflow dropdown for everyone.

### Step 5 — 🖥️ DEVBOX: Log in and leave unlocked

UI automation needs an interactive, unlocked desktop.

- **Do NOT** log the DevBox off — you can disconnect RDP, but leave it logged in.
- **Do NOT** lock the screen — Windows will suspend UI input.
- Ideally: RDP once, leave the session open, close the RDP client. The DevBox
  stays running with the desktop live.

> You told us screens are kept open at all times, so this should be a non-issue.
> No keep-alive script is needed.

**One-time setup is done.** From here on, you never need to RDP just to run
a test.

---

## Part B — Running tests (day-to-day, browser-only)

Anyone with `Actions: write` on the repo can trigger any registered DevBox.

### Step 1 — 💻 LAPTOP: Open the workflow page

<https://github.com/william051200/UI-automation/actions/workflows/run-ui-tests.yml>

Click **Run workflow** (top-right).

### Step 2 — 💻 LAPTOP: Fill in the inputs

| Input | Meaning | Example |
|---|---|---|
| `csv_spec` | Pick one CSV, or `ALL` to run every case sequentially | `test_cases/powershell_echo_loop.csv` |
| `target_devbox` | Which DevBox label to run on | `ZY-24072026-1` |
| `quiet` | Pass `-q` to `run.ps1` | `true` (recommended) |

Click **Run workflow**.

### Step 3 — 💻 LAPTOP: Watch and collect

- **Live logs** — click the running job to stream stdout.
- **Screenshots** — after the run, scroll to the bottom of the summary page;
  the `screenshots-<label>-<n>` artifact contains every screenshot the CSV
  captured.
- **Exit codes** — `0` = pass, `1` = assertion fail, `2` = runner error.

---

## What happens automatically on every run

Each workflow run performs these steps on the DevBox:

1. **`uv sync --frozen`** — reproducible dep install from `uv.lock`.
2. **`run.ps1 <spec> [-q]`** — for each spec, sequentially.
3. **Screenshot upload** — always, even on failure.

> **DevBox hygiene:** testers refresh their DevBox between runs, so the
> workflow does **not** perform pre/post cleanup today. A cleanup script
> (`scripts/finalize-run.ps1`) is checked in and the workflow has commented
> pre/post steps ready to enable if we ever move to shared or long-lived
> DevBoxes.

---

## Adding another DevBox for yourself

Same steps as Part A, using label `XX-DDMMYYYY-N` where `N` is one higher
than any DevBox you already own. Each label is unique per DevBox; **never**
reuse a label across two machines — GitHub will re-register and the previous
DevBox will silently stop receiving jobs.

---

## Common issues

| Symptom | Cause / Fix |
|---|---|
| Workflow queued forever | No runner is online with the chosen label. RDP the DevBox and check the `actions.runner.*` Windows service is running. |
| `The system cannot find the file specified` at UIA step | The DevBox is locked or logged off. Unlock and re-run. |
| Screenshots artifact missing | The CSV didn't write any screenshots (some don't) — not an error. |
| `uv sync` fails with `python not found` | First run on a fresh DevBox — `uv` will fetch Python. Re-trigger the workflow. |
| Runner appears twice in Settings → Runners | You re-registered without unregistering. From the DevBox: `cd C:\actions-runner; .\config.cmd remove --token <new-token>` then re-run `setup-runner.ps1`. |
| Two workflows fought over the same DevBox | The workflow uses a `concurrency` group per label, so this shouldn't happen. If you see interleaved logs, file a bug. |

---

## Uninstalling a runner from a DevBox

RDP in, admin PowerShell, then:

```powershell
cd C:\actions-runner
.\svc.cmd stop
.\svc.cmd uninstall
# Get a fresh removal token from the same URL as registration
.\config.cmd remove --token <TOKEN>
```

Then remove the label from `target_devbox.options` in the workflow via PR.
