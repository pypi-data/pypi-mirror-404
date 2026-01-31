"""
Net GUI implementation using tkinter (cross-platform, built-in)
Provides visual interface for network management similar to the TUI
"""
from __future__ import annotations

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog
    # Test if tkinter actually works
    test_root = tk.Tk()
    test_root.withdraw()  # Hide the test window
    test_root.destroy()
    TKINTER_AVAILABLE = True
except (ImportError, Exception):
    TKINTER_AVAILABLE = False
    tk = None
    ttk = None
    messagebox = None
    simpledialog = None

import threading
import time
import json
import io
import re
from contextlib import redirect_stdout
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from collections import defaultdict

import click

# ────────────────────────── Lager helpers ───────────────────────────
from ..context import get_impl_path
from ..commands.development.python import run_python_internal

# ──────────────── helpers / model ─────────────────

def _parse_backend_json_gui(raw: str):
    """Parse JSON response from backend, handling duplicate output from double execution."""
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

def _uid(instr: str, chan: str, role: str, name: str) -> str:
    """Return a row-key that is unique for (instrument, channel, role, name)."""
    base = f"{instr}_{chan}_{role}_{name}".replace(" ", "_")
    safe = "".join(c if re.fullmatch(r"[A-Za-z0-9_-]", c) else "_" for c in base)
    return f"_{safe}" if safe and safe[0].isdigit() else safe

_MULTI_HUBS = {"LabJack_T7", "Acroname_8Port", "Acroname_4Port"}
_SINGLE_CHANNEL_INST = {
    "Keithley_2281S": ("batt", "supply"),
    "EA_PSB_10060_60": ("solar", "supply"),
    "EA_PSB_10080_60": ("solar", "supply"),
}

def _first_word(role: str) -> str:
    """Return the first part of a hyphenated role name."""
    return role.split("-")[0]

# Common kwargs for run_python_internal calls
_RUN_PYTHON_KWARGS = {
    "image": "",
    "env": {},
    "passenv": (),
    "kill": False,
    "download": (),
    "allow_overwrite": False,
    "signum": "SIGTERM",
    "timeout": 0,
    "detach": False,
    "port": (),
    "org": None,
}

def _run_script(ctx: click.Context, script: str, dut: str, *args) -> str:
    """Execute an internal script with given arguments and capture stdout."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            run_python_internal(ctx, get_impl_path(script), dut, **_RUN_PYTHON_KWARGS, args=args)
    except SystemExit:
        pass
    return buf.getvalue()

def _save_nets_batch(ctx: click.Context, dut: str, nets: list["Net"]) -> bool:
    """Save multiple nets using batch save with fallback to individual saves."""
    if not nets:
        return True

    nets_data = []
    for n in nets:
        nets_data.append({
            "name": n.net,
            "role": n.type,
            "address": n.addr,
            "instrument": n.instrument,
            "pin": n.chan,
        })

    # Try batch save first
    try:
        raw = _run_script(ctx, "net.py", dut, "save-batch", json.dumps(nets_data))

        if raw and raw.strip():
            # Use the same JSON parsing logic as the CLI to handle duplicate output
            response = _parse_backend_json_gui(raw)
            if response.get("ok", False):
                return True
    except (json.JSONDecodeError, Exception):
        pass  # Fall through to individual saves

    # Fallback to individual saves (batch save failed or returned empty)
    saved_count = 0
    for n in nets:
        try:
            _run_script(ctx, "net.py", dut, "save", json.dumps({
                "name": n.net,
                "role": n.type,
                "address": n.addr,
                "instrument": n.instrument,
                "pin": n.chan,
            }))
            saved_count += 1
        except Exception:
            pass  # Continue trying to save other nets

    return saved_count > 0

def is_single_channel_taken(all_nets: list["Net"], inst: str, addr: str) -> bool:
    """
    True if a *saved* net for this "single-channel" instrument+address
    already exists (Keithley 2281S, EA PSB models, …).
    """
    if inst not in _SINGLE_CHANNEL_INST:
        return False
    return any(n.saved and n.instrument == inst and n.addr == addr for n in all_nets)

@dataclass
class Net:
    instrument: str
    chan: str
    type: str
    net: str
    addr: str
    saved: bool = False

    def __post_init__(self) -> None:
        self._uid = _uid(self.instrument, self.chan, self.type, self.net)

    def key(self) -> str:
        return self._uid

class NetGUI:
    """Net Manager GUI application"""

    def __init__(self, ctx, dut: str):
        self.ctx = ctx
        self.dut = dut
        self.nets: List[Net] = []
        self.inst_list: List[Dict[str, Any]] = []

        # Create main window
        self.root = tk.Tk()
        self.root.title(f"Lager Net Manager - DUT {dut}")
        self.root.geometry("1400x900")  # Larger window for better layout
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.minsize(1000, 700)  # Minimum window size

        # Enhanced Lager color scheme matching status GUI
        self.colors = {
            'bg_dark': '#1e1e1e',
            'bg_light': '#2d2d2d',
            'bg_card': '#3a3a3a',
            'accent': '#ff69b4',       # Lager pink
            'accent_hover': '#ff1493',
            'text_primary': '#ffffff',
            'text_secondary': '#cccccc',
            'text_muted': '#999999',
            'success': '#28a745',
            'error': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'border': '#555555',
            'header_bg': '#2a2a2a'
        }

        # Configure root window
        self.root.configure(bg=self.colors['bg_dark'])

        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configure custom styles for Lager theme
        self.configure_styles()

        self.setup_ui()

        # Initialize data - but don't let errors crash the GUI
        try:
            self.refresh_data()
        except Exception as e:
            print(f"Warning: Initial data refresh failed: {e}")
            # Set some default data so GUI still works
            self.nets = []
            self.inst_list = []
            self.status_var.set(f"Error loading data: {str(e)[:50]}...")

    def configure_styles(self):
        """Configure custom ttk styles for Lager theme"""
        # Configure frame styles
        self.style.configure('Dark.TFrame',
                           background=self.colors['bg_dark'])
        self.style.configure('Card.TFrame',
                           background=self.colors['bg_card'],
                           relief='flat',
                           borderwidth=1)

        # Configure label styles
        self.style.configure('Title.TLabel',
                           background=self.colors['bg_dark'],
                           foreground=self.colors['text_primary'],
                           font=('Segoe UI', 22, 'bold'))
        self.style.configure('Header.TLabel',
                           background=self.colors['bg_card'],
                           foreground=self.colors['accent'],
                           font=('Segoe UI', 13, 'bold'))
        self.style.configure('Dark.TLabel',
                           background=self.colors['bg_dark'],
                           foreground=self.colors['text_primary'],
                           font=('Segoe UI', 10))
        self.style.configure('Card.TLabel',
                           background=self.colors['bg_card'],
                           foreground=self.colors['text_primary'],
                           font=('Segoe UI', 10))
        self.style.configure('Subtitle.TLabel',
                           background=self.colors['bg_dark'],
                           foreground=self.colors['text_secondary'],
                           font=('Segoe UI', 11))

        # Configure button styles
        self.style.configure('Accent.TButton',
                           background=self.colors['accent'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           font=('Segoe UI', 10, 'bold'),
                           padding=(15, 8))
        self.style.map('Accent.TButton',
                     background=[('active', self.colors['accent_hover']),
                               ('pressed', self.colors['accent_hover'])])

        self.style.configure('Success.TButton',
                           background=self.colors['success'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           font=('Segoe UI', 10, 'bold'),
                           padding=(15, 8))

        self.style.configure('Error.TButton',
                           background=self.colors['error'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           font=('Segoe UI', 10, 'bold'),
                           padding=(15, 8))

        # Configure notebook styles
        self.style.configure('Dark.TNotebook',
                           background=self.colors['bg_card'],
                           borderwidth=0)
        self.style.configure('Dark.TNotebook.Tab',
                           background=self.colors['bg_light'],
                           foreground=self.colors['text_primary'],
                           padding=[20, 8])
        self.style.map('Dark.TNotebook.Tab',
                     background=[('selected', self.colors['accent']),
                               ('active', self.colors['bg_card'])])

        # Configure treeview styles
        self.style.configure('Dark.Treeview',
                           background=self.colors['bg_light'],
                           foreground=self.colors['text_primary'],
                           fieldbackground=self.colors['bg_light'],
                           borderwidth=1,
                           relief='solid',
                           font=('Segoe UI', 10),
                           rowheight=28)
        self.style.configure('Dark.Treeview.Heading',
                           background=self.colors['header_bg'],
                           foreground=self.colors['text_primary'],
                           borderwidth=1,
                           relief='solid',
                           font=('Segoe UI', 10, 'bold'))
        self.style.map('Dark.Treeview',
                     background=[('selected', self.colors['accent']),
                               ('focus', self.colors['accent'])],
                     foreground=[('selected', 'white'),
                               ('focus', 'white')])

    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding="25")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Header section
        header_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        header_frame.columnconfigure(1, weight=1)

        # Try to load and display Lager logo
        logo_loaded = False
        try:
            import os
            import sys

            # Try multiple paths to find the logo
            possible_paths = [
                "assets/logo.png",  # Relative to current working directory
                "/Users/danielerskine/Desktop/LagerData/Internship2025/lager-cli/assets/logo.png",  # Absolute path
            ]

            # Also try relative to the module file
            try:
                module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                project_root = os.path.dirname(module_dir)
                possible_paths.append(os.path.join(project_root, 'assets', 'logo.png'))
            except:
                pass

            # Try bundled executable path
            if hasattr(sys, '_MEIPASS'):
                possible_paths.insert(0, os.path.join(sys._MEIPASS, 'assets', 'logo.png'))

            logo_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    logo_path = path
                    break

            if logo_path:
                self.logo_photo = tk.PhotoImage(file=logo_path)
                # Subsample the image to make it smaller (since PhotoImage doesn't have resize)
                self.logo_photo = self.logo_photo.subsample(4, 4)  # Reduce size
                logo_label = ttk.Label(header_frame, image=self.logo_photo, style='Dark.TLabel')
                logo_label.grid(row=0, column=0, padx=(0, 15))
                logo_loaded = True
        except Exception as e:
            pass

        if not logo_loaded:
            # Fallback: Pink square to match Lager branding
            logo_canvas = tk.Canvas(header_frame, width=60, height=60,
                                  bg=self.colors['accent'], highlightthickness=0)
            logo_canvas.grid(row=0, column=0, padx=(0, 15))

        # Title and subtitle
        title_frame = ttk.Frame(header_frame, style='Dark.TFrame')
        title_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))

        title_label = ttk.Label(title_frame, text="Lager Net Manager", style='Title.TLabel')
        title_label.pack(anchor=tk.W)

        subtitle_label = ttk.Label(title_frame,
                                 text=f"DUT {self.dut} • Net Configuration Dashboard",
                                 style='Subtitle.TLabel')
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))

        # Control buttons
        control_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))

        self.refresh_btn = ttk.Button(control_frame, text="Refresh",
                                     style='Accent.TButton',
                                     command=self.refresh_data)
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.add_all_nets_btn = ttk.Button(control_frame, text="Add All Nets",
                                          style='Success.TButton',
                                          command=self.add_all_nets)
        self.add_all_nets_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.delete_all_btn = ttk.Button(control_frame, text="Delete All Nets",
                                        style='Error.TButton',
                                        command=self.delete_all_nets)
        self.delete_all_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Status label
        self.status_var = tk.StringVar(value="Initializing...")
        status_label = ttk.Label(control_frame, textvariable=self.status_var,
                               style='Dark.TLabel', font=('Segoe UI', 10, 'italic'))
        status_label.pack(side=tk.RIGHT)

        # Main content area - notebook with tabs
        content_frame = ttk.Frame(main_frame, style='Card.TFrame', padding="15")
        content_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(content_frame, style='Dark.TNotebook')
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Setup tabs
        self.setup_saved_nets_tab()
        self.setup_add_nets_tab()

    def setup_saved_nets_tab(self):
        """Setup the saved nets tab"""
        # Create frame for saved nets
        saved_frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(saved_frame, text="Saved Nets")

        saved_frame.columnconfigure(0, weight=1)
        saved_frame.rowconfigure(1, weight=1)

        # Table header
        table_header = ttk.Label(saved_frame, text="Saved Nets", style='Header.TLabel')
        table_header.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        # Create treeview for saved nets
        columns = ("name", "type", "instrument", "channel", "address")
        self.nets_tree = ttk.Treeview(saved_frame, columns=columns, show="headings",
                                    style='Dark.Treeview')

        # Configure columns
        column_configs = {
            "name": ("Net Name", 150),
            "type": ("Type", 100),
            "instrument": ("Instrument", 200),
            "channel": ("Channel", 100),
            "address": ("Address", 300)
        }

        for col, (heading, width) in column_configs.items():
            self.nets_tree.heading(col, text=heading)
            self.nets_tree.column(col, width=width, minwidth=width)

        # Scrollbar for nets table
        nets_scrollbar = ttk.Scrollbar(saved_frame, orient=tk.VERTICAL,
                                     command=self.nets_tree.yview)
        self.nets_tree.configure(yscrollcommand=nets_scrollbar.set)

        # Pack table and scrollbar
        self.nets_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        nets_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

        # Placeholder for empty state
        self.no_nets_label = ttk.Label(saved_frame, text="No saved nets found",
                                      style='Card.TLabel', font=('Segoe UI', 12, 'italic'))
        self.no_nets_label.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.no_nets_label.grid_remove()  # Hide initially

        # Context menu for nets
        self.setup_context_menu()

    def setup_add_nets_tab(self):
        """Setup the add nets tab"""
        # Create frame for add nets
        add_frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(add_frame, text="Add Nets")

        add_frame.columnconfigure(0, weight=1)
        add_frame.rowconfigure(1, weight=1)

        # Header
        header_frame = ttk.Frame(add_frame, style='Card.TFrame')
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(0, weight=1)

        table_header = ttk.Label(header_frame, text="Available Nets", style='Header.TLabel')
        table_header.grid(row=0, column=0, sticky=tk.W)

        # Add Nets button
        self.add_selected_btn = ttk.Button(header_frame, text="Add Selected Nets",
                                          style='Success.TButton',
                                          command=self.add_selected_nets_from_tab,
                                          state="disabled")  # Start disabled until nets are selected
        self.add_selected_btn.grid(row=0, column=1, sticky=tk.E)

        # Create treeview for available nets
        add_columns = ("select", "name", "type", "instrument", "channel", "address")
        self.available_tree = ttk.Treeview(add_frame, columns=add_columns, show="headings",
                                         style='Dark.Treeview')

        # Configure columns
        add_column_configs = {
            "select": ("Select", 80),
            "name": ("Name", 120),
            "type": ("Type", 80),
            "instrument": ("Instrument", 150),
            "channel": ("Channel", 80),
            "address": ("Address", 200)
        }

        for col, (heading, width) in add_column_configs.items():
            self.available_tree.heading(col, text=heading)
            self.available_tree.column(col, width=width, minwidth=width)

        # Scrollbar for available nets
        available_scrollbar = ttk.Scrollbar(add_frame, orient=tk.VERTICAL,
                                          command=self.available_tree.yview)
        self.available_tree.configure(yscrollcommand=available_scrollbar.set)

        # Pack table and scrollbar
        self.available_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        available_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

        # Bind selection event
        self.available_tree.bind('<Button-1>', self.on_available_tree_click)

        # Warning labels frame
        self.warnings_frame = ttk.Frame(add_frame, style='Card.TFrame')
        self.warnings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))


        # Initialize chosen set for tracking selections
        self.chosen: set[str] = set()

    def setup_context_menu(self):
        """Setup right-click context menu for nets"""
        self.context_menu = tk.Menu(self.root, tearoff=0,
                                   bg=self.colors['bg_card'],
                                   fg=self.colors['text_primary'],
                                   activebackground=self.colors['accent'],
                                   activeforeground='white')
        self.context_menu.add_command(label="Rename", command=self.rename_net)
        self.context_menu.add_command(label="Delete", command=self.delete_net)

        # Bind right-click to treeview
        self.nets_tree.bind("<Button-3>", self.show_context_menu)  # Right-click

    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Select the item that was right-clicked
        item = self.nets_tree.identify_row(event.y)
        if item:
            self.nets_tree.selection_set(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def refresh_data(self):
        """Refresh nets data from backend"""
        self.status_var.set("Refreshing...")
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.configure(state="disabled")

        try:
            # Get connected instruments and saved nets
            try:
                inst_result = _run_script(self.ctx, "query_instruments.py", self.dut)
                self.inst_list = json.loads(inst_result) if inst_result.strip() else []
            except (json.JSONDecodeError, AttributeError, Exception) as e:
                print(f"Warning: Could not get instruments: {e}")
                self.inst_list = []

            try:
                saved_result = _run_script(self.ctx, "net.py", self.dut, "list")
                saved_list = _parse_backend_json_gui(saved_result) if saved_result.strip() else []
            except (json.JSONDecodeError, AttributeError, Exception) as e:
                print(f"Warning: Could not get saved nets: {e}")
                saved_list = []

            # Update nets list
            self._update_nets_from_data(saved_list)

            # Refresh display
            self._refresh_nets_table()

            # If add nets tab exists and is currently visible, refresh it too
            if hasattr(self, 'available_tree') and self.notebook.index(self.notebook.select()) == 1:
                self.refresh_available_nets()

            self.status_var.set(f"Monitoring DUT {self.dut} - {len(saved_list)} saved nets")

        except Exception as e:
            error_msg = f"Error refreshing data: {str(e)}"
            print(f"GUI Error: {error_msg}")
            self.status_var.set(error_msg)
            # Don't show popup during initialization
            if hasattr(self, 'refresh_btn'):
                try:
                    messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")
                except:
                    pass  # In case messagebox fails too
        finally:
            if hasattr(self, 'refresh_btn'):
                try:
                    self.refresh_btn.configure(state="normal")
                except:
                    pass  # In case the button doesn't exist yet

    def _update_nets_from_data(self, saved_list):
        """Update internal nets list from backend data"""
        # Generate auto nets from instruments
        role_counter: dict[str, int] = defaultdict(int)
        self.nets: list[Net] = []

        for dev in self.inst_list:
            instr = dev.get("name", "Unknown")
            addr = dev.get("address", "NA")
            channel_map = dev.get("channels", {})
            for role, channels in (channel_map or {}).items():
                for ch in channels:
                    idx = role_counter.setdefault(role, 0) + 1
                    role_counter[role] = idx
                    auto_name = f"{_first_word(role)}{idx}"
                    self.nets.append(Net(instr, ch, role, auto_name, addr, saved=False))

        # Add saved nets
        for rec in saved_list:
            self.nets.append(Net(
                instrument=rec.get("instrument", "NA"),
                chan=rec.get("pin", "NA"),
                type=rec.get("role", "NA"),
                net=rec.get("name"),
                addr=rec.get("address", "NA"),
                saved=True,
            ))

    def _refresh_nets_table(self):
        """Refresh the nets table display"""
        # Clear existing data
        self.nets_tree.delete(*self.nets_tree.get_children())

        # Get saved nets only
        saved_nets = [n for n in self.nets if n.saved]

        if saved_nets:
            self.no_nets_label.grid_remove()
            self.nets_tree.grid()

            # Sort nets for display
            saved_nets.sort(key=lambda x: (x.instrument, x.net))

            # Populate table
            for net in saved_nets:
                self.nets_tree.insert('', tk.END, values=(
                    net.net,
                    net.type,
                    net.instrument,
                    net.chan,
                    net.addr
                ), tags=(net.key(),))
        else:
            self.nets_tree.grid_remove()
            self.no_nets_label.grid()

    def switch_to_add_nets_tab(self):
        """Switch to the Add Nets tab"""
        self.notebook.select(1)  # Select second tab (Add Nets)
        self.refresh_available_nets()

    def refresh_available_nets(self):
        """Refresh the available nets list"""
        remaining, warnings = self._get_addable_nets()

        # Clear existing data
        self.available_tree.delete(*self.available_tree.get_children())
        self.chosen.clear()

        # Clear warnings
        for widget in self.warnings_frame.winfo_children():
            widget.destroy()

        # Sort nets for display
        role_rank = {"adc": 0, "dac": 1, "gpio": 2, "batt": 3, "power-supply": 4}
        num_idx = re.compile(r"^([A-Za-z]+)(\d+)$").search

        def sort_key(n: Net) -> tuple:
            m = num_idx(n.net)
            return (
                n.instrument,
                role_rank.get(n.type, 99),
                m.group(1) if m else n.net,
                int(m.group(2)) if m else 0,
                n.net,
            )

        remaining.sort(key=sort_key)

        # Populate table
        for net in remaining:
            self.available_tree.insert('', tk.END, values=(
                "Add",
                net.net,
                net.type,
                net.instrument,
                net.chan,
                net.addr
            ), tags=(net.key(),))

        # Show warnings
        for warning in warnings:
            warning_label = ttk.Label(self.warnings_frame, text=f"{warning}",
                                    style='Card.TLabel',
                                    foreground=self.colors['warning'])
            warning_label.pack(anchor=tk.W, pady=(2, 0))

        # Show message if no nets available
        if not remaining:
            no_nets_label = ttk.Label(self.warnings_frame, text="No nets available to add",
                                    style='Card.TLabel',
                                    foreground=self.colors['text_muted'])
            no_nets_label.pack(anchor=tk.W, pady=(10, 0))

        # Update button state
        self.update_add_button_state()

    def on_available_tree_click(self, event):
        """Handle tree click for selection in add nets tab"""
        region = self.available_tree.identify("region", event.x, event.y)
        if region == "cell":
            # Get the item and column
            item = self.available_tree.identify_row(event.y)
            column = self.available_tree.identify_column(event.x)

            # Only handle clicks on the "Select" column
            if column == "#1" and item:  # First column is select
                key = self.available_tree.item(item)['tags'][0] if self.available_tree.item(item)['tags'] else None
                if key:
                    if key in self.chosen:
                        self.chosen.remove(key)
                        self.available_tree.set(item, "select", "Add")
                    else:
                        self.chosen.add(key)
                        self.available_tree.set(item, "select", "Added")

                # Update button state based on selections
                self.update_add_button_state()

    def update_add_button_state(self):
        """Update the Add Selected Nets button state based on current selections"""
        if hasattr(self, 'add_selected_btn'):
            if self.chosen:
                self.add_selected_btn.configure(state="normal")
                self.add_selected_btn.configure(text=f"Add Selected Nets ({len(self.chosen)})")
            else:
                self.add_selected_btn.configure(state="disabled")
                self.add_selected_btn.configure(text="Add Selected Nets")

    def add_all_nets(self):
        """Add all available nets"""
        remaining, warnings = self._get_addable_nets()

        if not remaining:
            messagebox.showinfo("No Nets", "No nets available to add.")
            return

        # Confirm adding all nets
        if not messagebox.askyesno("Add All Nets",
                                  f"Add all {len(remaining)} available nets to DUT {self.dut}?"):
            return

        # Separate debug and normal nets
        debug_nets = [n for n in remaining if n.type == "debug"]
        normal_nets = [n for n in remaining if n.type != "debug"]

        # Handle debug nets - prompt for device type
        if debug_nets:
            for net in debug_nets:
                device_type = simpledialog.askstring(
                    "J-Link Device Type",
                    f"Enter device type for debug net on {net.instrument} at {net.addr}:"
                )
                if device_type:
                    net.chan = device_type
                else:
                    messagebox.showinfo("Cancelled", "Debug net configuration cancelled.")
                    return

        try:
            # Save all nets
            all_nets_to_save = normal_nets + debug_nets
            if _save_nets_batch(self.ctx, self.dut, all_nets_to_save):
                self.refresh_data()
                self.refresh_available_nets()
                # Switch back to saved nets tab
                self.notebook.select(0)
                messagebox.showinfo("Success", f"Added {len(all_nets_to_save)} nets successfully.")
            else:
                messagebox.showerror("Error", "Failed to save some nets.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add nets: {str(e)}")

    def add_selected_nets_from_tab(self):
        """Add selected nets from the add nets tab"""
        if not self.chosen:
            messagebox.showwarning("No Selection", "Please select nets to add.")
            return

        # Collect selected nets
        selected_nets = [next(n for n in self.nets if n.key() == k) for k in self.chosen]

        # Separate debug and normal nets
        debug_nets = [n for n in selected_nets if n.type == "debug"]
        normal_nets = [n for n in selected_nets if n.type != "debug"]

        # Handle debug nets - prompt for device type
        if debug_nets:
            for net in debug_nets:
                device_type = simpledialog.askstring(
                    "J-Link Device Type",
                    f"Enter device type for debug net on {net.instrument} at {net.addr}:"
                )
                if device_type:
                    net.chan = device_type
                else:
                    messagebox.showinfo("Cancelled", "Debug net configuration cancelled.")
                    return

        try:
            # Save all selected nets
            all_nets_to_save = normal_nets + debug_nets
            if _save_nets_batch(self.ctx, self.dut, all_nets_to_save):
                self.refresh_data()
                self.chosen.clear()
                self.refresh_available_nets()
                # Switch back to saved nets tab
                self.notebook.select(0)
                messagebox.showinfo("Success", f"Added {len(all_nets_to_save)} nets successfully.")
            else:
                messagebox.showerror("Error", "Failed to save some nets.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add nets: {str(e)}")

    def _get_addable_nets(self) -> tuple[list[Net], list[str]]:
        """Build list of nets that can be added and warnings"""
        warnings: list[str] = []

        # Deduplicate nets by unique key
        uniq: dict[str, Net] = {}
        for n in self.nets:
            uniq.setdefault(n.key(), n)
        nets: list[Net] = list(uniq.values())

        # Detect multiple physical hubs of same type
        chan_seen: dict[str, set[str]] = defaultdict(set)
        duplicate_hubs: set[str] = set()
        for n in nets:
            if n.instrument in _MULTI_HUBS:
                if n.chan in chan_seen[n.instrument]:
                    duplicate_hubs.add(n.instrument)
                chan_seen[n.instrument].add(n.chan)
        blocked_families = duplicate_hubs.copy()

        remaining: list[Net] = []
        dup_single: set[tuple[str, str]] = set()

        for n in nets:
            if n.instrument in blocked_families:
                continue
            if n.instrument in _SINGLE_CHANNEL_INST and is_single_channel_taken(self.nets, n.instrument, n.addr):
                dup_single.add((n.instrument, n.addr))
                continue
            if n.type == "debug" and n.chan != "DEVICE_TYPE":
                continue
            if not self._row_allowed(n):
                continue
            remaining.append(n)

        for inst in sorted(blocked_families):
            warnings.append(f"Multiple {inst} devices detected – unplug extras before adding nets.")
        for inst, addr in sorted(dup_single):
            warnings.append(f"{inst} at {addr} already has a net.")

        return remaining, warnings

    def _row_allowed(self, n: Net) -> bool:
        """True if row should be shown in Add Nets list"""
        if n.saved:
            return False
        # Hide exact duplicates of saved nets
        for s in self.nets:
            if s.saved and (s.type, s.instrument, s.chan, s.addr) == (n.type, n.instrument, n.chan, n.addr):
                return False
        # Hide a second net for single-channel instruments
        if n.instrument == "Keithley_2281S":
            if any(s.saved and s.instrument == "Keithley_2281S" and s.addr == n.addr for s in self.nets):
                return False
        # Prevent multiple debug nets with same type/instrument/address
        if n.type == "debug":
            if any(s.saved and s.type == "debug" and s.instrument == n.instrument and s.addr == n.addr for s in self.nets):
                return False
        return True

    def rename_net(self):
        """Rename selected net"""
        selection = self.nets_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a net to rename.")
            return

        item = self.nets_tree.item(selection[0])
        old_name = item['values'][0]

        # Find the net object
        net = next((n for n in self.nets if n.saved and n.net == old_name), None)
        if not net:
            messagebox.showerror("Error", "Could not find the selected net.")
            return

        RenameDialog(self.root, self, net)

    def delete_net(self):
        """Delete selected net"""
        selection = self.nets_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a net to delete.")
            return

        item = self.nets_tree.item(selection[0])
        net_name = item['values'][0]
        net_type = item['values'][1]

        # Find the net object
        net = next((n for n in self.nets if n.saved and n.net == net_name and n.type == net_type), None)
        if not net:
            messagebox.showerror("Error", "Could not find the selected net.")
            return

        # Confirm deletion
        if messagebox.askyesno("Confirm Delete",
                              f"Delete saved net '{net_name}' (Type: {net_type})?"):
            try:
                _run_script(self.ctx, "net.py", self.dut, "delete", net_name, net_type)
                self.refresh_data()
                messagebox.showinfo("Success", f"Deleted '{net_name}' successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete net: {str(e)}")

    def delete_all_nets(self):
        """Delete all saved nets"""
        saved_nets = [n for n in self.nets if n.saved]
        if not saved_nets:
            messagebox.showinfo("No Nets", "No saved nets to delete.")
            return

        # Confirm deletion
        if messagebox.askyesno("Confirm Delete All",
                              f"Delete ALL {len(saved_nets)} saved nets on DUT {self.dut}?\n\n"
                              "This action cannot be undone."):
            try:
                _run_script(self.ctx, "net.py", self.dut, "delete-all")
                self.refresh_data()
                messagebox.showinfo("Success", "All nets deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete all nets: {str(e)}")

    def on_closing(self):
        """Handle window closing"""
        self.root.destroy()

    def run(self):
        """Run the GUI application"""
        # Start the GUI main loop
        self.root.mainloop()

class RenameDialog:
    """Dialog for renaming a net"""

    def __init__(self, parent, net_gui: NetGUI, net: Net):
        self.parent = parent
        self.net_gui = net_gui
        self.net = net

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Rename Net")
        self.dialog.geometry("400x150")
        self.dialog.configure(bg=net_gui.colors['bg_dark'])
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))

        self.setup_ui()

    def setup_ui(self):
        """Setup rename dialog UI"""
        main_frame = ttk.Frame(self.dialog, style='Dark.TFrame', padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Label
        label = ttk.Label(main_frame, text=f"Rename '{self.net.net}' to:",
                         style='Dark.TLabel')
        label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # Entry
        self.name_var = tk.StringVar(value=self.net.net)
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        self.name_entry.focus()
        self.name_entry.select_range(0, tk.END)

        # Buttons
        cancel_btn = ttk.Button(main_frame, text="Cancel",
                               command=self.dialog.destroy)
        cancel_btn.grid(row=2, column=0, sticky=tk.W)

        confirm_btn = ttk.Button(main_frame, text="Rename",
                                style='Success.TButton',
                                command=self.rename_net)
        confirm_btn.grid(row=2, column=1, sticky=tk.E)

        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.rename_net())

    def rename_net(self):
        """Perform the rename operation"""
        new_name = self.name_var.get().strip()
        if not new_name or new_name == self.net.net:
            self.dialog.destroy()
            return

        # Check for duplicate names
        if any(n is not self.net and n.saved and n.net.lower() == new_name.lower() for n in self.net_gui.nets):
            messagebox.showerror("Error", "That name is already used!")
            return

        try:
            # Rename via backend
            _run_script(
                self.net_gui.ctx,
                "net.py",
                self.net_gui.dut,
                "rename",
                json.dumps({
                    "old_name": self.net.net,
                    "new_name": new_name,
                    "role": self.net.type,
                    "address": self.net.addr,
                    "instrument": self.net.instrument,
                    "pin": self.net.chan,
                })
            )

            self.net_gui.refresh_data()
            self.dialog.destroy()
            messagebox.showinfo("Success", f"Renamed to '{new_name}' successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename net: {str(e)}")

def launch_net_gui(ctx: click.Context, dut: str) -> None:
    """Launch the Net GUI"""
    if not TKINTER_AVAILABLE:
        click.secho("GUI not available: tkinter not working.", fg='yellow')
        click.secho("   This could be due to:", fg='yellow')
        click.secho("   1. Missing tkinter: brew install python-tk", fg='cyan')
        click.secho("   2. Virtual env using different Python version", fg='cyan')
        click.secho("   3. SSH session without display forwarding", fg='cyan')
        click.secho("   Try: lager nets tui for text-based interface", fg='green')
        return

    try:
        # Create and run GUI
        gui = NetGUI(ctx, dut)
        gui.run()

    except KeyboardInterrupt:
        pass  # Silent exit on Ctrl+C
    except Exception as e:
        click.secho(f"GUI launch failed: {e}", fg='red')
        click.secho("   This might be due to:", fg='yellow')
        click.secho("   1. Display/X11 forwarding issues over SSH", fg='cyan')
        click.secho("   2. Tkinter installation problems", fg='cyan')
        click.secho("   3. Backend connection issues", fg='cyan')
        click.secho("   Try: lager nets tui for text-based interface", fg='green')