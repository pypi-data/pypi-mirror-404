"""
Debug Service Helper

Backward compatibility stub - module has been migrated to cli.commands.development.debug.service_helper

All exports are re-exported from the new location for backward compatibility.
"""
# Re-export everything from the new location
from ..commands.development.debug.service_helper import (
    ServiceTunnel,
    is_service_available,
    ensure_service_tunnel,
    cleanup_tunnels,
)

__all__ = [
    "ServiceTunnel",
    "is_service_available",
    "ensure_service_tunnel",
    "cleanup_tunnels",
]
