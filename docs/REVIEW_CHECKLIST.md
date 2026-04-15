# Change Review Checklist — ProjectManager

Every change — whether made by a human or an AI agent — must pass these three gates before being committed. This applies to code edits, config changes, new files, and dependency updates.

---

## Gate A: Safety — Is This Safe for My Computer and Company?

| # | Check | How to verify |
|---|---|---|
| A1 | **No personal data in committed files** | `profiles/<Company>/` folders are gitignored. Never commit workbooks, `domain.json`, `task_notes.json`, or `task_links.json`. |
| A2 | **No credentials or secrets** | Search for API keys, passwords, tokens, emails, phone numbers, server paths. None should appear in code or config. |
| A3 | **No company-internal paths** | Network paths (`\\server\...`), internal URLs, or proprietary system names must not appear in source code. They belong in profile data (gitignored). |
| A4 | **Dependencies are from trusted sources** | Only install packages from PyPI. Check that new packages are well-known and actively maintained. Never run `pip install` from an arbitrary URL. |
| A5 | **No code that sends data externally** | The app should never phone home, upload telemetry, or contact external servers. Outlook integration is local COM only (Windows). |
| A6 | **No destructive operations without confirmation** | Code that deletes files, drops data, or overwrites the workbook must have a confirmation step or be explicitly user-triggered. |
| A7 | **`.gitignore` is intact** | Verify that `.gitignore` still excludes `__pycache__/`, `profiles/*/`, `.env`, and other sensitive patterns. Never remove exclusions without discussion. |

### Quick self-test
> _"If a stranger found this commit on the internet, could they learn anything private about my company, coworkers, or projects?"_
> If yes → **do not commit.**

---

## Gate B: GitHub-Ready — Will This Work for Others and Merge Cleanly?

| # | Check | How to verify |
|---|---|---|
| B1 | **Runs after `setup/reset_for_distribution.py`** | The app must launch from a blank state. If your change requires pre-existing data to avoid a crash, fix the code to handle the empty case. |
| B2 | **Runs in a fresh Codespace** | `postCreateCommand` in `devcontainer.json` installs everything. If you add a dependency, add it to `requirements.txt` with proper platform markers. |
| B3 | **Tests pass** | Run `python -m pytest tests/` — all existing tests must still pass. New features should include tests. |
| B4 | **No hardcoded paths** | Never use `C:\Users\...` or `/home/username/...`. Use the path helpers in `helpers/profile/config.py` and `helpers/io/paths.py`. |
| B5 | **Platform-aware dependencies** | Windows-only packages (`pywin32`, `tkinterdnd2`) use `; sys_platform == "win32"` markers. Runtime imports are guarded with try/except. |
| B6 | **One logical change per commit** | A commit should do one thing: fix a bug, add a feature, or refactor code. Don't mix unrelated changes — they're hard to review and hard to revert. |
| B7 | **Clear commit messages** | Format: `Add/Fix/Update <what>`. Examples: `Fix crash on empty profile load`, `Add deadline column to task export`. Avoid `misc changes` or `updates`. |
| B8 | **No merge conflicts with main** | Before opening a PR, pull the latest `main` and resolve conflicts locally. |
| B9 | **Documentation updated if needed** | If you add a CLI command → update AGENTS.md. New GUI page → update page_registry and FEATURES.md. New field → follow the Schema Extension Checklist in AGENTS.md. |

### Quick self-test
> _"If a new developer opens this Codespace tomorrow with no setup instructions, will everything work?"_
> If no → **fix the gap.**

---

## Gate C: Distribution-Ready — Does This Move Us Toward a Shippable App?

| # | Check | How to verify |
|---|---|---|
| C1 | **No development shortcuts left in** | Remove `print()` debugging, hardcoded test data, `TODO` hacks, and commented-out experiments before committing. |
| C2 | **Error messages are user-friendly** | If something fails, the user should see a plain-English message — not a raw Python traceback. Critical paths (load, save, generate) should have try/except with clear feedback. |
| C3 | **The GUI handles blank/first-run state** | After `setup/reset_for_distribution.py`, the GUI should open to the Profile page or show a clear "Set up your profile" prompt — not crash. |
| C4 | **Features degrade gracefully on different platforms** | Outlook email → skip on Linux/macOS. Drag-and-drop → warning if unavailable. PDF generation → skip if no Chrome/Edge. Never crash due to a missing optional feature. |
| C5 | **The install path is simple** | A non-technical user should be able to: clone → `python setup/install.py` → `python scripts/gui.py`. No manual pip commands, no environment variable setup, no config file editing before first launch. |
| C6 | **Profile data stays isolated** | Each profile's data lives under `profiles/<Company>/`. Switching profiles never leaks data between companies. The YAML template never contains real data. |
| C7 | **The workbook is always regenerable** | Since `domain.json` is the source of truth, deleting the `.xlsx` and running `generate` should recreate it perfectly. Never store data only in Excel. |

### Quick self-test
> _"Could I hand this to a coworker who's never seen the code, and have them running in 5 minutes?"_
> If no → **simplify the onboarding path.**

---

## How to Use This Checklist

### During development
Skim the relevant gate(s) before committing. Most changes only touch Gate A + B. Gate C matters for feature work and UI changes.

### During code review (PRs)
The reviewer should verify all three gates. If a check fails, request changes before merging.

### With AI agents (Copilot, etc.)
Before accepting AI-generated changes, run through Gate A (safety) and Gate B (will it work). AI agents don't know about your company data or deployment constraints.

---

## Red Flags — Stop and Ask Before Proceeding

- Adding a new Python package you haven't heard of
- Any change to `.gitignore` that removes exclusions
- Code that reads/writes outside the `profiles/` directory tree
- Changes to `contract.py` or `serializer.py` (data integrity core)
- Anything that touches `setup/reset_for_distribution.py` (affects what ships)
- Force-pushing, rebasing published branches, or deleting branches others use
