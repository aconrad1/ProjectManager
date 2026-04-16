"""
Weekly Report Generator — Command-Line Interface
=================================================
Provides a headless alternative to the GUI for scripting and CI.

Usage:
    python cli.py generate          Generate all reports
    python cli.py save              Save & snapshot the workbook
    python cli.py open              Open the latest PDF/MD report
    python cli.py email             Draft an email with the latest report
    python cli.py list              List active tasks
    python cli.py profile           Show current profile info
    python cli.py profile --switch N  Switch to profile index N
    python cli.py init "Name" "Company" --workbook "File.xlsx"
    python cli.py shell             Interactive command shell
    python cli.py project list      List projects in the hierarchy
    python cli.py task list [--project <id>]     List tasks
    python cli.py task add --project <id> --title "…"
    python cli.py deliverable list --task <id>
    python cli.py deliverable add --task <id> --title "…"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ── Ensure project root is importable ──────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent.parent   # scripts/
_PROJECT_DIR = _SCRIPT_DIR.parent                       # project root
sys.path.insert(0, str(_SCRIPT_DIR))
sys.path.insert(0, str(_PROJECT_DIR))

from helpers.profile.profile import (
    USER_NAME, USER_ROLE, USER_COMPANY,
    USER_EMAIL, USER_PHONE, RECIPIENT_NAME, RECIPIENT_EMAIL, WORKBOOK_FILENAME,
    DAILY_HOURS_BUDGET,
    get_profiles, get_active_index, switch_profile,
)
from helpers.profile.config import workbook_path
from helpers.data.workbook import load_workbook
from helpers.persistence.contract import sync as sync_profile, resync_json
from helpers.commands.task_ops import set_post_mutate_hook


def _load_profile():
    """Load the workbook and sync the domain Profile hierarchy."""
    from helpers.profile.profile import scaffold_profile
    wb_path = workbook_path()
    if not wb_path.exists():
        scaffold_profile(USER_COMPANY, WORKBOOK_FILENAME)
    wb = load_workbook(wb_path)
    profile = sync_profile(
        wb,
        USER_COMPANY,
        wb_path,
        profile_name=USER_NAME,
        role=USER_ROLE,
        email=USER_EMAIL,
        phone=USER_PHONE,
        recipient_name=RECIPIENT_NAME,
        recipient_email=RECIPIENT_EMAIL,
        workbook_filename=WORKBOOK_FILENAME,
        daily_hours_budget=DAILY_HOURS_BUDGET,
    )

    # Auto-save .xlsx and resync JSON after every task_ops mutation
    def _auto_persist(mutated_wb):
        p = workbook_path()
        mutated_wb.save(str(p))
        resync_json(mutated_wb, USER_COMPANY, p, **_meta_kwargs())

    set_post_mutate_hook(_auto_persist)

    return wb, profile


def _meta_kwargs() -> dict:
    """Return the profile metadata kwargs used in contract calls."""
    return dict(
        profile_name=USER_NAME,
        role=USER_ROLE,
        email=USER_EMAIL,
        phone=USER_PHONE,
        recipient_name=RECIPIENT_NAME,
        recipient_email=RECIPIENT_EMAIL,
        workbook_filename=WORKBOOK_FILENAME,
        daily_hours_budget=DAILY_HOURS_BUDGET,
    )


# ── Sub-command handlers ───────────────────────────────────────────────────────

def cmd_generate(args: argparse.Namespace) -> None:
    from helpers.commands.report_pipeline import generate_reports
    print(f"\n{'='*60}")
    print(f"  {USER_COMPANY} Weekly Report Generator  (CLI)")
    print(f"  User: {USER_NAME}")
    print(f"{'='*60}\n")
    generate_reports(log=print)
    print()


def cmd_save(args: argparse.Namespace) -> None:
    from helpers.commands.utilities import save_workbook_cmd
    wb = load_workbook(workbook_path())
    save_workbook_cmd(wb, log=print)


def cmd_open(args: argparse.Namespace) -> None:
    from helpers.commands.utilities import open_latest_report
    target = open_latest_report()
    if target:
        print(f"Opened: {target}")
    else:
        print("No reports found. Generate one first.")


def cmd_email(args: argparse.Namespace) -> None:
    from helpers.commands.utilities import email_report
    try:
        email_report(log=print)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_list(args: argparse.Namespace) -> None:
    _, profile = _load_profile()

    print(f"\n{'='*60}")
    print(f"  Active Tasks — {USER_NAME}")
    print(f"{'='*60}\n")

    categories = ["Weekly", "Ongoing"]
    if args.all:
        from helpers.config.loader import valid_categories
        categories = list(valid_categories())

    for cat in categories:
        tasks = profile.tasks_for_category(cat)
        print(f"── {cat} ({len(tasks)}) ─────────────────────")
        for t in sorted(tasks, key=lambda x: x.priority):
            print(f"  P{t.priority}  [{t.status}]  {t.title}  (id: {t.id})")
        print()


def cmd_profile(args: argparse.Namespace) -> None:
    if args.switch is not None:
        switch_profile(args.switch)
        print(f"Switched to profile {args.switch}.")
        return

    profiles = get_profiles()
    active = get_active_index()
    print(f"\nActive profile: [{active}]")
    for i, p in enumerate(profiles):
        marker = " *" if i == active else "  "
        print(f"  {marker} [{i}] {p.get('name', '?')}  ({p.get('company', '')})")
    print()


def cmd_init(args: argparse.Namespace) -> None:
    from helpers.profile.profile import init_profile
    from helpers.io.paths import PROFILE_SUBDIRS
    name = args.name
    company = args.company
    wb_name = args.workbook or ""

    idx = init_profile({
        "name": name,
        "company": company,
        "workbook_filename": wb_name,
    })
    print(f"\nProfile [{idx}] created for {name} ({company})")
    print(f"Folder structure:")
    for sub in PROFILE_SUBDIRS:
        print(f"  {company}/{sub}/")
    if wb_name:
        print(f"  {company}/{wb_name}")
    print(f"\nSwitch to it with: python cli.py profile --switch {idx}")
    print()


# ── Hierarchy commands ─────────────────────────────────────────────────────────

def cmd_project(args: argparse.Namespace) -> None:
    """Handle 'project list' subcommand."""
    _, profile = _load_profile()

    if args.action == "list":
        print(f"\n{'='*60}")
        print(f"  Projects — {profile.title}")
        print(f"{'='*60}\n")
        for p in profile.projects:
            print(f"  [{p.id}]  {p.title}  ({p.task_count} tasks)")
        print()
    else:
        print(f"Unknown project action: {args.action}")


def cmd_task(args: argparse.Namespace) -> None:
    """Handle 'task list/add/delete' subcommands."""
    wb, profile = _load_profile()

    if args.action == "list":
        project_id = getattr(args, "project", None)
        if project_id:
            proj = profile.find_project(project_id)
            if not proj:
                print(f"Project not found: {project_id}")
                sys.exit(1)
            tasks = proj.tasks
            label = proj.title
        else:
            tasks = profile.all_tasks
            label = "All Projects"

        print(f"\n{'='*60}")
        print(f"  Tasks — {label}")
        print(f"{'='*60}\n")
        for t in sorted(tasks, key=lambda x: x.priority):
            print(f"  P{t.priority}  [{t.status}]  {t.title}  (id: {t.id})")
        print(f"\n  Total: {len(tasks)} task(s)\n")

    elif args.action == "add":
        project_id = getattr(args, "project", None)
        title = getattr(args, "title", None)
        if not project_id or not title:
            print("Usage: cli task add --project <id> --title \"Task Title\"")
            sys.exit(1)
        proj = profile.find_project(project_id)
        if not proj:
            print(f"Project not found: {project_id}")
            sys.exit(1)

        from helpers.commands.task_ops import add_task
        from helpers.config.loader import default_status, default_priority
        data = {"Title": title, "Status": default_status(), "Priority": default_priority()}
        add_task(wb, proj.id, data)
        print(f"Task '{title}' added to {proj.title}.")

    elif args.action == "delete":
        task_id = getattr(args, "task_id", None)
        if not task_id:
            print("Usage: cli task delete --task-id <id>")
            sys.exit(1)

        from helpers.commands.task_ops import delete_task
        t = profile.find_task_global(task_id)
        if not t:
            print(f"Task not found: {task_id}")
            sys.exit(1)
        delete_task(wb, task_id)
        print(f"Task '{t.title}' deleted.")

    else:
        print(f"Unknown task action: {args.action}")


def cmd_deliverable(args: argparse.Namespace) -> None:
    """Handle 'deliverable list/add' subcommands."""
    _, profile = _load_profile()

    task_id = getattr(args, "task", None)
    if not task_id:
        print("Usage: cli deliverable <action> --task <id>")
        sys.exit(1)

    target_task = profile.find_task_global(task_id)
    if not target_task:
        print(f"Task not found: {task_id}")
        sys.exit(1)

    if args.action == "list":
        print(f"\n{'='*60}")
        print(f"  Deliverables — {target_task.title}")
        print(f"{'='*60}\n")
        if target_task.deliverables:
            for d in target_task.deliverables:
                print(f"  [{d.id}]  {d.title}  [{d.status}]")
        else:
            print("  No deliverables defined.")
        print()

    elif args.action == "add":
        title = getattr(args, "title", None)
        if not title:
            print("Usage: cli deliverable add --task <id> --title \"…\"")
            sys.exit(1)

        wb, _ = _load_profile()
        from helpers.commands.task_ops import add_deliverable
        from helpers.config.loader import default_status
        data = {"Title": title, "Status": default_status(), "% Complete": 0}
        d = add_deliverable(wb, task_id, data)
        print(f"Deliverable '{title}' (ID: {d.deliverable_id}) added to task '{target_task.title}'.")

    else:
        print(f"Unknown deliverable action: {args.action}")


# ── Argument parser ────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli",
        description="Weekly Report Generator — CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("generate", help="Run the full report-generation pipeline")
    sub.add_parser("save", help="Save & snapshot the workbook")
    sub.add_parser("open", help="Open the latest report")
    sub.add_parser("email", help="Draft an email with the latest PDF attached")

    list_p = sub.add_parser("list", help="List active tasks")
    list_p.add_argument("--all", action="store_true", help="Include completed tasks")

    prof_p = sub.add_parser("profile", help="Show or switch profiles")
    prof_p.add_argument("--switch", type=int, metavar="N", help="Switch to profile index N")

    init_p = sub.add_parser("init", help="Create a new profile with folder structure")
    init_p.add_argument("name", help="User name for the new profile")
    init_p.add_argument("company", help="Company / profile folder name")
    init_p.add_argument("--workbook", metavar="FILE", help="Workbook filename (e.g. My Report.xlsx)")

    sub.add_parser("shell", help="Start an interactive command shell")

    # ── Hierarchy subcommands ──────────────────────────────────────────────
    project_p = sub.add_parser("project", help="Manage projects in the hierarchy")
    project_p.add_argument("action", choices=["list"], help="Action to perform")

    task_p = sub.add_parser("task", help="Manage tasks in the hierarchy")
    task_p.add_argument("action", choices=["list", "add", "delete"], help="Action to perform")
    task_p.add_argument("--project", metavar="ID", help="Project ID to scope tasks")
    task_p.add_argument("--title", help="Title for the new task (for 'add')")
    task_p.add_argument("--task-id", metavar="ID", help="Task ID to delete (for 'delete')")

    deliv_p = sub.add_parser("deliverable", help="Manage deliverables in the hierarchy")
    deliv_p.add_argument("action", choices=["list", "add"], help="Action to perform")
    deliv_p.add_argument("--task", metavar="ID", help="Parent task ID")
    deliv_p.add_argument("--title", help="Title for the new deliverable (for 'add')")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "generate": cmd_generate,
        "save": cmd_save,
        "open": cmd_open,
        "email": cmd_email,
        "list": cmd_list,
        "profile": cmd_profile,
        "init": cmd_init,
        "shell": lambda _args: _start_shell(),
        "project": cmd_project,
        "task": cmd_task,
        "deliverable": cmd_deliverable,
    }
    dispatch[args.command](args)


def _start_shell() -> None:
    from cli.shell import shell
    shell()


if __name__ == "__main__":
    main()
