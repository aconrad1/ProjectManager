"""Shared fixtures for GUI widget-level tests.

Provides a real ``Tk()`` root (hidden), a ``MockApp`` that satisfies the
``AppContext`` protocol, and auto-patches for modal dialogs so tests never
block on user input.
"""

from __future__ import annotations

import sys
import tkinter as tk
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ── Ensure project paths are importable ────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_PROJECT = _HERE.parent.parent
_SCRIPTS = _PROJECT / "scripts"
for p in (_PROJECT, _SCRIPTS, _HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


# ══════════════════════════════════════════════════════════════════════════════
#  Skip early if there is no display (headless CI without XVFB)
# ══════════════════════════════════════════════════════════════════════════════

def _display_available() -> bool:
    try:
        root = tk.Tk()
        root.destroy()
        return True
    except tk.TclError:
        return False


if not _display_available():
    pytest.skip("No display available (run with XVFB on CI)", allow_module_level=True)


# ══════════════════════════════════════════════════════════════════════════════
#  Domain factories
# ══════════════════════════════════════════════════════════════════════════════

def make_profile(company="TestCo", name="Test User"):
    from helpers.domain.profile import Profile
    return Profile(
        id="profile:TestCo", title=name, company=company, status="Active",
        workbook_filename="test.xlsx",
        daily_hours_budget=8.0, weekly_hours_budget=40.0,
    )


def make_project(pid="P-001", title="Ongoing Project", category="Ongoing"):
    from helpers.domain.project import Project
    return Project(id=pid, title=title, category=category, status="In Progress")


def make_task(tid="T-001", title="Task A", project_id="P-001", **kw):
    from helpers.domain.task import Task
    defaults = dict(
        id=tid, title=title, project_id=project_id, status="In Progress",
        priority=2, supervisor="Jane Doe", site="Harmattan",
    )
    defaults.update(kw)
    return Task(**defaults)


def make_deliverable(did="D-001", title="Deliverable 1", task_id="T-001"):
    from helpers.domain.deliverable import Deliverable
    return Deliverable(
        id=did, title=title, task_id=task_id, status="Not Started",
        percent_complete=0, time_allocated=4.0, time_spent=1.0,
    )


def build_sample_profile():
    """Build a profile with 2 projects, 3 tasks, 2 deliverables."""
    profile = make_profile()

    p1 = make_project("P-001", "Ongoing Project", "Ongoing")
    t1 = make_task("T-001", "Task A", "P-001",
                   start=date(2026, 3, 20), end=date(2026, 3, 27),
                   deadline=date(2026, 4, 1))
    t2 = make_task("T-002", "Task B", "P-001", priority=1,
                   start=date(2026, 3, 22), end=date(2026, 3, 30))
    d1 = make_deliverable("D-001", "Deliverable 1", "T-001")
    d2 = make_deliverable("D-002", "Deliverable 2", "T-001")
    t1.add_deliverable(d1)
    t1.add_deliverable(d2)
    p1.add_task(t1)
    p1.add_task(t2)

    p2 = make_project("P-002", "Weekly Project", "Weekly")
    t3 = make_task("T-003", "Weekly Task", "P-002", priority=3,
                   supervisor="Kurt MacKay", site="Taylor")
    p2.add_task(t3)

    profile.add_project(p1)
    profile.add_project(p2)
    return profile


# ══════════════════════════════════════════════════════════════════════════════
#  MockApp — satisfies the AppContext protocol without real workbook
# ══════════════════════════════════════════════════════════════════════════════

class MockApp:
    """Lightweight stand-in for ``App`` that pages can reference."""

    def __init__(self, profile=None):
        from helpers.commands.domain_service import DomainService

        self.wb = MagicMock()
        self.profile = profile or build_sample_profile()
        self.service = DomainService(self.profile, self.wb)
        # Patch _persist to be a no-op (avoids file I/O)
        self.service._persist = MagicMock()

        # Protocol methods
        self.reload_data = MagicMock()
        self.save_state = MagicMock()
        self.save_and_refresh = MagicMock()
        self.mark_dirty = MagicMock()
        self.log = MagicMock()
        self.notify = MagicMock()
        self.show_page = MagicMock()
        self.refresh_page = MagicMock()


# ══════════════════════════════════════════════════════════════════════════════
#  Pytest fixtures
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def tk_root():
    """Create a single, hidden Tk root that lives for the entire test session."""
    import customtkinter as ctk
    ctk.set_appearance_mode("light")
    root = ctk.CTk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def mock_app():
    """Return a fresh ``MockApp`` for each test."""
    return MockApp()


@pytest.fixture
def pump(tk_root):
    """Return a callable that flushes the Tk event queue."""
    def _pump():
        tk_root.update_idletasks()
        tk_root.update()
    return _pump


# ── Auto-use: patch modal dialogs so tests never block ─────────────────────

@pytest.fixture(autouse=True)
def _patch_modals():
    """Globally patch messagebox and filedialog to prevent GUI blocking."""
    with patch("tkinter.messagebox.showinfo") as m_info, \
         patch("tkinter.messagebox.showwarning") as m_warn, \
         patch("tkinter.messagebox.showerror") as m_error, \
         patch("tkinter.messagebox.askyesno", return_value=True) as m_yesno, \
         patch("tkinter.filedialog.askopenfilename", return_value="") as m_open, \
         patch("tkinter.filedialog.askopenfilenames", return_value=()) as m_opens, \
         patch("tkinter.filedialog.askdirectory", return_value="") as m_dir, \
         patch("tkinter.filedialog.asksaveasfilename", return_value="") as m_save:
        yield {
            "showinfo": m_info,
            "showwarning": m_warn,
            "showerror": m_error,
            "askyesno": m_yesno,
            "askopenfilename": m_open,
            "askopenfilenames": m_opens,
            "askdirectory": m_dir,
            "asksaveasfilename": m_save,
        }


@pytest.fixture(autouse=True)
def _patch_grab_set():
    """Patch CTkToplevel.grab_set to prevent modal blocking in tests."""
    import customtkinter as ctk
    with patch.object(ctk.CTkToplevel, "grab_set", lambda self: None):
        yield


@pytest.fixture(autouse=True)
def _patch_ui_state():
    """Patch UI state persistence so tests don't hit disk."""
    with patch("helpers.ui.state.load_ui_state", return_value={}), \
         patch("helpers.ui.state.save_ui_state"):
        yield
