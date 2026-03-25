"""CLI shim — delegates to scripts/cli/run.py.

Keeps ``python scripts/cli.py <subcommand>`` working as documented.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_SCRIPT_DIR))
sys.path.insert(0, str(_PROJECT_DIR))

from cli.run import main  # noqa: E402

if __name__ == "__main__":
    main()
