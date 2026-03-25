"""
Base page contract — all GUI pages subclass BasePage.
"""
from __future__ import annotations

from typing import Protocol, Any, TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from helpers.commands.domain_service import DomainService
    from helpers.domain.profile import Profile


class AppContext(Protocol):
    """Narrow surface that pages need from the App orchestrator."""

    # shared state
    wb: Any
    profile: "Profile"
    service: "DomainService"

    # services
    def reload_data(self) -> None: ...
    def save_state(self) -> None: ...
    def save_and_refresh(self) -> None: ...
    def mark_dirty(self) -> None: ...
    def log(self, text: str) -> None: ...
    def notify(self, title: str, message: str, level: str = "info") -> None: ...
    def show_page(self, key: str) -> None: ...
    def refresh_page(self, key: str) -> None: ...


class BasePage(ctk.CTkFrame):
    """All pages subclass this and implement build() and refresh()."""

    KEY: str = "base"
    TITLE: str = "Base"

    def __init__(self, master: ctk.CTk, app: AppContext):
        super().__init__(master, corner_radius=0)
        self.app = app
        self.build()

    def build(self) -> None:
        """Create widgets and layout.  Called once in __init__."""
        raise NotImplementedError

    def refresh(self) -> None:
        """Called whenever the page is shown or data changes."""
