"""
Lager Debug Service Client

Backward compatibility stub - module has been migrated to cli.commands.development.debug.service_client

All exports are re-exported from the new location for backward compatibility.
"""
# Re-export everything from the new location
from ..commands.development.debug.service_client import (
    DebugServiceClient,
)

__all__ = [
    "DebugServiceClient",
]
