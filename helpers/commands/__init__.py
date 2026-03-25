"""helpers.commands — shared command layer for GUI and CLI.

Importing this package ensures all command modules are loaded so that
their ``@register`` decorators populate the registry.
"""

from __future__ import annotations

from helpers.commands import report_pipeline, task_ops, utilities  # noqa: F401
from helpers.commands.registry import COMMANDS, get_command, list_commands, invoke  # noqa: F401
