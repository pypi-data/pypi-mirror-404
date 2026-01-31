"""
Status GUI implementation using tkinter (cross-platform, built-in)
Provides visual dashboard for box status monitoring
"""
from __future__ import annotations

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
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
import threading
import time
import json
import io
import os
from contextlib import redirect_stdout
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import click


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
    lock_status: str = "Unlocked"
    session_duration: Optional[str] = None
    usage_history: list = None
    last_user: Optional[str] = None

    def __post_init__(self):
        if self.nets is None:
            self.nets = []
        if self.usage_history is None:
            self.usage_history = []


class StatusGUI:
    """Status dashboard GUI application"""

    def __init__(self, ctx, target_box: Optional[str], refresh_interval: float, emitter):
        self.ctx = ctx
        self.target_box = target_box
        self.refresh_interval = refresh_interval
        self.emitter = emitter
        self.running = False
        self.refresh_thread = None

        # Data storage
        self.box_data: Dict[str, BoxInfo] = {}
        self.selected_box: Optional[str] = None  # Will be set to first box after data load
        self.all_boxes: List[str] = []

        # Create main window
        self.root = tk.Tk()
        self.root.title(f"Lager Status Dashboard - Box {target_box}")
        self.root.geometry("1200x800")  # Larger window for better readability
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.minsize(800, 600)  # Minimum window size

        # Enhanced Lager color scheme with better contrast and readability
        self.colors = {
            'bg_dark': '#1e1e1e',      # Slightly lighter dark background
            'bg_light': '#2d2d2d',     # Lighter dark background
            'bg_card': '#3a3a3a',      # More contrast for card background
            'accent': '#ff69b4',       # Lager pink
            'accent_hover': '#ff1493', # Darker pink for hover states
            'text_primary': '#ffffff',  # White text
            'text_secondary': '#cccccc', # Lighter gray text for better readability
            'text_muted': '#999999',   # Muted text for less important info
            'success': '#28a745',      # Professional green for success
            'error': '#dc3545',        # Professional red for error
            'warning': '#ffc107',      # Professional yellow for warning
            'info': '#17a2b8',         # Professional blue for info
            'border': '#555555',       # Border color for separation
            'header_bg': '#2a2a2a'     # Header background
        }

        # Configure root window
        self.root.configure(bg=self.colors['bg_dark'])

        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configure custom styles for Lager theme
        self.configure_styles()

        # Configure colors for status
        self.status_colors = {
            "Online": self.colors['success'],
            "Offline": self.colors['error'],
            "Error": self.colors['warning'],
            "Unknown": self.colors['text_secondary']
        }

        self.setup_ui()

    def configure_styles(self):
        """Configure custom ttk styles for Lager theme"""
        # Configure frame styles
        self.style.configure('Dark.TFrame',
                           background=self.colors['bg_dark'])
        self.style.configure('Card.TFrame',
                           background=self.colors['bg_card'],
                           relief='flat',
                           borderwidth=1)

        # Configure label styles with better contrast and spacing
        self.style.configure('Title.TLabel',
                           background=self.colors['bg_dark'],
                           foreground=self.colors['text_primary'],
                           font=('Segoe UI', 22, 'bold'))  # Larger, better font
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
        self.style.configure('Status.TLabel',
                           background=self.colors['bg_card'],
                           foreground=self.colors['text_secondary'],
                           font=('Segoe UI', 9))

        # Configure button styles with better appearance
        self.style.configure('Accent.TButton',
                           background=self.colors['accent'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           font=('Segoe UI', 10, 'bold'),
                           padding=(15, 8))  # Better padding
        self.style.map('Accent.TButton',
                     background=[('active', self.colors['accent_hover']),
                               ('pressed', self.colors['accent_hover'])])  # Better hover states

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

        # Configure treeview styles with better readability
        self.style.configure('Dark.Treeview',
                           background=self.colors['bg_light'],
                           foreground=self.colors['text_primary'],
                           fieldbackground=self.colors['bg_light'],
                           borderwidth=1,
                           relief='solid',
                           font=('Segoe UI', 10),
                           rowheight=28)  # Better row spacing
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
        """Setup the user interface with enhanced spacing and layout"""
        # Main container with dark theme and better padding
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding="25")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Header section with logo and title
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

        title_label = ttk.Label(title_frame, text="Lager Status Dashboard", style='Title.TLabel')
        title_label.pack(anchor=tk.W)

        # Get current user info for subtitle
        try:
            current_user = self._get_current_user()
            subtitle_text = f"Logged in as: {current_user} • Hardware Testing Dashboard"
        except Exception:
            subtitle_text = "Hardware Testing Dashboard • Session Active"

        subtitle_label = ttk.Label(title_frame,
                                 text=subtitle_text,
                                 style='Subtitle.TLabel')
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))

        # Create main content area with splitter
        content_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Left panel: Multi-box overview
        self.setup_multi_box_overview(content_frame)

        # Right panel: Selected box details
        self.setup_box_details_panel(content_frame)

        # Control panel at bottom (read-only monitoring controls)
        self.setup_monitoring_controls(main_frame)

        # Enhanced status bar with better styling
        self.status_var = tk.StringVar(value="Initializing...")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W, style='Status.TLabel',
                              padding=(10, 5))  # Better padding
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

    def create_status_cards(self, parent):
        """Create modern status cards"""
        self.overview_labels = {}

        # Status cards data
        cards = [
            ("Target Box", self.target_box or "All"),
            ("Backend", "Connected"),
            ("Last Update", "Never"),
            ("Auto-refresh", f"Every {self.refresh_interval}s")
        ]

        for i, (title, value) in enumerate(cards):
            # Card frame
            card = ttk.Frame(parent, style='Card.TFrame', padding="15")
            card.grid(row=0, column=i, padx=(0, 15 if i < len(cards)-1 else 0),
                     sticky=(tk.W, tk.E, tk.N, tk.S))

            # Card header without icon
            title_label = ttk.Label(card, text=title, style='Header.TLabel')
            title_label.pack(anchor=tk.W)

            # Card value
            value_label = ttk.Label(card, text=value, style='Card.TLabel',
                                  font=('Arial', 12, 'bold'))
            value_label.pack(anchor=tk.W, pady=(10, 0))

            self.overview_labels[f"{title}:"] = value_label

    def setup_multi_box_overview(self, parent):
        """Setup left panel with multi-box overview"""
        # Left panel for box overview
        left_panel = ttk.Frame(parent, style='Card.TFrame', padding="15")
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_panel.rowconfigure(1, weight=1)

        # Header
        header_label = ttk.Label(left_panel, text="All Boxes", style='Header.TLabel')
        header_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        # Box overview table
        columns = ("box_id", "status", "lock_status", "response_time", "nets", "last_user")
        self.box_overview_tree = ttk.Treeview(left_panel, columns=columns, show="headings",
                                            height=12, style='Dark.Treeview')

        # Configure columns for multi-box view
        column_configs = {
            "box_id": ("Box Name", 80),
            "status": ("Status", 80),
            "lock_status": ("Lock Status", 100),
            "response_time": ("Response", 80),
            "nets": ("Nets", 50),
            "last_user": ("Last User", 180)
        }

        for col, (heading, width) in column_configs.items():
            self.box_overview_tree.heading(col, text=heading)
            self.box_overview_tree.column(col, width=width, minwidth=width)

        # Scrollbar for box table
        box_scrollbar = ttk.Scrollbar(left_panel, orient=tk.VERTICAL,
                                    command=self.box_overview_tree.yview)
        self.box_overview_tree.configure(yscrollcommand=box_scrollbar.set)

        # Pack table and scrollbar
        self.box_overview_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        box_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

        # Bind selection event
        self.box_overview_tree.bind('<<TreeviewSelect>>', self.on_box_selected)

    def setup_box_details_panel(self, parent):
        """Setup right panel with detailed box information"""
        # Right panel for selected box details
        right_panel = ttk.Frame(parent, style='Card.TFrame', padding="15")
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)

        # Header with selected box info
        self.selected_box_header = ttk.Label(right_panel,
                                           text="Select a box for details",
                                           style='Header.TLabel')
        self.selected_box_header.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        # Create notebook for detailed tabs
        self.notebook = ttk.Notebook(right_panel, style='Dark.TNotebook')
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Setup detail tabs
        self.setup_usage_history_tab()
        self.setup_networks_tab()
        self.setup_activity_log_tab()

    def setup_monitoring_controls(self, parent):
        """Setup read-only monitoring controls"""
        control_frame = ttk.Frame(parent, style='Dark.TFrame')
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        # Monitoring controls (read-only)
        monitor_label = ttk.Label(control_frame, text="Monitoring Controls:",
                                style='Header.TLabel', font=('Arial', 10, 'bold'))
        monitor_label.pack(side=tk.LEFT)

        # Auto-refresh toggle (read-only monitoring)
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_cb = ttk.Checkbutton(control_frame, text="Auto-refresh",
                                        variable=self.auto_refresh_var,
                                        command=self.toggle_auto_refresh)
        self.style.configure('TCheckbutton',
                           background=self.colors['bg_dark'],
                           foreground=self.colors['text_primary'],
                           focuscolor=self.colors['accent'])
        auto_refresh_cb.pack(side=tk.LEFT, padx=(10, 0))

        # Manual refresh button
        self.refresh_btn = ttk.Button(control_frame, text="Refresh Now",
                                     style='Accent.TButton',
                                     command=self.manual_refresh)
        self.refresh_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Status indicator
        self.status_var = tk.StringVar(value="Starting monitoring...")
        status_label = ttk.Label(control_frame, textvariable=self.status_var,
                               style='Dark.TLabel', font=('Arial', 10, 'italic'))
        status_label.pack(side=tk.RIGHT)

    def on_box_selected(self, event):
        """Handle box selection from overview table"""
        selection = self.box_overview_tree.selection()
        if selection:
            item = self.box_overview_tree.item(selection[0])
            selected_box_id = item['values'][0]  # First column is box ID
            self.selected_box = selected_box_id
            self.update_selected_box_details()

    def update_selected_box_details(self):
        """Update the details panel for selected box"""
        if not self.selected_box or self.selected_box not in self.box_data:
            self.selected_box_header.configure(text="Select a box for details")
            return

        box_info = self.box_data[self.selected_box]
        header_text = f"Box {self.selected_box} Details"
        if box_info.lock_status != "Unlocked":
            header_text += f" - {box_info.lock_status}"

        self.selected_box_header.configure(text=header_text)
        self.update_usage_history()
        self.update_networks_display()

    def setup_usage_history_tab(self):
        """Setup usage history and lock status tab"""
        usage_frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(usage_frame, text="Usage History")

        # Current lock status section
        lock_frame = ttk.LabelFrame(usage_frame, text="Current Status", padding="10")
        lock_frame.pack(fill=tk.X, pady=(0, 10))

        self.lock_status_label = ttk.Label(lock_frame, text="Status: Unlocked",
                                         style='Card.TLabel', font=('Arial', 11, 'bold'))
        self.lock_status_label.pack(anchor=tk.W)

        self.session_info_label = ttk.Label(lock_frame, text="No active session",
                                          style='Card.TLabel')
        self.session_info_label.pack(anchor=tk.W, pady=(5, 0))

        # Usage history table
        history_label = ttk.Label(usage_frame, text="Usage History",
                                style='Header.TLabel', font=('Arial', 12, 'bold'))
        history_label.pack(anchor=tk.W, pady=(10, 5))

        # Usage history treeview
        history_columns = ("timestamp", "user", "action", "duration")
        self.usage_history_tree = ttk.Treeview(usage_frame, columns=history_columns,
                                             show="headings", height=10, style='Dark.Treeview')

        history_column_configs = {
            "timestamp": ("Timestamp", 150),
            "user": ("User", 100),
            "action": ("Action", 100),
            "duration": ("Duration", 100)
        }

        for col, (heading, width) in history_column_configs.items():
            self.usage_history_tree.heading(col, text=heading)
            self.usage_history_tree.column(col, width=width)

        # History scrollbar
        history_scrollbar = ttk.Scrollbar(usage_frame, orient=tk.VERTICAL,
                                        command=self.usage_history_tree.yview)
        self.usage_history_tree.configure(yscrollcommand=history_scrollbar.set)

        self.usage_history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_networks_tab(self):
        """Setup networks tab for selected box"""
        net_frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(net_frame, text="Nets")

        # Create treeview for networks of selected box
        columns = ("net_name", "net_type", "instrument", "channel", "status")
        self.selected_net_tree = ttk.Treeview(net_frame, columns=columns, show="headings",
                                            height=10, style='Dark.Treeview')

        # Configure columns
        column_configs = {
            "net_name": ("Net Name", 120),
            "net_type": ("Type", 80),
            "instrument": ("Instrument", 150),
            "channel": ("Channel", 100),
            "status": ("Status", 80)
        }

        for col, (heading, width) in column_configs.items():
            self.selected_net_tree.heading(col, text=heading)
            self.selected_net_tree.column(col, width=width)

        # Scrollbar for networks table
        net_scrollbar = ttk.Scrollbar(net_frame, orient=tk.VERTICAL,
                                    command=self.selected_net_tree.yview)
        self.selected_net_tree.configure(yscrollcommand=net_scrollbar.set)

        self.selected_net_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        net_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def update_usage_history(self):
        """Update usage history for selected box"""
        if not self.selected_box or self.selected_box not in self.box_data:
            return

        box_info = self.box_data[self.selected_box]

        # Update lock status
        if box_info.locked_by:
            status_text = f"Status: Locked by {box_info.locked_by}"
            session_text = f"Session duration: {box_info.session_duration or 'Unknown'}"
        else:
            status_text = "Status: Unlocked"
            session_text = "No active session"

        self.lock_status_label.configure(text=status_text)
        self.session_info_label.configure(text=session_text)

        # Update usage history table
        self.usage_history_tree.delete(*self.usage_history_tree.get_children())
        for entry in box_info.usage_history:
            self.usage_history_tree.insert('', tk.END, values=(
                entry.get('timestamp', ''),
                entry.get('user', ''),
                entry.get('action', ''),
                entry.get('duration', '')
            ))

    def update_networks_display(self):
        """Update networks display for selected box"""
        if not self.selected_box or self.selected_box not in self.box_data:
            return

        box_info = self.box_data[self.selected_box]

        # Clear and repopulate networks table
        self.selected_net_tree.delete(*self.selected_net_tree.get_children())
        for net in box_info.nets:
            net_status = "Active" if box_info.status == "Online" else "Unknown"
            self.selected_net_tree.insert('', tk.END, values=(
                net.get("name", "Unknown"),
                net.get("role", "Unknown"),
                net.get("instrument", "None"),
                net.get("pin", "N/A"),
                net_status
            ))


    def setup_activity_log_tab(self):
        """Setup activity log tab"""
        log_frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(log_frame, text="Activity Log")

        # Create text widget for log with enhanced dark theme and better formatting
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=15,
                               bg=self.colors['bg_light'],
                               fg=self.colors['text_primary'],
                               insertbackground=self.colors['accent'],
                               selectbackground=self.colors['accent'],
                               font=('Consolas', 12),  # Increased font size for better readability
                               relief='solid',
                               borderwidth=1,
                               padx=10, pady=8)  # Internal padding for better readability
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        # Pack text and scrollbar
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure text tags for better colored output
        self.log_text.tag_config("info", foreground=self.colors['info'])
        self.log_text.tag_config("success", foreground=self.colors['success'])
        self.log_text.tag_config("warning", foreground=self.colors['warning'])
        self.log_text.tag_config("error", foreground=self.colors['error'])


    def log_message(self, message: str, level: str = "info"):
        """Add formatted message to activity log with better structure"""
        timestamp = time.strftime("%H:%M:%S")

        # Format the message with better visual structure
        level_prefix = {
            "info": "i",
            "success": "v",
            "warning": "!",
            "error": "x"
        }.get(level, "-")

        full_message = f"[{timestamp}] {level_prefix} {message}\n"

        # Insert with proper formatting and color
        self.log_text.insert(tk.END, full_message, level)
        self.log_text.see(tk.END)

        # Keep log size manageable - keep last 500 lines
        line_count = int(self.log_text.index('end-1c').split('.')[0])
        if line_count > 500:
            self.log_text.delete('1.0', f'{line_count - 400}.0')




    def fetch_box_data(self):
        """Fetch real box data from backend for all configured boxes"""
        try:
            from ....box_storage import list_boxes
            from .commands import _check_box_connectivity, _get_box_nets

            # Get all configured boxes
            boxes = list_boxes()

            if not boxes:
                self.log_message("No boxes configured in .lager file", "warning")
                return False

            # Process each configured box
            for box_name, box_info_raw in boxes.items():
                # Handle both string (IP only) and dict formats
                if isinstance(box_info_raw, dict):
                    box_ip = box_info_raw.get('ip', box_info_raw.get('address', 'unknown'))
                else:
                    box_ip = box_info_raw

                if box_ip == 'unknown':
                    continue

                self.log_message(f"Fetching data for box {box_name} ({box_ip})", "info")

                # Check box connectivity using the fixed function
                connectivity_result = _check_box_connectivity(box_ip)
                status = connectivity_result['status']
                response_time = connectivity_result['response_time'] / 1000.0  # Convert ms to seconds

                if status == "Online":
                    self.log_message(f"Box {box_name}: Online (response time: {response_time:.3f}s)", "success")
                elif status == "Offline":
                    self.log_message(f"Box {box_name}: Offline - {connectivity_result.get('error', 'Unknown error')}", "error")
                else:
                    self.log_message(f"Box {box_name}: {status} - {connectivity_result.get('error', 'Unknown error')}", "warning")
                # Get nets data (only if box is online)
                if status == "Online":
                    nets_info = _get_box_nets(self.ctx, box_ip)
                    nets_data = nets_info.get('nets', [])
                    if nets_info.get('error'):
                        self.log_message(f"Box {box_name}: Error fetching nets - {nets_info['error']}", "error")
                    else:
                        self.log_message(f"Box {box_name}: Found {len(nets_data)} nets", "success")
                else:
                    nets_data = []

                # Get real user information from JWT token
                try:
                    current_user = self._get_current_user()
                    # For now, use simple lock status - in real implementation this would come from lock status API
                    lock_status = "Unlocked"  # Would come from real lock status API
                    locked_by = None
                    session_duration = None

                    self.log_message(f"Box {box_name}: Current user - {current_user}", "info")

                except Exception as e:
                    current_user = "unknown@user.com"
                    lock_status = "Unknown"
                    locked_by = None
                    session_duration = None
                    self.log_message(f"Box {box_name}: Error getting user info - {e}", "warning")

                # Update box info with real data (use box name for display)
                self.box_data[box_name] = BoxInfo(
                    box_id=box_name,
                    status=status,
                    response_time=response_time,
                    nets_count=len(nets_data),
                    last_seen=time.strftime("%H:%M:%S"),
                    nets=nets_data,
                    locked_by=locked_by,
                    lock_status=lock_status,
                    session_duration=session_duration,
                    usage_history=[],  # Real usage history would come from backend API
                    last_user=current_user
                )

                # Emit events for consistency
                self.emitter.emit('box_status', {
                    'box_id': box_name,
                    'status': status,
                    'response_time': response_time,
                    'nets_count': len(nets_data)
                })

            self.log_message(f"Successfully updated {len(boxes)} boxes with real data", "success")
            return True

        except Exception as e:
            self.log_message(f"Error fetching real box data: {e}", "error")
            return False

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

    def refresh_data(self):
        """Refresh all data and update displays"""
        try:
            self.status_var.set("Refreshing...")
            self.refresh_btn.configure(state="disabled")

            # Do the data fetching
            success = self.fetch_box_data()

            # Auto-select first box if none is selected
            if not self.selected_box and self.box_data:
                self.selected_box = list(self.box_data.keys())[0]
                self.log_message(f"Auto-selected box {self.selected_box}", "info")

            # Update displays
            self.update_multi_box_overview()
            self.update_selected_box_details()

            if success:
                status_msg = f"Monitoring {len(self.box_data)} boxes - Last updated: {time.strftime('%H:%M:%S')}"
                self.status_var.set(status_msg)
                self.log_message("Data refresh completed successfully", "success")
            else:
                self.status_var.set("Update failed - using mock data")
                self.log_message("Data refresh failed, showing mock data", "warning")

        except Exception as e:
            error_msg = f"Refresh error: {str(e)}"
            self.log_message(error_msg, "error")
            self.status_var.set("Update failed - error occurred")

            # Show some data even on error to keep GUI functional
            if not self.box_data:
                self.log_message("No data available, generating emergency mock data", "warning")
                self._generate_emergency_data()

        finally:
            # Always re-enable the button
            try:
                self.refresh_btn.configure(state="normal")
            except Exception:
                pass  # Ignore button state errors

    def _generate_emergency_data(self):
        """Generate minimal emergency data to keep GUI functional"""
        emergency_box = self.target_box or "DEMO"
        self.box_data[emergency_box] = BoxInfo(
            box_id=emergency_box,
            status="Emergency-Mode",
            response_time=0.0,
            nets_count=0,
            last_seen=time.strftime("%H:%M:%S"),
            nets=[],
            locked_by=None,
            lock_status="Unknown",
            session_duration=None,
            usage_history=[],
            last_user=None
        )

    def update_multi_box_overview(self):
        """Update the multi-box overview table"""
        try:
            # Clear existing data
            self.box_overview_tree.delete(*self.box_overview_tree.get_children())

            # Populate with current box data
            for box_id, box_info in self.box_data.items():
                # Format response time
                response_str = f"{box_info.response_time:.3f}s" if box_info.response_time < 999 else "Timeout"

                self.box_overview_tree.insert('', tk.END, values=(
                    box_info.box_id,
                    box_info.status,
                    box_info.lock_status,
                    response_str,
                    box_info.nets_count,
                    box_info.last_user or "Unknown"
                ))

            self.log_message(f"Updated overview for {len(self.box_data)} boxes", "success")

        except Exception as e:
            self.log_message(f"Error updating multi-box overview: {e}", "error")

    def update_displays(self):
        """Update all display elements"""
        # The main displays are now handled by update_multi_box_overview and update_selected_box_details
        # which are called from refresh_data()
        pass

    def manual_refresh(self):
        """Handle manual refresh button"""
        self.refresh_data()

    def toggle_auto_refresh(self):
        """Toggle auto-refresh on/off"""
        if self.auto_refresh_var.get():
            self.start_auto_refresh()
            self.log_message("Auto-refresh enabled", "info")
        else:
            self.stop_auto_refresh()
            self.log_message("Auto-refresh disabled", "info")

    def start_auto_refresh(self):
        """Start auto-refresh using tkinter timer"""
        if not self.running:
            self.running = True
            self.schedule_next_refresh()

    def stop_auto_refresh(self):
        """Stop auto-refresh"""
        self.running = False

    def schedule_next_refresh(self):
        """Schedule next auto-refresh using tkinter timer"""
        if self.running and self.auto_refresh_var.get():
            # Schedule refresh in main thread after interval
            self.root.after(int(self.refresh_interval * 1000), self.auto_refresh_callback)

    def auto_refresh_callback(self):
        """Auto-refresh callback - runs in main thread"""
        try:
            self.refresh_data()
            self.schedule_next_refresh()  # Schedule next refresh
        except Exception as e:
            self.log_message(f"Auto-refresh error: {e}", "error")

    def on_closing(self):
        """Handle window closing"""
        self.stop_auto_refresh()
        self.emitter.emit('gui_close', {'reason': 'user_close'})
        self.root.destroy()

    def run(self):
        """Run the GUI application"""
        self.log_message("Status GUI started", "success")

        # Initial data load
        self.refresh_data()

        # Start auto-refresh if enabled
        if self.auto_refresh_var.get():
            self.start_auto_refresh()

        # Start the GUI main loop
        self.root.mainloop()


def launch_status_gui(ctx: click.Context, target_box: Optional[str], refresh_interval: float = 10.0) -> None:
    """Launch the status GUI"""
    from ....box_storage import get_box_ip

    # Resolve local box if provided
    if target_box:
        local_ip = get_box_ip(target_box)
        if local_ip:
            target_box = local_ip

    # Create a minimal emitter that doesn't do anything
    class DummyEmitter:
        def emit(self, event, data):
            pass

    emitter = DummyEmitter()
    ui_config = {}

    emitter.emit('gui_launch', {'box': target_box, 'refresh_interval': refresh_interval})

    if not TKINTER_AVAILABLE:
        emitter.emit('gui_error', {'error': 'tkinter not available', 'details': 'tkinter module not found'})
        click.secho("GUI not available: tkinter not working.", fg='yellow')
        click.secho("   This could be due to:", fg='yellow')
        click.secho("   1. Missing tkinter: brew install python-tk", fg='cyan')
        click.secho("   2. Virtual env using different Python version", fg='cyan')
        click.secho("   3. SSH session without display forwarding", fg='cyan')
        click.secho("   Try: --ui=tui for text-based interface", fg='green')
        return False

    try:
        # Create and run GUI
        gui = StatusGUI(ctx, target_box, refresh_interval, emitter)
        gui.run()
        return True

    except Exception as e:
        emitter.emit('gui_error', {'error': 'GUI launch failed', 'details': str(e)})
        click.echo(f"GUI launch failed: {e}")
        return False
