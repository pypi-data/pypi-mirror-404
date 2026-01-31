"""
    lager.debug.gdb

    Backward compatibility stub - module has been migrated to cli.commands.development.debug.gdb

    All exports are re-exported from the new location for backward compatibility.
"""
# Re-export everything from the new location
from ..commands.development.debug.gdb import (
    debug,
    PathResolutionError,
    zip_files,
    get_comp_dir,
    line_entry_mapping,
    lpe_filename,
    collect_filenames,
    remove_source_link,
    sha256sum,
    SOURCE_LINK,
)

__all__ = [
    "debug",
    "PathResolutionError",
    "zip_files",
    "get_comp_dir",
    "line_entry_mapping",
    "lpe_filename",
    "collect_filenames",
    "remove_source_link",
    "sha256sum",
    "SOURCE_LINK",
]
