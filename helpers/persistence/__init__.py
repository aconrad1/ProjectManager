"""helpers.persistence — adapters for loading/saving domain objects."""

from __future__ import annotations

from helpers.persistence.workbook_reader import load_profile_from_workbook  # noqa: F401
from helpers.persistence.workbook_writer import (                            # noqa: F401
    save_profile_to_workbook,
    add_project_row, add_task_row, add_deliverable_row,
    update_project_row, update_task_row, update_deliverable_row,
    delete_row_by_id,
)
from helpers.persistence.serializer import (                                 # noqa: F401
    serialize_profile, deserialize_profile,
    save_profile_json, load_profile_json, hash_file,
)
from helpers.persistence.contract import (                                   # noqa: F401
    load_profile, save, sync,
    push_to_workbook, import_from_workbook, resync_json,
    domain_json_path,
)
from helpers.persistence.field_map import (                                   # noqa: F401
    fields_to_attrs, attrs_to_fields, normalize_to_attrs,
)

