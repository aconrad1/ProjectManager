"""Interactive command shell — REPL that calls the helpers command registry.

Usage:
    python cli.py shell
    > list
    > run generate_reports
    > run open_latest
    > quit
"""

from __future__ import annotations

import shlex

import helpers.commands  # trigger all @register decorators  # noqa: F401
from helpers.commands.registry import list_commands, get_command

BANNER = """\
╔══════════════════════════════════════════════════════════╗
║  Weekly Report Generator — Interactive Shell             ║
║  Type 'help' for commands, 'quit' to exit.               ║
╚══════════════════════════════════════════════════════════╝"""


def shell() -> None:
    print(BANNER)
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue
        if line in ("quit", "exit"):
            break

        if line in ("help", "?"):
            print("  list                  Show all registered commands")
            print("  run <name> [args...]  Execute a command")
            print("  quit                  Exit the shell")
            continue

        if line == "list":
            cmds = list_commands()
            print(f"  {len(cmds)} registered commands:")
            for name in cmds:
                print(f"    {name}")
            continue

        if line.startswith("run "):
            parts = shlex.split(line)
            if len(parts) < 2:
                print("Usage: run <name> [args...]")
                continue
            name = parts[1]
            cmd = get_command(name)
            if not cmd:
                print(f"Unknown command: {name}")
                print(f"  Type 'list' to see available commands.")
                continue
            try:
                result = cmd(*parts[2:])
                if result is not None:
                    print(result)
            except TypeError as e:
                print(f"Argument error: {e}")
                print(f"  Most commands need a workbook or keyword args.")
                print(f"  Try the simpler ones: generate_reports, open_latest, email_report")
            except Exception as e:
                print(f"ERROR: {e}")
            continue

        print(f"Unknown input: {line!r}. Try 'help'.")
