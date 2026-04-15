# Task 12: Extract Tasks Page Filtering & Tree Data Logic

**Audit ID**: C-07  
**Effort**: Medium  
**Phase**: 2 — Separation of Concerns

---

## Objective

Extract the filtering, searching, and tree data assembly logic from `tasks_page.py`'s `_populate_tree()` method into a helper function. The page should call a helper for data, then handle only tree widget insertion.

---

## Audit Reference

> **C-07: Tasks Page _populate_tree() Is 170 Lines**
>
> Nested loops (project → task → deliverable) with filtering, searching, tree building, indexing, and rendering mixed together.
>
> Fix: Extract filtering into a helper (`filter_projects_and_tasks(profile, category, search_term)`) and keep only tree-widget insertion in the page.

---

## Affected Files

| File | Action |
|------|--------|
| `helpers/data/tasks.py` | **MODIFY** — add tree data preparation function |
| `scripts/gui/pages/tasks_page.py` | **MODIFY** — call helper, keep only widget insertion |

---

## Current Code

### _populate_tree() (lines ~351–438) — 3-level nested loop

```python
def _populate_tree(self):
    self.tree.delete(*self.tree.get_children())
    self._node_index.clear()

    profile = self.app.profile
    if not profile:
        return

    cat_filter = self._filter_var.get()
    search = self._search_var.get().lower()

    for project in profile.projects:
        # Category filter
        if cat_filter != "All" and project.category != cat_filter:
            continue

        # Search tasks
        matching_tasks = []
        for task in project.tasks:
            if search:
                haystack = f"{task.title} {task.supervisor} {task.site} {task.status}".lower()
                if search not in haystack:
                    continue
            matching_tasks.append(task)

        if not matching_tasks and search:
            continue

        # Insert project row
        proj_iid = f"proj_{project.id}"
        alloc = project.time_allocated_total
        spent = project.time_spent_total
        time_str = f"{alloc:.1f}/{spent:.1f}" if alloc or spent else ""
        self.tree.insert("", "end", iid=proj_iid, values=(...), tags=("project",))
        self._node_index[proj_iid] = {"type": "project", "id": project.id, ...}

        # Insert task rows
        for task in matching_tasks:
            prio_label = PRIORITY_LABELS.get(task.priority, f"P{task.priority}")
            task_iid = f"task_{task.id}"
            # ... format time, scheduled date ...
            self.tree.insert(proj_iid, "end", iid=task_iid, values=(...), tags=(...))
            self._node_index[task_iid] = {"type": "task", "id": task.id, ...}

            # Insert deliverable rows
            for deliv in task.deliverables:
                d_iid = f"deliv_{deliv.id}"
                # ... format percent, time ...
                self.tree.insert(task_iid, "end", iid=d_iid, values=(...), tags=("deliverable",))
                self._node_index[d_iid] = {"type": "deliverable", "id": deliv.id, ...}

    # Tag coloring
    for prio in range(1, 6):
        bg = TREEVIEW_TAG_COLORS.get(f"p{prio}", "#ffffff")
        self.tree.tag_configure(f"p{prio}", background=bg)
    # ...
    self.update_status_bar()
```

---

## Required Changes

### Step 1: Add filtering + data assembly function to `helpers/data/tasks.py`

```python
"""Task data helpers for UI consumption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from helpers.domain.profile import Profile
    from helpers.domain.project import Project
    from helpers.domain.task import Task


@dataclass
class TreeProject:
    """Pre-computed project row data for tree insertion."""
    id: str
    title: str
    status: str
    category: str
    time_str: str
    tasks: list[TreeTask]


@dataclass
class TreeTask:
    """Pre-computed task row data for tree insertion."""
    id: str
    title: str
    supervisor: str
    site: str
    status: str
    priority: int
    priority_label: str
    scheduled: str
    time_str: str
    category: str  # from parent project
    project_id: str
    deliverables: list[TreeDeliverable]


@dataclass
class TreeDeliverable:
    """Pre-computed deliverable row data for tree insertion."""
    id: str
    title: str
    status: str
    pct_str: str
    time_str: str
    task_id: str
    task_title: str


def build_tree_data(
    profile: Profile,
    category: str = "All",
    search: str = "",
) -> list[TreeProject]:
    """Build filtered, formatted tree data from a profile.
    
    Applies category filtering and text search. Returns a list of
    TreeProject objects with nested tasks and deliverables, ready for
    tree widget insertion.
    """
    from helpers.data.queries import filter_projects_by_category
    
    result: list[TreeProject] = []
    search_lower = search.lower() if search else ""

    for project in filter_projects_by_category(profile.projects, category):
        matching_tasks: list[TreeTask] = []

        for task in project.tasks:
            if search_lower:
                haystack = f"{task.title} {task.supervisor} {task.site} {task.status}".lower()
                if search_lower not in haystack:
                    continue

            deliverables: list[TreeDeliverable] = []
            for deliv in task.deliverables:
                d_alloc = f"{deliv.time_allocated:.1f}" if deliv.time_allocated else ""
                d_spent = f"{deliv.time_spent:.1f}" if deliv.time_spent else ""
                deliverables.append(TreeDeliverable(
                    id=deliv.id,
                    title=deliv.title,
                    status=deliv.status,
                    pct_str=f"{deliv.percent_complete}%",
                    time_str=f"{d_alloc}/{d_spent}" if d_alloc or d_spent else "",
                    task_id=task.id,
                    task_title=task.title,
                ))

            t_alloc = task.time_allocated_total
            t_spent = task.time_spent_total
            sched = task.scheduled_date.strftime("%m/%d") if task.scheduled_date else ""

            matching_tasks.append(TreeTask(
                id=task.id,
                title=task.title,
                supervisor=task.supervisor,
                site=task.site,
                status=task.status,
                priority=task.priority,
                priority_label="",  # set by caller from PRIORITY_LABELS
                scheduled=sched,
                time_str=f"{t_alloc:.1f}/{t_spent:.1f}" if t_alloc or t_spent else "",
                category=project.category,
                project_id=project.id,
                deliverables=deliverables,
            ))

        if not matching_tasks and search_lower:
            continue

        alloc = project.time_allocated_total
        spent = project.time_spent_total
        result.append(TreeProject(
            id=project.id,
            title=project.title,
            status=project.status,
            category=project.category,
            time_str=f"{alloc:.1f}/{spent:.1f}" if alloc or spent else "",
            tasks=matching_tasks,
        ))

    return result
```

### Step 2: Simplify `_populate_tree()` in `scripts/gui/pages/tasks_page.py`

```python
from helpers.data.tasks import build_tree_data

def _populate_tree(self):
    self.tree.delete(*self.tree.get_children())
    self._node_index.clear()

    profile = self.app.profile
    if not profile:
        return

    tree_data = build_tree_data(
        profile,
        category=self._filter_var.get(),
        search=self._search_var.get(),
    )

    for proj in tree_data:
        proj_iid = f"proj_{proj.id}"
        self.tree.insert("", "end", iid=proj_iid,
                         values=(proj.title, "", "", proj.status, "",
                                 "", proj.time_str, proj.category),
                         open=True, tags=("project",))
        self._node_index[proj_iid] = {
            "type": "project", "id": proj.id, "title": proj.title,
        }

        for task in proj.tasks:
            prio_label = PRIORITY_LABELS.get(task.priority, f"P{task.priority}")
            task_iid = f"task_{task.id}"
            self.tree.insert(proj_iid, "end", iid=task_iid,
                             values=(task.title, task.supervisor, task.site,
                                     task.status, prio_label, task.scheduled,
                                     task.time_str, task.category),
                             tags=(f"p{task.priority}",))
            self._node_index[task_iid] = {
                "type": "task", "id": task.id, "title": task.title,
                "project_id": proj.id,
            }

            for deliv in task.deliverables:
                d_iid = f"deliv_{deliv.id}"
                self.tree.insert(task_iid, "end", iid=d_iid,
                                 values=(deliv.title, "", "", deliv.status,
                                         deliv.pct_str, "", deliv.time_str, ""),
                                 tags=("deliverable",))
                self._node_index[d_iid] = {
                    "type": "deliverable", "id": deliv.id,
                    "title": deliv.title, "task_id": task.id,
                    "task_title": task.task_title,
                }

    # Tag coloring (unchanged)
    for prio in range(1, 6):
        bg = TREEVIEW_TAG_COLORS.get(f"p{prio}", "#ffffff")
        self.tree.tag_configure(f"p{prio}", background=bg)
    # ...
    self.update_status_bar()
```

---

## Acceptance Criteria

1. `build_tree_data()` function exists in `helpers/data/tasks.py`
2. No category filtering, search matching, or time formatting logic remains in `_populate_tree()`
3. `_populate_tree()` only handles tree widget insertion and `_node_index` building
4. Search behavior is identical (case-insensitive, matches title/supervisor/site/status)
5. Category filtering uses `filter_projects_by_category()` from Task 8
6. `pytest tests/` passes
7. `build_tree_data()` can be unit tested without a GUI

---

## Constraints

- `PRIORITY_LABELS` mapping stays in the page (it's a UI display concern)
- `_node_index` building stays in the page (it's widget-specific state)
- Tag coloring configuration stays in the page (it's treeview-specific)
- Do NOT change the IID format (`proj_`, `task_`, `deliv_` prefixes) — other methods depend on it
- If Task 8 hasn't been completed, inline the category filter in `build_tree_data()`
