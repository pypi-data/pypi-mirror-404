"""
Backward compatibility stub for cli.debug module.

This module has been migrated to cli.commands.development.debug.
Imports are lazy to avoid circular dependencies.
"""

# Lazy imports to avoid circular dependencies
# These can be imported directly from their respective submodules

__all__ = [
    "_debug",
    "gdb_debug",
    "get_net_cache",
    "DebugNetCache",
    "DebugServiceClient",
    "ServiceTunnel",
    "is_service_available",
    "ensure_service_tunnel",
    "cleanup_tunnels",
    "serve_tunnel",
]


def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name == "_debug":
        from ..commands.development.debug.commands import _debug
        return _debug
    elif name == "gdb_debug":
        from ..commands.development.debug.gdb import debug as gdb_debug
        return gdb_debug
    elif name in ("get_net_cache", "DebugNetCache"):
        from ..commands.development.debug import net_cache
        return getattr(net_cache, name)
    elif name == "DebugServiceClient":
        from ..commands.development.debug.service_client import DebugServiceClient
        return DebugServiceClient
    elif name in ("ServiceTunnel", "is_service_available", "ensure_service_tunnel", "cleanup_tunnels"):
        from ..commands.development.debug import service_helper
        return getattr(service_helper, name)
    elif name == "serve_tunnel":
        from ..commands.development.debug.tunnel import serve_tunnel
        return serve_tunnel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
