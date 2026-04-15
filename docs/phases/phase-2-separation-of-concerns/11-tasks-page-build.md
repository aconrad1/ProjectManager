# Task 11: Break tasks_page build() into Helper Methods

**Audit ID**: C-06  
**Effort**: Medium  
**Phase**: 2 — Separation of Concerns

---

## Objective

Break the monolithic `build()` method in `tasks_page.py` (145+ lines, 50+ widgets, 9 sections) into focused private helper methods. Each method handles one UI section.

---

## Audit Reference

> **C-06: Tasks Page build() Creates 50+ Widgets in 145 Lines**
>
> Single function creates the header, filter bar, treeview with column configuration, styling, two button rows, a right-click context menu with 30+ items, drag-and-drop setup, and status bar.
>
> Fix: Break into `_build_filters()`, `_build_treeview()`, `_build_buttons()`, `_build_context_menu()`.

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/pages/tasks_page.py` | **MODIFY** — split `build()` into helper methods |

---

## Current Code Structure

### build() method (lines ~36–192) — 9 sections

```python
def build(self) -> None:
    # Section 1: State Init (L41–42)
    self._node_index: dict[str, dict] = {}
    self._dnd_available: bool = False

    # Section 2: Restore UI State (L45–48)
    try:
        ui = load_ui_state()
    except Exception:
        ui = {}
    saved_filter = ui.get("tasks_filter", "All")
    saved_search = ui.get("tasks_search", "")

    # Section 3: Header + Filter Bar (L51–68) — 6 widgets
    top = ctk.CTkFrame(self, fg_color="transparent")
    # ... label, option menu, search entry ...

    # Section 4: Treeview Setup + Styling (L73–117) — 17 lines of columns + style
    tree_frame = ctk.CTkFrame(self, fg_color="transparent")
    cols = ("title", "supervisor", "site", ...)
    self.tree = ttk.Treeview(tree_frame, columns=cols, ...)
    # ... headings, column widths, style configuration, scrollbar ...

    # Section 5: Main Button Bar (L120–133) — 6 buttons
    btn_bar = ctk.CTkFrame(self, fg_color="transparent")
    # ... Edit, Delete, Duplicate, Add Project, Batch Edit, Refresh ...

    # Section 6: Attachments/Links Button Row (L136–147) — 5 buttons
    btn_bar2 = ctk.CTkFrame(self, fg_color="transparent")
    # ... Attach File, View Attachments, Link Folder, Open Folder, Task Notes ...

    # Section 7: Right-Click Context Menu (L150–184) — 30+ menu items
    self._ctx_menu = tk.Menu(self.tree, tearoff=0)
    # ... project ops, task ops, status submenu, priority submenu, attachments ...

    # Section 8: Drag-and-Drop Setup (L186)
    self._setup_drag_drop()

    # Section 9: Status Bar (L189–192)
    self._status_label = ctk.CTkLabel(...)
```

---

## Required Changes

### Refactor `build()` into helper methods

Replace the monolithic `build()` with a structured delegation:

```python
def build(self) -> None:
    self.grid_columnconfigure(0, weight=1)
    self.grid_rowconfigure(1, weight=1)

    self._node_index: dict[str, dict] = {}
    self._dnd_available: bool = False

    saved_filter, saved_search = self._restore_ui_state()

    self._build_filter_bar(saved_filter, saved_search)
    self._build_treeview()
    self._build_button_bars()
    self._build_context_menu()
    self._setup_drag_drop()
    self._build_status_bar()
```

### New helper methods

**`_restore_ui_state()`** — returns (saved_filter, saved_search)
```python
def _restore_ui_state(self) -> tuple[str, str]:
    try:
        ui = load_ui_state()
    except Exception:
        ui = {}
    return ui.get("tasks_filter", "All"), ui.get("tasks_search", "")
```

**`_build_filter_bar(saved_filter, saved_search)`** — creates the top frame with label, category dropdown, and search entry

**`_build_treeview()`** — creates the tree frame, configures columns/headings/widths, applies styling, adds scrollbar, binds double-click

**`_build_button_bars()`** — creates both button rows (main actions + attachment actions)

**`_build_context_menu()`** — creates the right-click menu with all submenus (project ops, task ops, status, priority, attachments, delete)

**`_build_status_bar()`** — creates the status label

### Important: Keep instance variables accessible

All methods set instance variables (`self.tree`, `self._filter_var`, `self._search_var`, `self._ctx_menu`, `self._status_label`) as before. Widget references must remain on `self` so other methods (`_populate_tree()`, `refresh()`, event handlers) can access them.

---

## Acceptance Criteria

1. `build()` is reduced to ~10–15 lines of delegation
2. Each `_build_*` method is focused on one UI section
3. All instance variables (`self.tree`, `self._filter_var`, `self._ctx_menu`, etc.) are still accessible from other methods
4. The page looks and behaves identically — same layout, same button positions, same context menu items
5. `pytest tests/gui/test_add_task_page.py` and other GUI tests pass
6. No new imports or dependencies added

---

## Constraints

- This is a **pure refactor** within a single file — do NOT extract code to new files
- Do NOT change widget styling, layout, or functionality
- Do NOT move business logic to helpers in this task (that's Task 12)
- The `_setup_drag_drop()` method already exists — just ensure it's called from `build()`
- Keep the method extraction within `tasks_page.py` — these are private UI construction methods
- Each helper method should be understandable on its own (clear parameter names, focused purpose)
