# Reproducibility notes

- All values are pinned directly in the CSV `# STEPS` rows (no random generation at run time); the CSV format has no separate `inputs` block.
- The CSV spec is parsed deterministically in-memory by `run_test.py` (via `scripts/csvfmt/`), so the same file always yields the same step sequence.
- Window/control targeting via UIA names/ids, not hard-coded coordinates. The only mouse-coordinate clicks derive `(x, y)` from UIA-reported rectangles, so they survive window-position changes.
- Console validation uses UIA text — independent of fonts, themes, OCR.
- Screenshots are evidence only; pass/fail is decided by the UIA assertion.
- `uv.lock` pins every transitive dependency with content hashes.
- `.python-version` pins the interpreter; `uv` will download the exact build on first sync.
