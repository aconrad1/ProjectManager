"""helpers.config — JSON-driven configuration for the GUI and domain layer.

All data-driven constants (status values, categories, field mappings,
theme colours, deadline thresholds) live as JSON files in this package
and are loaded via :func:`load`.
"""

from __future__ import annotations

from helpers.config.loader import load, load_field_map, load_reverse_field_map  # noqa: F401
