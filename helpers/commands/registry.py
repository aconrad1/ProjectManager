"""Command registry — maps command names to callables.

Both the GUI and CLI use these names to invoke shared logic.
Commands are registered via the ``@register`` decorator at module load time.
The ``COMMANDS`` dict and ``get_command()`` provide a public discovery API
for adapters (interactive shell, future web UI, etc.).
"""

from __future__ import annotations

from typing import Any, Callable

_commands: dict[str, Callable[..., Any]] = {}


def register(name: str):
    """Decorator that registers a callable under *name*."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        _commands[name] = fn
        return fn
    return decorator


def invoke(name: str, **kwargs: Any) -> Any:
    """Call the command registered as *name* with *kwargs*."""
    if name not in _commands:
        raise KeyError(f"Unknown command: {name!r}")
    return _commands[name](**kwargs)


def get_command(name: str) -> Callable[..., Any] | None:
    """Return the callable for *name*, or ``None`` if not found."""
    return _commands.get(name)


def list_commands() -> list[str]:
    """Return sorted list of registered command names."""
    return sorted(_commands)


# Public read-only view — populated once all command modules are imported.
# Callers should import the command modules first (e.g. via helpers.commands)
# to ensure the decorators have run.
COMMANDS = _commands
