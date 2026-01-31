"""
Enhanced Status TUI implementation with multi-box support, tabs, and activity log
"""
from __future__ import annotations

import time
import json
import io
import os
from contextlib import redirect_stdout
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import click

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, Label, TabbedContent, TabPane, Log, Tree, TextArea, Button
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.reactive import reactive


@dataclass
class BoxInfo:
    """Box information structure with usage tracking"""
    box_id: str
    status: str = "Unknown"
    response_time: float = 0.0
    nets_count: int = 0
    last_seen: str = "Unknown"
    nets: list = None
    locked_by: Optional[str] = None
    lock_status: str = "Available"
    session_duration: Optional[str] = None
    usage_history: list = None
    last_user: Optional[str] = None
    
    def __post_init__(self):
        if self.nets is None:
            self.nets = []
        if self.usage_history is None:
            self.usage_history = []


class EnhancedStatusApp(App):
    """Enhanced Status TUI with multi-box support and detailed information"""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("a", "toggle_auto_refresh", "Toggle Auto-refresh"),
        Binding("tab", "next_tab", "Next Tab"),
        Binding("shift+tab", "previous_tab", "Previous Tab"),
        Binding("up,down", "navigate_table", "Navigate"),
    ]
    
    CSS = """
    .status-online { color: green; }
    .status-offline { color: red; }
    .status-error { color: yellow; }
    .status-unlocked { color: green; }
    .status-locked { color: red; }
    
    #left_panel {
        width: 40%;
        border: solid $primary;
        margin: 1;
    }
    
    #right_panel {
        width: 60%;
        border: solid $secondary;
        margin: 1;
    }
    
    #overview_table {
        height: 80%;
        width: 100%;
    }
    
    #usage_history_table {
        height: 20;
        width: 100%;
    }
    
    #nets_table {
        height: 20;
        width: 100%;
    }
    
    #activity_log {
        height: 20;
        width: 100%;
    }
    
    #summary_stats {
        height: 3;
        margin: 1 0;
    }
    
    DataTable {
        width: 100%;
    }
    """
    
    selected_box = reactive(None)
    auto_refresh_enabled = reactive(True)

    def __init__(self, ctx, target_box, refresh_interval):
        super().__init__()
        self.ctx = ctx
        self.target_box = target_box
        self.refresh_interval = refresh_interval
        self.box_data: Dict[str, BoxInfo] = {}
        self.selected_box = target_box  # Will be set to first box after data load
        self.auto_refresh_enabled = True
        
    def compose(self) -> ComposeResult:
        yield Header()
        
        # Title with user information
        title = f"Lager Status Dashboard - Multi-Box Monitoring"
        yield Static(title, id="title")

        # Summary statistics
        self.summary_stats = Static("Loading...", id="summary_stats")
        yield self.summary_stats

        # Main layout: Left panel (box overview) + Right panel (Details)
        with Horizontal():
            # Left Panel: Multi-Box Overview
            with Vertical(id="left_panel"):
                yield Label("All Boxes")
                self.overview_table = DataTable(id="overview_table", zebra_stripes=True)
                self.overview_table.add_columns(
                    "Box Name", "Status", "Lock Status", "Response", "Nets", "Last User"
                )
                yield self.overview_table

            # Right Panel: Selected Box Details with Tabs
            with Vertical(id="right_panel"):
                self.selected_box_label = Label("Select a box for details")
                yield self.selected_box_label
                
                with TabbedContent(initial="usage_history"):
                    # Usage History Tab
                    with TabPane("Usage History", id="usage_history"):
                        yield Label("Current Status")
                        self.current_status = Static("Status: Unlocked\nNo active session", id="current_status")
                        yield self.current_status
                        
                        yield Label("Usage History")
                        self.usage_history_table = DataTable(id="usage_history_table")
                        self.usage_history_table.add_columns("Timestamp", "User", "Action", "Duration")
                        yield self.usage_history_table
                    
                    # Nets Tab
                    with TabPane("Nets", id="nets"):
                        yield Label("Network Connections")
                        self.nets_table = DataTable(id="nets_table", zebra_stripes=True)
                        self.nets_table.add_columns("Net Name", "Type", "Instrument", "Channel", "Status")
                        yield self.nets_table
                    
                    # Activity Log Tab
                    with TabPane("Activity Log", id="activity_log_tab"):
                        yield Label("System Activity")
                        self.activity_log = Log(id="activity_log", highlight=True)
                        yield self.activity_log

        yield Footer()
    
    def on_mount(self):
        """Initialize the application"""
        self.log_activity("Status Dashboard Started", "info")
        self.refresh_all_data()
        if self.auto_refresh_enabled:
            self.set_interval(self.refresh_interval, self.refresh_all_data)
        
        # Set up table selection handling
        self.overview_table.cursor_type = "row"
        
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in overview table"""
        if event.data_table == self.overview_table:
            row_key = event.row_key
            if row_key and row_key.value in self.box_data:
                self.selected_box = row_key.value
                self.update_selected_box_details()
                self.log_activity(f"Selected box {self.selected_box}", "info")

    
    def refresh_all_data(self):
        """Refresh all data for all boxes"""
        try:
            self.log_activity("Refreshing data for all boxes...", "info")

            # Import box listing functionality
            from ..box_storage import list_boxes

            # Get all configured boxes
            boxes = list_boxes()

            if not boxes:
                self.log_activity("No boxes configured in .lager file", "warning")
                return

            # Process each configured box
            for box_name, box_info in boxes.items():
                # Handle both string (IP only) and dict formats
                if isinstance(box_info, dict):
                    box_ip = box_info.get('ip', box_info.get('address', 'unknown'))
                else:
                    box_ip = box_info

                if box_ip == 'unknown':
                    continue

                # Use the IP address for connectivity checking
                box_data = self.fetch_box_data(box_ip)
                # But use the box name for display
                box_data.box_id = box_name
                self.box_data[box_name] = box_data

            self.update_overview_table()
            self.update_summary_stats()

            # Auto-select first box if none is selected
            if not self.selected_box and self.box_data:
                self.selected_box = list(self.box_data.keys())[0]
                self.log_activity(f"Auto-selected box {self.selected_box}", "info")

            if self.selected_box:
                self.update_selected_box_details()

            self.log_activity("Data refresh completed successfully", "success")
            
        except Exception as e:
            self.log_activity(f"Error refreshing data: {e}", "error")
    
    def fetch_box_data(self, box_id: str) -> BoxInfo:
        """Fetch comprehensive data for a single box"""
        # Use the same connectivity check as the main status command
        from .commands import _check_box_connectivity

        # Check box connectivity using the fixed function
        connectivity_result = _check_box_connectivity(box_id)
        status = connectivity_result['status']
        response_time = connectivity_result['response_time'] / 1000.0  # Convert ms to seconds

        # Get nets data (only if box is online)
        if status == "Online":
            from .commands import _get_box_nets
            nets_info = _get_box_nets(self.ctx, box_id)
            nets_data = nets_info.get('nets', [])
        else:
            nets_data = []

        # Get current user information
        try:
            current_user = self._get_current_user()
        except Exception:
            current_user = "unknown@user.com"

        return BoxInfo(
            box_id=box_id,
            status=status,
            response_time=response_time,
            nets_count=len(nets_data),
            last_seen=time.strftime("%H:%M:%S"),
            nets=nets_data,
            locked_by=None,  # Would come from real API
            lock_status="Unlocked",
            session_duration=None,
            usage_history=[],  # Would come from real API
            last_user=current_user
        )
    
    def _parse_backend_json(self, raw: str):
        """
        Parse JSON response from backend, handling duplicate output from double execution.

        Args:
            raw: Raw output from backend

        Returns:
            Parsed JSON data

        Raises:
            json.JSONDecodeError: If JSON cannot be parsed
        """
        try:
            return json.loads(raw or "[]")
        except json.JSONDecodeError:
            # Handle duplicate JSON output from backend double execution
            if raw and raw.count('[') >= 2:
                # Try to extract the first JSON array
                depth = 0
                first_array_end = -1
                for i, char in enumerate(raw):
                    if char == '[':
                        depth += 1
                    elif char == ']':
                        depth -= 1
                        if depth == 0:
                            first_array_end = i + 1
                            break

                if first_array_end > 0:
                    first_json = raw[:first_array_end]
                    return json.loads(first_json)
                else:
                    raise json.JSONDecodeError("Could not find complete JSON array", raw, 0)
            else:
                # Handle duplicate JSON objects (e.g., {"ok": true}{"ok": true})
                if raw and raw.count('{') >= 2:
                    depth = 0
                    first_obj_end = -1
                    for i, char in enumerate(raw):
                        if char == '{':
                            depth += 1
                        elif char == '}':
                            depth -= 1
                            if depth == 0:
                                first_obj_end = i + 1
                                break

                    if first_obj_end > 0:
                        first_json = raw[:first_obj_end]
                        return json.loads(first_json)

                raise  # Re-raise original exception

    def _get_current_user(self):
        """Get current user information (direct mode - no cloud auth)"""
        # In direct connection mode, there's no cloud authentication
        # Return None to indicate local/direct connection
        return None
    
    def update_overview_table(self):
        """Update the multi-box overview table"""
        try:
            self.overview_table.clear()

            for box_id, box_info in self.box_data.items():
                response_str = f"{box_info.response_time:.3f}s" if box_info.response_time < 999 else "Timeout"

                # Apply status styling
                status_class = f"status-{box_info.status.lower()}"
                lock_class = f"status-{box_info.lock_status.lower()}"

                self.overview_table.add_row(
                    box_info.box_id,
                    f"[{status_class}]{box_info.status}[/{status_class}]",
                    f"[{lock_class}]{box_info.lock_status}[/{lock_class}]",
                    response_str,
                    str(box_info.nets_count),
                    box_info.last_user or "Unknown",
                    key=box_id
                )

        except Exception as e:
            self.log_activity(f"Error updating overview table: {e}", "error")
    
    def update_summary_stats(self):
        """Update the summary statistics"""
        try:
            online_count = sum(1 for box in self.box_data.values() if box.status == "Online")
            total_nets = sum(box.nets_count for box in self.box_data.values())

            current_user = list(self.box_data.values())[0].last_user if self.box_data else "Unknown"

            summary = (
                f"Boxes: {online_count}/{len(self.box_data)} online | "
                f"Total Nets: {total_nets} | "
                f"User: {current_user} | "
                f"Auto-refresh: {'ON' if self.auto_refresh_enabled else 'OFF'} ({self.refresh_interval}s) | "
                f"Last Update: {time.strftime('%H:%M:%S')}"
            )

            self.summary_stats.update(summary)

        except Exception as e:
            self.log_activity(f"Error updating summary: {e}", "error")
    
    def update_selected_box_details(self):
        """Update the details panel for selected box"""
        if not self.selected_box or self.selected_box not in self.box_data:
            self.selected_box_label.update("Select a box for details")
            return

        box_info = self.box_data[self.selected_box]
        header_text = f"Box {self.selected_box} Details"
        if box_info.lock_status != "Unlocked":
            header_text += f" - {box_info.lock_status}"

        self.selected_box_label.update(header_text)

        # Update current status
        if box_info.locked_by:
            status_text = f"Status: Locked by {box_info.locked_by}\nSession duration: {box_info.session_duration or 'Unknown'}"
        else:
            status_text = f"Status: Unlocked\nNo active session"

        self.current_status.update(status_text)

        # Update usage history table
        self.usage_history_table.clear()
        for entry in box_info.usage_history:
            self.usage_history_table.add_row(
                entry.get('timestamp', ''),
                entry.get('user', ''),
                entry.get('action', ''),
                entry.get('duration', '')
            )

        # Update nets table
        self.nets_table.clear()
        for net in box_info.nets:
            net_status = "Active" if box_info.status == "Online" else "Unknown"
            self.nets_table.add_row(
                net.get("name", "Unknown"),
                net.get("role", "Unknown"),
                net.get("instrument", "None"),
                net.get("pin", "N/A"),
                f"[status-{net_status.lower()}]{net_status}[/status-{net_status.lower()}]"
            )

    
    def log_activity(self, message: str, level: str = "info"):
        """Add message to activity log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")

        # Simple message format without styling
        plain_message = f"[{timestamp}] {message}"

        try:
            # Use write_line() method to add entries on new lines
            self.activity_log.write_line(plain_message)
        except Exception:
            # Fallback - use write with manual newline
            self.activity_log.write(f"{plain_message}\n")






    
    def old_refresh_data(self):
        """Legacy refresh method - kept for compatibility"""
        current_time = time.strftime("%H:%M:%S")
        try:
            if self.target_box:
                # Legacy compatibility - now uses new methods
                pass
            else:
                # Multi-box mode is now implemented
                pass

        except Exception as e:
            self.log_activity(f"Refresh error: {str(e)}", "error")

    def _check_box_status(self, box_id):
        """Check box status with minimal error handling"""
        try:
            session = self.ctx.obj.session
            start_time = time.time()
            resp = session.gateway_hello(box_id)
            response_time = time.time() - start_time

            if resp.status_code == 200:
                return {'status': 'Online', 'response': response_time}
            else:
                return {'status': 'Error', 'response': response_time}
        except Exception:
            return {'status': 'Offline', 'response': 999.0}

    def _get_nets_data(self, box_id):
        """Get nets data for box using the same method as nets command"""
        print(f"Getting nets data for box: {box_id}")
        try:
            import json
            import io
            from contextlib import redirect_stdout
            from ..context import get_impl_path
            from ..commands.development.python import run_python_internal

            print("Running net.py...")
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    run_python_internal(
                        self.ctx, get_impl_path("net.py"), box_id,
                        image="", env={}, passenv=(), kill=False, download=(),
                        allow_overwrite=False, signum="SIGTERM", timeout=0,
                        detach=False, port=(), org=None, args=("list",)
                    )
            except SystemExit:
                # This is expected - net.py raises SystemExit
                pass

            raw_output = buf.getvalue()
            print(f"Raw output: '{raw_output}'")
            nets_data = self._parse_backend_json(raw_output or "[]")
            print(f"Found {len(nets_data)} nets: {nets_data}")
            return nets_data
        except Exception as e:
            print(f"Error getting nets data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def action_refresh(self) -> None:
        """Manual refresh action"""
        self.log_activity("Manual refresh triggered", "info")
        self.refresh_all_data()
    
    def action_toggle_auto_refresh(self) -> None:
        """Toggle auto-refresh on/off"""
        self.auto_refresh_enabled = not self.auto_refresh_enabled
        if self.auto_refresh_enabled:
            self.set_interval(self.refresh_interval, self.refresh_all_data)
            self.log_activity("Auto-refresh enabled", "success")
        else:
            # Cancel interval (Textual handles this automatically)
            self.log_activity("Auto-refresh disabled", "warning")
        
        # Update summary to reflect change
        self.update_summary_stats()
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.log_activity("Shutting down Status Dashboard", "info")
        self.exit()


def launch_status_tui(ctx: click.Context, target_box: Optional[str], refresh_interval: float = 10.0) -> None:
    """Launch the enhanced status TUI with comprehensive error handling"""
    from ..box_storage import get_box_ip

    # Resolve local box if provided
    if target_box:
        local_ip = get_box_ip(target_box)
        if local_ip:
            target_box = local_ip

    try:
        app = EnhancedStatusApp(ctx, target_box, refresh_interval)
        app.run()
    except KeyboardInterrupt:
        print("\nStatus TUI interrupted by user")
    except Exception as e:
        print(f"Error launching Enhanced Status TUI: {e}")
        import traceback
        traceback.print_exc()

        print("\nFalling back to basic mode...")
        input("Press Enter to continue...")

        # Fallback to basic TUI
        try:
            from textual.app import App
            from textual.widgets import Static, DataTable, Label
            from textual.containers import Container

            class FallbackStatusApp(App):
                def compose(self):
                    yield Header()
                    yield Static("Lager Status TUI - Fallback Mode")
                    yield Static(f"Target Box: {target_box or 'All'}")

                    with Container():
                        yield Label("Enhanced features unavailable")
                        yield Label("Basic status information:")

                        self.status_info = Static("Checking status...")
                        yield self.status_info

                        yield Static("\nControls: Press 'r' to refresh, 'q' to quit")

                    yield Footer()

                def on_mount(self):
                    self.refresh_basic_status()
                    self.set_interval(refresh_interval, self.refresh_basic_status)

                def refresh_basic_status(self):
                    try:
                        if target_box:
                            session = ctx.obj.session
                            resp = session.gateway_hello(target_box)
                            if resp.status_code == 200:
                                status = "Online"
                            else:
                                status = "Error"
                        else:
                            status = "Multi-box mode"

                        current_time = time.strftime("%H:%M:%S")
                        info = f"Status: {status}\nLast check: {current_time}\nRefresh interval: {refresh_interval}s"
                        self.status_info.update(info)

                    except Exception as e:
                        self.status_info.update(f"Status check failed: {e}")

                def action_refresh(self):
                    self.refresh_basic_status()

                def action_quit(self):
                    self.exit()

                BINDINGS = [
                    ("q", "quit", "Quit"),
                    ("r", "refresh", "Refresh"),
                ]

            fallback_app = FallbackStatusApp()
            fallback_app.run()

        except Exception as e2:
            print(f"Even fallback TUI failed: {e2}")
            print("Try using --ui=gui for graphical interface")
            print("Contact support if the issue persists")