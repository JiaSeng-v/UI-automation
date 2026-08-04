# Remote UI Test Execution — DevBox Runner Guide

Run the CSV-driven UI tests on a Microsoft DevBox by clicking a button in
your laptop browser. No RDP needed during the run itself.

> **Deployment model.** Each tester works on **their own fork** of
> `william051200/UI-automation`. Runners are registered against your fork
> (you're auto-admin of your fork, no permission wait), and you dispatch
> workflows from your fork's Actions tab. Shared improvements go back to
> upstream via PR.

> **Legend:** **🖥️ DEVBOX** = the RDP'd Windows machine · **💻 LAPTOP** = your local browser

---

## Architecture at a glance

```
                     💻 LAPTOP browser              GitHub                    🖥️ DEVBOX
                    ┌────────────────┐         ┌─────────────┐          ┌────────────────────┐
                    │ Click          │         │ Your fork's │          │ Self-hosted runner │
                    │ "Run workflow" │ ──────► │ Actions tab │ ──job──► │  → uv sync         │
                    └────────────────┘         └─────────────┘          │  → run.ps1 <csv>   │
                                                     ▲                  │  → screenshots     │
                                                     │ artifacts        └────────────────────┘
       artifact download ────────────────────────────┘
```

**Fork-based model.** Every tester works on **their own fork** of
`william051200/UI-automation`:

- You register your DevBox as a runner on **your fork** — you're auto-admin
  of your fork, no permission wait.
- You dispatch runs from **your fork's Actions tab**.
- Improvements to shared code (workflow, docs, scripts, new test cases) are
  contributed back to upstream via pull request.

**How it stays scalable:** each DevBox registers as a distinct runner with
a unique label (e.g. `ZY-24072026-1`). The workflow's `target_devbox` input
picks which label to run on. Adding a DevBox = one command on that DevBox;
the setup script also adds the label to your fork's workflow dropdown.

---

## Part A — First-time fork setup (💻 laptop)

Do this once per tester.

### Step 1 — Fork `william051200/UI-automation`

Open <https://github.com/william051200/UI-automation> and click **Fork** →
your account. You'll end up at `https://github.com/<your-handle>/UI-automation`.

### Step 2 — Enable Actions on your fork

Forks have Actions disabled by default:

> Your fork → **Settings** → **Actions** → **General** →
> "Allow all actions and reusable workflows" → **Save**.

---

## Part B — Register your DevBox as a runner (one-time, 🖥️ DevBox)

Run these once on each DevBox you own. After this, day-to-day usage is
entirely browser-driven from your laptop.

### Step 1 — 🖥️ DEVBOX: RDP in and open an admin PowerShell

`Win + X` → **Windows PowerShell (Admin)** → `Yes` to the UAC prompt.

> ⚠️ Do NOT `cd C:\Windows\System32`. Work from `$HOME`.
> ```powershell
> cd $HOME
> ```

### Step 2 — 🖥️ DEVBOX: Clone YOUR fork and install the toolchain

Clone your fork (not upstream — the runner must be registered against the
repo that owns the clone):

```powershell
cd $HOME
git clone https://github.com/<your-handle>/UI-automation.git
cd $HOME\UI-automation
```

Then bring in `uv`, Python, and the project dependencies:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
$env:Path = "$HOME\.local\bin;$env:Path"
uv sync
```

> If `git` isn't installed on the DevBox, `setup-runner.ps1` will install
> it via `winget` on first run — you can also skip the manual clone and
> re-run this section after Step 4 finishes.

### Step 3 — 🖥️ DEVBOX: Get a runner registration token from YOUR fork

In your **laptop** browser, open (replace `<your-handle>`):

```
https://github.com/<your-handle>/UI-automation/settings/actions/runners/new?arch=x64&os=win
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

Then run (in the same admin PowerShell, from `$HOME\UI-automation`):

```powershell
# Edit locally; print the git commands to publish it yourself
.\scripts\setup-runner.ps1 -Label ZY-30072026-1 -TesterName "Zun Yang"

# Or: let the script push and open a PR on your fork via `gh`
.\scripts\setup-runner.ps1 -Label ZY-30072026-1 -TesterName "Zun Yang" -OpenPR
```

Paste the token when prompted. The script will:

1. Auto-detect your fork slug from `git remote origin` (warns if it
   accidentally points at upstream — pass `-Repo <your-handle>/UI-automation`
   to override).
2. Verify uv / git / python (installing what's missing).
3. Download the latest GitHub Actions runner.
4. Register it against **your fork** with your label.
5. Install it as a **Windows service** so it survives reboots.
6. **Add your label to `.github/workflows/run-ui-tests.yml`** under
   `target_devbox.options` (with your name as a YAML comment).
7. If `-OpenPR` was passed, commit + push + open the PR via `gh` on your
   fork. Otherwise, print the exact `git`/`gh` commands to run yourself.

> Because it's your own fork, you can also skip the PR and push straight
> to `main`:
> ```powershell
> git add .github/workflows/run-ui-tests.yml
> git commit -m "Register DevBox runner: ZY-30072026-1"
> git push origin main
> ```

When it finishes, verify at
`https://github.com/<your-handle>/UI-automation/settings/actions/runners`
that your runner shows status **Idle**, and merge the workflow PR (or
push directly) so your label appears in the dropdown.

### Step 5 — 🖥️ DEVBOX: Log in and leave unlocked

UI automation needs an interactive, unlocked desktop.

- **Do NOT** log the DevBox off — you can disconnect RDP, but leave it logged in.
- **Do NOT** lock the screen — Windows will suspend UI input.
- Ideally: RDP once, leave the session open, close the RDP client. The DevBox
  stays running with the desktop live.

> Screens are kept open at all times, so this should be a non-issue. No
> keep-alive script is needed.

**One-time setup is done.** From here on, you never need to RDP just to run
a test.

---

## Part C — Running tests (day-to-day, browser-only)

You trigger runs from **your fork's** Actions tab. Only your fork's registered
runners will pick up the job.

### Step 1 — 💻 LAPTOP: Open the workflow page on YOUR fork

```
https://github.com/<your-handle>/UI-automation/actions/workflows/run-ui-tests.yml
```

Click **Run workflow** (top-right).

### Step 2 — 💻 LAPTOP: Fill in the inputs

| Input | Meaning | Example |
|---|---|---|
| `csv_spec` | Pick one CSV, or `ALL` to run every case sequentially | `test_cases/powershell_echo_loop.csv` |
| `target_devbox` | Which DevBox label to run on | `ZY-30072026-1` |
| `quiet` | Pass `-q` to `run.ps1` | `true` (recommended) |

Click **Run workflow**.

### Step 3 — 💻 LAPTOP: Watch and collect

- **Live logs** — click the running job to stream stdout.
- **Screenshots** — after the run, scroll to the bottom of the summary page;
  the `screenshots-<label>-<n>` artifact contains every screenshot the CSV
  captured.
- **Exit codes** — `0` = pass, `1` = assertion fail, `2` = runner error.

---

## Part D — Staying in sync with upstream

Whenever upstream (`william051200/UI-automation`) adds new test cases or
fixes, pull them into your fork:

```powershell
cd $HOME\UI-automation
git remote add upstream https://github.com/william051200/UI-automation.git   # first time only
git fetch upstream
git checkout main
git merge upstream/main   # or: git rebase upstream/main
git push origin main
```

Then re-run `uv sync` if `pyproject.toml` / `uv.lock` changed.

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

Same steps as Part B, using label `XX-DDMMYYYY-N` where `N` is one higher
than any DevBox you already own. Each label is unique per DevBox; **never**
reuse a label across two machines — GitHub will re-register and the previous
DevBox will silently stop receiving jobs.

---

## Common issues

| Symptom | Cause / Fix |
|---|---|
| Workflow queued forever | No runner is online on **your fork** with the chosen label. RDP the DevBox and check the `actions.runner.*` Windows service is running. |
| Dispatched from wrong repo | You must dispatch from `https://github.com/<your-handle>/UI-automation/actions`, not upstream. Upstream has no runners of yours. |
| `Not Found` on the runner-registration URL | You're looking at upstream. The URL must contain your fork's handle. |
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

Then remove the label from `target_devbox.options` in your fork's workflow
and push (fork-internal — no upstream PR needed unless you want to clean
the seeded list upstream too).
