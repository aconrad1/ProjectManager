# Task 13: Centralize Color Mappings in ui_theme.py

**Audit ID**: N-07  
**Effort**: Small  
**Phase**: 2 — Separation of Concerns

---

## Objective

Move all hardcoded color mappings (priority colors, status colors, site palette, button colors) from individual pages into centralized constants in `ui_theme.py` (backed by `theme.json`). Pages should reference exported constants — no inline color hex values.

---

## Audit Reference

> **N-07: Status/Priority Color Mapping Duplicated Across Pages**
>
> Each page independently maps priorities to colors or statuses to colors. Some use `ui_theme.py`, others hardcode values.

---

## Affected Files

| File | Action |
|------|--------|
| `scripts/gui/ui_theme.py` | **MODIFY** — add missing color constants |
| `helpers/config/theme.json` | **MODIFY** — add new color entries |
| `scripts/gui/pages/dashboard_page.py` | **MODIFY** — use centralized colors |
| `scripts/gui/pages/gantt_page.py` | **MODIFY** — use centralized colors |
| `scripts/gui/pages/scheduler_page.py` | **MODIFY** — use centralized colors |

---

## Current State

### Already centralized in ui_theme.py (good):
```python
PRIORITY_COLORS: dict[int, str] = {int(k): v for k, v in _theme["priority_colors"].items()}
STATUS_COLORS: dict[str, str] = _theme.get("status_colors", {})
TREEVIEW_TAG_COLORS: dict[str, str] = _theme.get("treeview_tag_colors", {})
```

### Hardcoded in dashboard_page.py:
```python
# Line ~104 — duplicates PRIORITY_COLORS
prio_colors = {1: "#c0392b", 2: "#e67e22", 3: "#f39c12", 4: "#7f8c8d", 5: "#bdc3c7"}

# Line ~172 — site distribution palette (not in theme at all)
site_colors = ["#003DA5", "#336BBF", "#2980b9", "#16a085", "#27ae60",
               "#8e44ad", "#d35400", "#c0392b"]

# Line ~204 — priority badge color
pcolor = "#c0392b" if t.priority == 1 else "#e67e22"
```

### Hardcoded in scheduler_page.py:
```python
# Lines ~30-40 — status background colors
_STATUS_BG = {
    "in progress":  "#D6EAF8",
    "on track":     "#D5F5E3",
    "not started":  "#F2F3F4",
    "ongoing":      "#D6EAF8",
    "recurring":    "#D6EAF8",
    "on hold":      "#FADBD8",
    "completed":    "#ABEBC6",
}
```

### Hardcoded in gantt_page.py:
```python
# Multiple dark-mode fallback strings throughout _render()
fill=self._dk("text_dim", "#A0A0B0")
grid_color = self._dk("grid_line", "#333355")
today_color = self._dk("today_line", "#FF6B6B")

# Deadline marker
fill="#c0392b", outline="#c0392b"
```

---

## Required Changes

### Step 1: Add new color constants to `helpers/config/theme.json`

Add these sections to the existing theme.json:

```json
{
    "site_palette": ["#003DA5", "#336BBF", "#2980b9", "#16a085", "#27ae60",
                     "#8e44ad", "#d35400", "#c0392b"],
    "status_bg_colors": {
        "in progress": "#D6EAF8",
        "on track": "#D5F5E3",
        "not started": "#F2F3F4",
        "ongoing": "#D6EAF8",
        "recurring": "#D6EAF8",
        "on hold": "#FADBD8",
        "completed": "#ABEBC6"
    },
    "gantt_colors_dark": {
        "text_dim": "#A0A0B0",
        "grid_line": "#333355",
        "today_line": "#FF6B6B",
        "project_bg": "#2A2A4A",
        "section_bg": "#3A3020",
        "row_even": "#252538"
    }
}
```

### Step 2: Export new constants from `scripts/gui/ui_theme.py`

```python
SITE_PALETTE: list[str] = _theme.get("site_palette", [
    "#003DA5", "#336BBF", "#2980b9", "#16a085", "#27ae60",
    "#8e44ad", "#d35400", "#c0392b"
])
STATUS_BG_COLORS: dict[str, str] = _theme.get("status_bg_colors", {})
GANTT_COLORS_DARK: dict[str, str] = _theme.get("gantt_colors_dark", {})
```

### Step 3: Update pages to use centralized constants

**dashboard_page.py:**
```python
from scripts.gui.ui_theme import PRIORITY_COLORS, SITE_PALETTE

# Replace: prio_colors = {1: "#c0392b", ...}
# With: (use PRIORITY_COLORS directly)

# Replace: site_colors = ["#003DA5", ...]
# With: (use SITE_PALETTE directly)

# Replace: pcolor = "#c0392b" if t.priority == 1 else "#e67e22"
# With: pcolor = PRIORITY_COLORS.get(t.priority, "#7f8c8d")
```

**scheduler_page.py:**
```python
from scripts.gui.ui_theme import STATUS_BG_COLORS

# Replace: _STATUS_BG = { "in progress": "#D6EAF8", ... }
# With: (use STATUS_BG_COLORS directly, with fallback)
```

**gantt_page.py:**
```python
from scripts.gui.ui_theme import GANTT_COLORS_DARK

# Replace hardcoded fallback strings in self._dk() calls
# with lookups from GANTT_COLORS_DARK
```

---

## Acceptance Criteria

1. All priority color dicts reference `PRIORITY_COLORS` from `ui_theme.py`
2. Site distribution palette references `SITE_PALETTE` from `ui_theme.py`
3. Scheduler status backgrounds reference `STATUS_BG_COLORS` from `ui_theme.py`
4. Gantt dark-mode fallbacks reference `GANTT_COLORS_DARK` from `ui_theme.py`
5. No hardcoded hex color values remain in dashboard, scheduler, or gantt pages (except button colors — those can stay in theme.json too, but are not required for this task)
6. All colors are visually identical (same hex values, just moved to centralized location)
7. `pytest tests/` passes

---

## Constraints

- Button colors in `tasks_page.py` can be left as-is (they're one-off UI styling) unless trivially centralizable
- Do NOT change any color values — this is purely a move from inline to centralized
- Provide reasonable defaults in `ui_theme.py` so the app works even if `theme.json` is missing a key
- The gantt page's `_dk()` helper method can stay — just update its fallback lookup to use the centralized dict
