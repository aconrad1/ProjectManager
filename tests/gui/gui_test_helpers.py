"""Widget search and event simulation utilities for GUI tests."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Type


def find_widget(parent, widget_type: Type, *, text: str | None = None):
    """Recursively find the first child widget matching *widget_type*.

    If *text* is given, also match ``cget("text")`` (for CTk/tk labels/buttons).
    Returns None if no match is found.
    """
    for child in parent.winfo_children():
        if isinstance(child, widget_type):
            if text is None:
                return child
            try:
                if child.cget("text") == text:
                    return child
            except (tk.TclError, AttributeError):
                pass
        # Recurse into children
        found = find_widget(child, widget_type, text=text)
        if found is not None:
            return found
    return None


def find_all_widgets(parent, widget_type: Type) -> list:
    """Recursively find ALL descendant widgets matching *widget_type*."""
    results = []
    for child in parent.winfo_children():
        if isinstance(child, widget_type):
            results.append(child)
        results.extend(find_all_widgets(child, widget_type))
    return results


def get_treeview_items(tree: ttk.Treeview) -> list[dict]:
    """Extract all top-level + nested items from a Treeview.

    Returns a flat list of dicts: ``{"iid": ..., "values": ..., "parent": ...}``.
    """
    items = []

    def _walk(parent_iid: str = ""):
        for iid in tree.get_children(parent_iid):
            items.append({
                "iid": iid,
                "values": tree.item(iid, "values"),
                "parent": parent_iid,
                "open": tree.item(iid, "open"),
                "tags": tree.item(iid, "tags"),
            })
            _walk(iid)

    _walk()
    return items


def get_treeview_column_names(tree: ttk.Treeview) -> list[str]:
    """Return the column identifiers of a Treeview (excluding #0)."""
    return list(tree["columns"])


def simulate_click(widget, pump_fn=None) -> None:
    """Generate a left-button click event on *widget*."""
    widget.event_generate("<Button-1>")
    widget.event_generate("<ButtonRelease-1>")
    if pump_fn:
        pump_fn()


def simulate_type(widget, text: str, pump_fn=None) -> None:
    """Clear an Entry/Textbox widget and type *text* into it.

    Works with both ``tk.Entry`` and ``ctk.CTkEntry`` (which wraps a tk.Entry).
    """
    try:
        # CTkEntry
        widget.delete(0, "end")
        widget.insert(0, text)
    except (tk.TclError, AttributeError):
        try:
            # CTkTextbox
            widget.delete("1.0", "end")
            widget.insert("1.0", text)
        except Exception:
            pass
    if pump_fn:
        pump_fn()


def count_children(parent, widget_type: Type) -> int:
    """Count the total number of descendant widgets matching *widget_type*."""
    return len(find_all_widgets(parent, widget_type))
