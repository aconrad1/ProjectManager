"""Simple logger adapter shared by GUI and CLI.

Provides a callback-based logger so the GUI can route messages through
``after()`` while the CLI prints directly to stdout.
"""

from __future__ import annotations

from typing import Callable


class Logger:
    """Thin logging adapter.

    Parameters
    ----------
    sink : callable
        A function that accepts a single ``str`` argument.
        Defaults to ``print``.
    """

    def __init__(self, sink: Callable[[str], None] | None = None):
        self._sink: Callable[[str], None] = sink or print

    def log(self, message: str) -> None:
        self._sink(message)

    def set_sink(self, sink: Callable[[str], None]) -> None:
        self._sink = sink


# Module-level default logger (prints to stdout).
default_logger = Logger()
