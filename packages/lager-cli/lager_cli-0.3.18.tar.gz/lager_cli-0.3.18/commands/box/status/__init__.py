"""
Status module - Status monitoring interfaces for lager-cli.

This package provides multiple interfaces for monitoring box status:
- CLI commands: lager status, lager status tui
- TUI: Terminal-based interactive status dashboard
- GUI: Graphical status dashboard using tkinter

Usage:
    lager status                  # Show status of all boxes
    lager status --box <name>     # Show status of specific box
    lager status tui              # Launch interactive TUI
"""

from .commands import status

__all__ = [
    "status",
]
