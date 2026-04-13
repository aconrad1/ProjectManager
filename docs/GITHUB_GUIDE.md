# GitHub Development Guide — ProjectManager

A plain-language guide for developing ProjectManager on GitHub, written for someone who has always worked locally with a regular Python install.

---

## What Changed (Local → GitHub)

| Before (Local) | Now (GitHub) |
|---|---|
| Python installed on your Windows PC | Python runs inside a **Codespace** — a Linux virtual machine in the cloud |
| You double-click `gui.py` to run | You open a Codespace in your browser and run commands in a terminal |
| Files live on your hard drive | Files live in a **Git repository** — every change is tracked with history |
| You copy folders to share with someone | Others **clone** (download) the repo and see every file and its history |
| If your PC dies, the code is gone | The code is safely stored on GitHub — accessible from any computer |

---

## Key Concepts in Simple Terms

### Repository (Repo)
A folder on GitHub that holds all your code, plus its complete change history. Think of it as a shared cloud folder — except every edit ever made is permanently recorded.

### Codespace
A virtual computer that GitHub spins up for you in the cloud. When you open a Codespace:
1. GitHub creates a fresh Linux machine
2. It reads `.devcontainer/devcontainer.json` to know what to install
3. It installs Python, your packages, and sets up the desktop
4. You get VS Code in your browser — connected to that machine

**Your actual PC is never touched.** Code runs entirely in the cloud. Closing the browser tab doesn't destroy it — you can reopen the same Codespace later.

### Commit
A "save point" in Git. Like saving a game — you can always go back to any previous commit. Each commit has a message explaining what changed.

**Every meaningful change should be one commit**, not six files changed in silence.

### Branch
A parallel copy of the code where you can work on something without affecting the "official" version. Think of it like:
- `main` = the production-ready version
- `feature/add-dashboard` = your experiment — if it works, you merge it back

### Pull Request (PR)
When your branch is ready, you open a PR — a formal request that says "please review my changes and merge them into `main`." Others can comment, suggest edits, and approve before the code is merged.

### Fork
A complete copy of someone else's repo under your own account. If a coworker forks ProjectManager, they get their own sandbox to experiment in. When they're ready, they open a PR back to the original repo.

---

## How the Codespace is Configured

The file `.devcontainer/devcontainer.json` tells GitHub exactly how to set up the virtual machine. Ours does:

| Setting | What it does |
|---|---|
| `image: python:3.12` | Starts with a machine that has Python 3.12 |
| `desktop-lite` feature | Installs a virtual screen (so the Tkinter GUI can run in the cloud) |
| `postCreateCommand` | Auto-runs `pip install -r requirements.txt` + installs `python3-tk` |
| `forwardPorts: [6080]` | Makes the virtual desktop accessible in your browser |
| VS Code extensions | Auto-installs the Python extension for linting and debugging |

**You don't need to memorize this.** It just means: when you (or anyone) opens the Codespace, everything is ready automatically.

---

## Day-to-Day Workflow

### Starting up

1. Go to the repo on GitHub.com.
2. Click **Code → Codespaces → Open** (or resume an existing one).
3. Wait for it to build (first time takes a minute; after that it's fast).
4. You're in VS Code with everything installed.

### Running the app

```bash
# CLI (always works, no display needed)
python scripts/cli.py --help
python scripts/cli.py list

# GUI (needs the virtual desktop)
# Open the "Desktop" tab in the Ports panel (port 6080), then:
python scripts/gui.py
```

### Making changes

```bash
# 1. See what you've changed
git status

# 2. Stage the files you want to commit
git add helpers/domain/task.py scripts/gui/pages/tasks_page.py

# 3. Commit with a clear message
git commit -m "Add deadline warning to task list"

# 4. Push to GitHub
git push
```

### Working with branches (recommended for bigger changes)

```bash
# Create a branch for your work
git checkout -b feature/add-email-export

# ... make your changes, commit them ...
git add .
git commit -m "Add email export for weekly summary"
git push -u origin feature/add-email-export

# Then go to GitHub.com and open a Pull Request
```

---

## What Not to Commit

The `.gitignore` file (in the project root) tells Git to ignore files that shouldn't be shared:

| Ignored | Why |
|---|---|
| `__pycache__/`, `*.pyc` | Python generates these automatically — they're machine-specific |
| `profiles/*/` (company folders) | **Contains personal data** — names, emails, task content, workbooks |
| `profiles/_template.xlsx` | Generated artifact |
| `.env` | Could contain secrets |
| `*.xlsx` under profiles | Workbooks are generated from `domain.json` — not source code |

**Rule of thumb:** If running `reset_for_distribution.py` would delete it, it shouldn't be in Git.

---

## What SHOULD Be in Git

| File/Folder | Why |
|---|---|
| `helpers/` | All business logic — the core of the app |
| `scripts/` | GUI and CLI entry points |
| `tests/` | Automated tests — prove the code works |
| `profiles/user_profile.yaml` | The **template** (blank fields) — not your personal data |
| `.devcontainer/` | So anyone can open a Codespace and it works immediately |
| `requirements.txt` | Package list — so installs are reproducible |
| `*.md` docs | README, AGENTS, FEATURES, this file |
| `.gitignore` | Tells Git what to skip |

---

## Understanding GitHub Terms You'll See

| Term | Meaning |
|---|---|
| **Clone** | Download a copy of the repo to your machine |
| **Push** | Upload your local commits to GitHub |
| **Pull** | Download the latest commits from GitHub to your local copy |
| **Merge** | Combine two branches into one |
| **Conflict** | Two people edited the same line — Git can't auto-merge, you pick which version to keep |
| **HEAD** | The commit you're currently on |
| **Origin** | The GitHub copy of the repo (as opposed to your local copy) |
| **Diff** | A side-by-side comparison of what changed |

---

## Safety & Privacy

- **Your personal task data never goes to GitHub** — it's in `profiles/<Company>/` which is gitignored.
- **The blank YAML template is safe** — it has empty strings, no real names or emails.
- **Your PC is not affected** — Codespaces run on GitHub's servers, not your computer.
- **The repo can be private** — only people you invite can see the code.
- **Nothing runs automatically** — there are no GitHub Actions that deploy or send data anywhere.

---

## Glossary for Quick Reference

| You say... | Git equivalent |
|---|---|
| "Save my work" | `git commit` |
| "Upload to GitHub" | `git push` |
| "Get the latest version" | `git pull` |
| "Start working on something new" | `git checkout -b branch-name` |
| "I'm done, review this" | Open a Pull Request |
| "Start fresh" | `python reset_for_distribution.py` (code-level), or delete the Codespace (environment-level) |
