from __future__ import annotations

import asyncio
import io
import json
import re
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable

import click
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
)

# Handle NoMatches compatibility across textual versions
try:  # textual >= 0.15
    from textual.exceptions import NoMatches
except ModuleNotFoundError:
    try:  # textual 0.12–0.14
        from textual.widget import NoMatches  # type: ignore
    except ModuleNotFoundError:
        class NoMatches(LookupError):
            """Raised when query_one finds no matching node."""
            pass

# ───────────────────────── Lager helpers ──────────────────────────
from ...context import get_impl_path
from ..development.python import run_python_internal

# ──────────────── helpers / model ─────────────────

def _parse_backend_json_tui(raw: str):
    """
    Parse JSON response from backend, handling duplicate output from double execution.
    Same logic as in nets_commands.py but for TUI usage.
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

def _uid(instr: str, chan: str, role: str, name: str) -> str:
    """Return a row-key that is unique for (instrument, USB0::0x05E6::0x2281::4519728::INSTR channel, type, name)."""
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
    # Special case: power-supply nets use 'supply' prefix instead of 'power'
    if role == "power-supply":
        return "supply"
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
    "timeout": 30,  # 30 second timeout to prevent infinite hangs (was 0)
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

def _save_nets_batch(ctx: click.Context, dut: str, nets: list["Net"], custom_names: dict[str, str] | None = None) -> bool:
    """Save multiple nets using batch save with fallback to individual saves."""
    if not nets:
        return True

    custom_names = custom_names or {}
    nets_data = []
    for n in nets:
        net_name = custom_names.get(n.key(), n.net)
        nets_data.append({
            "name": net_name,
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
            response = _parse_backend_json_tui(raw)
            if response.get("ok", False):
                return True
    except (json.JSONDecodeError, Exception):
        pass  # Fall through to individual saves

    # Fallback to individual saves (batch save failed or returned empty)
    saved_count = 0
    for n in nets:
        try:
            net_name = custom_names.get(n.key(), n.net)
            _run_script(ctx, "net.py", dut, "save", json.dumps({
                "name": net_name,
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
    _uid: str = field(init=False)

    def __post_init__(self) -> None:
        self._uid = _uid(self.instrument, self.chan, self.type, self.net)

    # ───── table rows
    def as_row_main(self) -> list[str]:
        status = "[SAVED]" if self.saved else "[PENDING]"
        return [
            f"{status} {self.net}",
            self.type.upper(),
            self.instrument.replace("_", " "),
            self.chan,
            self.addr,
            "[Rename]",
            "[Delete]",
        ]

    def as_row_add(self, chosen: bool, custom_name: str | None = None) -> list[str]:
        display_name = custom_name if custom_name else self.net
        return [
            "[SELECTED]" if chosen else "[ADD]",
            display_name,
            self.type.upper(),
            self.instrument.replace("_", " "),
            self.chan,
            self.addr,
            "[Rename]",
        ]

    def key(self) -> str:
        return self._uid

# ─────────────────── dialogs ────────────────────
class ConfirmDelete(Screen):
    """Are-you-sure overlay for Delete."""

    def __init__(self, net: Net) -> None:
        super().__init__()
        self.net = net

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Static("Confirm Deletion", classes="dialog-title")
            yield Static(
                f"Are you sure you want to delete the saved net:\n\n"
                f"Name: {self.net.net}\n"
                f"Type: {self.net.type}\n"
                f"Instrument: {self.net.instrument}\n\n"
                f"This action cannot be undone.",
                classes="dialog-content"
            )
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Delete", id="confirm", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app: NetApp = self.app  # type: ignore[attr-defined]

        if event.button.id == "cancel":
            app.pop_screen()
            return

        app.pop_screen()
        # Delete this net via net.py script
        try:
            _run_script(app.ctx, "net.py", app.dut, "delete", self.net.net, self.net.type)
            app.show_success(f"Successfully deleted net '{self.net.net}'")
        except Exception as e:
            app.show_error(f"Failed to delete net: {str(e)}")
            return

        if self.net in app.nets:
            app.nets.remove(self.net)
        auto_name = f"{self.net.type}{self.net.chan}"
        duplicate = next(
            (n for n in app.nets if (n.type, n.instrument, n.chan, n.addr) ==
             (self.net.type, self.net.instrument, self.net.chan, self.net.addr)),
            None,
        )
        if duplicate is None:
            app.nets.append(Net(
                instrument=self.net.instrument,
                chan=self.net.chan,
                type=self.net.type,
                net=auto_name,
                addr=self.net.addr,
                saved=False,
            ))
        app._sync_saved_from_disk()
        app._refresh_table()

class RenameDialog(Screen):
    """Prompt + text box to enter a new name."""

    def __init__(self, net: Net) -> None:
        super().__init__()
        self.net = net
        self.input: Input

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Static("Rename Net", classes="dialog-title")
            yield Static(
                f"Current name: {self.net.net}\n"
                f"Type: {self.net.type}\n"
                f"Instrument: {self.net.instrument}",
                classes="dialog-content"
            )
            self.input = Input(
                placeholder="Enter new net name...",
                id="rename_input",
                value=self.net.net
            )
            yield self.input
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Rename", id="confirm", variant="success")

    def on_mount(self) -> None:
        self.input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Cancel / Confirm in the rename dialog."""
        app: NetApp = self.app  # type: ignore[attr-defined]

        if event.button.id == "cancel":
            app.pop_screen()
            return

        new_name = self.input.value.strip()
        if not new_name or new_name == self.net.net:
            app.pop_screen()
            return

        if any(n is not self.net and n.saved and n.net.lower() == new_name.lower() for n in app.nets):
            self.input.placeholder = "That name is already used!"
            self.input.value = ""
            self.input.focus()
            return

        app.pop_screen()
        # Rename the net via net.py script
        try:
            _run_script(
                app.ctx,
                "net.py",
                app.dut,
                "rename",
                self.net.net,
                new_name
            )
            app.show_success(f"Successfully renamed net to '{new_name}'")
        except Exception as e:
            app.show_error(f"Failed to rename net: {str(e)}")
            return

        # Update the net name locally
        self.net.net = new_name
        self.net._uid = _uid(self.net.instrument, self.net.chan, self.net.type, new_name)

        placeholder = next(
            (n for n in app.nets if not n.saved and
             (n.type, n.instrument, n.chan, n.addr) ==
             (self.net.type, self.net.instrument, self.net.chan, self.net.addr)),
            None,
        )
        if placeholder is not None:
            app.nets.remove(placeholder)

        app._sync_saved_from_disk()
        app._refresh_table()

class RenameNewNetDialog(Screen):
    """Prompt + text box to enter a new name for an unsaved net in AddScreen."""

    def __init__(self, net: Net, add_screen: "AddScreen") -> None:
        super().__init__()
        self.net = net
        self.add_screen = add_screen
        self.input: Input

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Static("Rename Net Before Adding", classes="dialog-title")
            current_name = self.add_screen.custom_names.get(self.net.key(), self.net.net)
            yield Static(
                f"Current name: {current_name}\n"
                f"Type: {self.net.type}\n"
                f"Instrument: {self.net.instrument}",
                classes="dialog-content"
            )
            self.input = Input(
                placeholder="Enter new net name...",
                id="rename_new_input",
                value=current_name
            )
            yield self.input
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Rename", id="confirm", variant="success")

    def on_mount(self) -> None:
        self.input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Cancel / Confirm in the rename dialog."""
        app: NetApp = self.app  # type: ignore[attr-defined]

        if event.button.id == "cancel":
            app.pop_screen()
            return

        new_name = self.input.value.strip()
        current_name = self.add_screen.custom_names.get(self.net.key(), self.net.net)

        if not new_name or new_name == current_name:
            app.pop_screen()
            return

        # Check if the name conflicts with any saved net or other custom names
        if any(n.saved and n.net.lower() == new_name.lower() for n in app.nets):
            self.input.placeholder = "That name is already used by a saved net!"
            self.input.value = ""
            self.input.focus()
            return

        # Check if the name conflicts with other custom names in the add screen
        for key, custom in self.add_screen.custom_names.items():
            if key != self.net.key() and custom.lower() == new_name.lower():
                self.input.placeholder = "That name is already used in add list!"
                self.input.value = ""
                self.input.focus()
                return

        # Store the custom name
        self.add_screen.custom_names[self.net.key()] = new_name

        # Update the table display
        try:
            tbl = self.add_screen.query_one("#add_tbl", DataTable)
            # Find the row for this net and update the name column
            for row_idx, row_key in enumerate(tbl.rows):
                if row_key.value == self.net.key():
                    tbl.update_cell_at((row_idx, 1), new_name)
                    break
        except NoMatches:
            pass

        app.pop_screen()

class JLinkDeviceTypeDialog(Screen):
    def __init__(
        self,
        dut: str,
        net_name: str,
        address: str,
        callback: Callable[[bool, str | None], None]
    ):
        super().__init__()
        self.dut = dut
        self.net_name = net_name
        self.address = address
        self.callback = callback
        self.input = Input(placeholder=f"Enter device type for {address}", id="jlink_type")

    def compose(self):
        with Vertical(classes="dialog"):
            yield Static("J-Link Device Configuration", classes="dialog-title")
            yield Static(
                f"Net: {self.net_name}\n"
                f"Address: {self.address}\n\n"
                f"Please specify the device type for this J-Link debugger.",
                classes="dialog-content"
            )
            yield self.input
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Configure", id="confirm", variant="success")

    @on(Button.Pressed)
    def _on_jlink_type_entered(self, event: Button.Pressed):
        if event.button.id == "cancel":
            self.app.pop_screen()
            self.callback(False, None)
            return

        jlink_device_type = self.input.value.strip()
        if not jlink_device_type:
            return  # Prevent empty submission

        self.app.pop_screen()
        self.callback(True, jlink_device_type)

class AddScreen(Screen):
    """Dialog that lets the user multi-select nets to add (unsaved only)."""

    def __init__(self, nets: list[Net], multi_labjack: bool = False) -> None:
        super().__init__()
        self.nets: list[Net] = nets
        self.multi_labjack: bool = multi_labjack
        self.chosen: set[str] = set()
        self.custom_names: dict[str, str] = {}  # key -> custom_name

    def _row_allowed(self, n: Net) -> bool:
        """
        True ⇒ show row in *Add Nets* list (apply various filters).
        """
        if n.saved:
            return False

        # Hide unsaved nets if a saved net already exists for the same physical channel
        # Key: (type, instrument, channel, address)
        if any(s.saved and s.type == n.type and s.instrument == n.instrument and s.chan == n.chan and s.addr == n.addr for s in self.nets):
            return False

        # Hide a second net for single-channel instruments (e.g., Keithley 2281S)
        if n.instrument == "Keithley_2281S":
            if any(s.saved and s.instrument == "Keithley_2281S" and s.addr == n.addr for s in self.nets):
                return False
        # Prevent multiple debug nets with same type/instrument/address
        if n.type == "debug":
            if any(s.saved and s.type == "debug" and s.instrument == n.instrument and s.addr == n.addr for s in self.nets):
                return False
        return True

    def _get_addable_nets(self) -> tuple[list["Net"], list[str]]:
        """
        Build (rows, warnings) for the *Add Nets* screen.

        Rules:
        1. If >1 LabJack_T7 or >1 Acroname_8Port or 4Port is plugged in,
           no nets from that family are shown (with a warning).
        2. Otherwise, nets for the first hub only are listed.
        3. Single-channel instruments may have only one net per address – duplicates are hidden and warned.
        """
        warnings: list[str] = []

        # Deduplicate nets by (instrument, channel, address) - NOT by name
        # This ensures saved "hahahah" on channel 2 deduplicates with unsaved "usb2" on channel 2
        # Prioritize unsaved nets over saved ones when deduplicating
        uniq: dict[tuple[str, str, str, str], Net] = {}
        for n in self.nets:
            # Key by (type, instrument, channel, address) - excludes name
            dedup_key = (n.type, n.instrument, n.chan, n.addr)
            # Only add if key doesn't exist, OR if this net is unsaved and existing is saved
            if dedup_key not in uniq or (not n.saved and uniq[dedup_key].saved):
                uniq[dedup_key] = n
        nets: list[Net] = list(uniq.values())

        # Detect multiple physical hubs of same type (LabJack, Acroname)
        # Key by (instrument, address) to distinguish different physical devices
        chan_seen: dict[tuple[str, str], set[str]] = defaultdict(set)
        duplicate_hubs: set[tuple[str, str]] = set()
        for n in nets:
            if n.instrument in _MULTI_HUBS:
                device_key = (n.instrument, n.addr)
                if n.chan in chan_seen[device_key]:
                    # Same channel seen twice on same device - this is expected (saved + unsaved)
                    # Only block if we see the SAME channel on DIFFERENT devices
                    pass
                chan_seen[device_key].add(n.chan)

        # Check if we have multiple devices of the same type (different addresses)
        device_counts: dict[str, set[str]] = defaultdict(set)
        for n in nets:
            if n.instrument in _MULTI_HUBS:
                device_counts[n.instrument].add(n.addr)

        # Block instrument families that have multiple physical devices
        blocked_families: set[str] = set()
        for inst, addrs in device_counts.items():
            if len(addrs) > 1:
                blocked_families.add(inst)

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
            warnings.append(f"Multiple {inst} devices detected - unplug extras before adding nets.")
        for inst, addr in sorted(dup_single):
            warnings.append(f"{inst} at {addr} already has a net.")

        return remaining, warnings

    def compose(self) -> ComposeResult:
        remaining, warnings = self._get_addable_nets()

        # Sort nets by instrument, then role (adc<dac<gpio<batt<power-supply), then numeric order
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

        # Store the nets that are actually displayed in the table for rename lookups
        # CRITICAL: Only store unsaved nets to prevent delete dialogs
        self.displayed_nets = {n.key(): n for n in remaining if not n.saved}

        with Vertical(classes="dialog"):
            yield Static("Add Available Nets", classes="dialog-title")

            if warnings:
                yield Static("Warnings:", classes="dialog-content")
                for w in warnings:
                    yield Static(f"• {w}", classes="warning")

            # CRITICAL: Filter to only unsaved nets - multiple safety checks
            unsaved_only = [n for n in remaining if not n.saved]

            if unsaved_only:
                yield Static(f"Found {len(unsaved_only)} available nets. Click 'Select' to add nets:", classes="dialog-content")
                tbl = DataTable(id="add_tbl", zebra_stripes=True, show_cursor=True)
                tbl.add_column("[Select]", width=12)
                tbl.add_column("Name")
                tbl.add_column("Type")
                tbl.add_column("Instrument")
                tbl.add_column("Channel")
                tbl.add_column("Address")
                tbl.add_column("[Rename]", width=10)
                for n in unsaved_only:
                    custom_name = self.custom_names.get(n.key())
                    tbl.add_row(*n.as_row_add(False, custom_name), key=n.key())
                yield tbl
            else:
                yield Static("No Available Nets to Add", classes="placeholder")
                yield Static("All compatible nets are already saved or unavailable.", classes="info")

            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                if remaining:
                    yield Button("Add Selected", id="confirm", variant="success")
                else:
                    yield Button("Close", id="close", variant="primary")

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        key = event.cell_key.row_key.value
        col = event.coordinate.column

        # CRITICAL: Stop event propagation to prevent main screen from handling it
        event.stop()

        # Handle [Select] column (column 0)
        if col == 0:
            coord = (event.coordinate.row, 0)
            tbl = self.query_one(DataTable)
            if key in self.chosen:
                self.chosen.remove(key)
                tbl.update_cell_at(coord, "[ADD]")
            else:
                self.chosen.add(key)
                tbl.update_cell_at(coord, "[SELECTED]")

        # Handle [Rename] column (column 6)
        elif col == 6:
            # Get the net from the displayed nets (guaranteed to be unsaved)
            net = self.displayed_nets.get(key)
            if net and not net.saved:  # Double-check it's unsaved
                self.app.push_screen(RenameNewNetDialog(net, self))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle *Cancel* / *Confirm* buttons in the Add-dialog."""
        main: NetApp = self.app

        if event.button.id in ("cancel", "close"):
            main.pop_screen()
            return
        if not self.chosen:
            main.pop_screen()
            return

        # Collect all selected Net objects
        selected_nets = [next(n for n in main.nets if n.key() == k) for k in self.chosen]

        # Separate debug and normal nets
        debug_nets = [n for n in selected_nets if n.type == "debug"]
        normal_nets = [n for n in selected_nets if n.type != "debug"]

        # Check for single-channel device conflicts (one net per instrument+address)
        single_cnt: dict[tuple[str, str], int] = defaultdict(int)
        for s in main.nets:
            if s.saved and s.instrument in _SINGLE_CHANNEL_INST:
                single_cnt[(s.instrument, s.addr)] += 1
        for n in selected_nets:
            if n.instrument in _SINGLE_CHANNEL_INST:
                single_cnt[(n.instrument, n.addr)] += 1
        conflicts = [(inst, addr) for (inst, addr), cnt in single_cnt.items() if cnt > 1]
        if conflicts:
            parts = [f"{inst} at {addr}" for inst, addr in conflicts]
            msg = "Only one net may be added per " + ", ".join(parts) + "."
            try:
                self.query_one("#keithley_hint", Static).update(msg)
            except NoMatches:
                self.mount(Static(msg, id="keithley_hint", classes="warning"))
            return
        else:
            try:
                self.query_one("#keithley_hint", Static).update("")
            except NoMatches:
                pass

        # If no debug nets selected, save immediately using batch save
        if not debug_nets:
            if _save_nets_batch(main.ctx, main.dut, selected_nets, self.custom_names):
                main.show_success(f"Successfully added {len(selected_nets)} nets")
            else:
                main.show_error("Failed to save some nets")
            # Refresh saved nets and update UI
            main._sync_saved_from_disk()
            main._refresh_table()
            main.pop_screen()
            return

        # If there are debug nets, prompt for each J-Link device type
        self._pending_debug_nets = debug_nets
        self._pending_normal_nets = normal_nets
        self._debug_idx = 0

        def handle_jlink_complete(success: bool, device_type: str | None):
            if not success or not device_type:
                main.pop_screen(to=self)
                return
            # Set the J-Link device type as the "channel"
            self._pending_debug_nets[self._debug_idx].chan = device_type
            self._debug_idx += 1
            if self._debug_idx < len(self._pending_debug_nets):
                prompt_next()
                return
            # All debug prompts done – save all pending nets using batch save
            all_nets_to_save = self._pending_normal_nets + self._pending_debug_nets
            if _save_nets_batch(main.ctx, main.dut, all_nets_to_save, self.custom_names):
                main.show_success(f"Successfully added {len(all_nets_to_save)} nets")
            else:
                main.show_error("Failed to save some nets")
            main._sync_saved_from_disk()
            main._refresh_table()
            main.pop_screen()

        def prompt_next():
            n = self._pending_debug_nets[self._debug_idx]
            main.push_screen(JLinkDeviceTypeDialog(main.dut, n.net, n.addr, handle_jlink_complete))

        prompt_next()

class ConfirmDeleteAll(Screen):
    """Are-you-sure overlay for *Delete All Nets*."""

    def compose(self) -> ComposeResult:
        dut_id = getattr(self.app, "dut", "this DUT")  # type: ignore[attr-defined]
        with Vertical(classes="dialog"):
            yield Static("Confirm Delete All", classes="dialog-title")
            yield Static(
                f"WARNING: This will delete ALL saved nets on device {dut_id}.\n\n"
                f"This action is permanent and cannot be undone.\n\n"
                f"Are you sure you want to continue?",
                classes="dialog-content warning"
            )
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Delete All", id="confirm", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app: NetApp = self.app  # type: ignore[attr-defined]

        if event.button.id == "cancel":
            app.pop_screen()
            return

        # Delete all saved nets via net.py script
        try:
            _run_script(app.ctx, "net.py", app.dut, "delete-all")
            app.show_success("Successfully deleted all nets")
        except Exception as e:
            app.show_error(f"Failed to delete all nets: {str(e)}")
        app._sync_saved_from_disk()
        app._refresh_table()
        app.pop_screen()

# ────────────────────────── main app ───────────────────────────────
class NetApp(App):
    CSS = """
    /* Global App Styling */
    App {
        background: $surface-darken-2;
        color: $text;
    }

    /* Header Styling */
    Header {
        background: $primary;
        color: $text-primary;
        height: 3;
        text-align: center;
        content-align: center middle;
    }

    /* Main Title */
    .title {
        text-style: bold;
        color: $accent;
        background: $surface;
        height: 3;
        content-align: center middle;
        margin: 1 0;
        border: solid $primary;
        padding: 1;
    }

    /* Data Table Styling */
    DataTable {
        background: $surface;
        border: solid $primary;
        margin: 0;
        height: 1fr;
        dock: top;
    }

    DataTable > .datatable--header {
        background: $primary-darken-1;
        color: $text-primary;
        text-style: bold;
        height: 3;
    }

    DataTable > .datatable--cursor {
        background: $accent 30%;
        color: $text;
    }

    DataTable > .datatable--hover {
        background: $primary 20%;
    }

    /* Button Styling */
    Button {
        margin: 0 1;
        min-width: 16;
        height: 3;
        text-style: bold;
    }

    Button.-primary {
        background: $primary;
        color: $text-primary;
        border: none;
    }

    Button.-primary:hover {
        background: $primary-lighten-1;
    }

    Button.-success {
        background: $success;
        color: $text;
        border: none;
    }

    Button.-success:hover {
        background: $success-lighten-1;
    }

    Button.-error {
        background: $error;
        color: $text;
        border: none;
    }

    Button.-error:hover {
        background: $error-lighten-1;
    }

    /* Button Container Row */
    .button-row {
        height: 5;
        width: 100%;
        margin: 1 0;
        dock: bottom;
    }

    .button-container-left {
        width: 1fr;
    }

    .button-container-center {
        width: auto;
        align: center middle;
    }

    .button-container-right {
        width: 1fr;
        align: right middle;
        margin-right: 2;
    }

    /* Input Styling */
    Input {
        background: $surface;
        border: solid $primary;
        margin: 1 0;
        height: 3;
    }

    Input:focus {
        border: solid $accent;
    }

    /* Static Text Styling */
    .placeholder {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        height: 3;
        content-align: center middle;
        margin: 0;
        dock: top;
    }

    .warning {
        background: $warning;
        color: $text;
        text-style: bold;
        padding: 1;
        margin: 1 0;
        border-left: thick $error;
    }

    .error {
        background: $error;
        color: $text;
        text-style: bold;
        padding: 1;
        margin: 1 0;
        border-left: thick $error-darken-1;
    }

    .info {
        background: $primary 20%;
        color: $text;
        padding: 1;
        margin: 1 0;
        border-left: thick $primary;
    }

    .success {
        background: $success 20%;
        color: $text;
        padding: 1;
        margin: 1 0;
        border-left: thick $success;
    }

    /* Footer Styling */
    Footer {
        background: $surface-darken-1;
        color: $text-muted;
        height: 1;
    }

    /* Modal/Dialog Styling */
    Screen {
        align: center middle;
    }

    .dialog {
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin: 1;
        width: 90%;
        height: 90%;
        max-height: 90%;
    }

    .dialog-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }

    .dialog-content {
        margin: 1 0;
    }

    .dialog-buttons {
        height: 5;
        align: center middle;
        margin-top: 1;
        dock: bottom;
        padding: 1 0;
    }

    /* Action buttons specific styling */
    #add_btn {
        background: $success;
        color: $text;
    }

    #del_all_btn {
        background: $error;
        color: $text;
    }

    #exit_btn {
        min-width: 12;
    }

    /* Add Nets Table Styling */
    #add_tbl {
        height: 1fr;
        max-height: 25;
        overflow-y: auto;
        margin: 1 0;
    }

    /* Loading/Progress Indicators */
    .loading {
        text-align: center;
        color: $accent;
        text-style: bold;
    }

    .status-indicator {
        width: 3;
        height: 1;
        margin: 0 1;
    }

    .status-saved {
        background: $success;
        color: $text;
    }

    .status-pending {
        background: $warning;
        color: $text;
    }

    .status-error {
        background: $error;
        color: $text;
    }


    /* Zebra striping for tables */
    .zebra-even {
        background: $surface-lighten-1;
    }

    .zebra-odd {
        background: $surface;
    }
    """

    BINDINGS = [("q", "quit", "Quit"), ("ctrl+c", "quit", "Exit")]

    def __init__(self, ctx: click.Context, dut: str,
                 inst_list: list[dict[str, str]],
                 nets: list[Net], multi_labjack: bool = False):
        super().__init__()
        self.ctx, self.dut, self.nets = ctx, dut, nets
        self.inst_list = inst_list
        self.multi_labjack = multi_labjack

    def compose(self) -> ComposeResult:
        yield Header()

        # main table at the top
        self.tbl = DataTable(zebra_stripes=True, show_cursor=True)
        self.tbl.add_columns(
            "Net Name", "Type", "Instrument", "Channel", "Address",
            "[Rename]", "[Delete]"
        )
        yield self.tbl

        self.no_saved = Static("No Saved Nets Available", classes="placeholder")
        self.no_saved.visible = False
        yield self.no_saved

        # action buttons layout
        with Horizontal(classes="button-row"):
            # Left spacer
            with Horizontal(classes="button-container-left"):
                pass
            # Center buttons container
            with Horizontal(classes="button-container-center"):
                self.add_btn = Button("+ Add Nets", id="add_btn", variant="primary")
                self.del_all_btn = Button("Delete All Nets", id="del_all_btn", variant="error")
                self.del_all_btn.visible = False  # shown only when nets exist
                yield self.add_btn
                yield self.del_all_btn
            # Right button container
            with Horizontal(classes="button-container-right"):
                self.exit_btn = Button("Exit", id="exit_btn", variant="success")
                yield self.exit_btn

        yield Footer()

    def on_mount(self) -> None:
        self.show_loading("Loading saved nets...")
        self._sync_saved_from_disk()
        self._refresh_table()
        self.hide_loading()

    def show_loading(self, message: str) -> None:
        """Show loading message."""
        if hasattr(self, 'loading_msg'):
            self.loading_msg.update(message)
        else:
            self.loading_msg = Static(message, classes="loading")
            self.mount(self.loading_msg)

    def hide_loading(self) -> None:
        """Hide loading message."""
        if hasattr(self, 'loading_msg'):
            self.loading_msg.remove()

    def _refresh_table(self) -> None:
        """Re-populate the main table & toggle *Delete All* visibility."""
        saved = [n for n in self.nets if n.saved]
        if saved:
            self.tbl.visible = True
            self.no_saved.visible = False
            self.del_all_btn.visible = True

            self.tbl.clear()
            seen: set[str] = set()
            # Sort by instrument, then by net type, then by name
            sorted_nets = sorted(saved, key=lambda x: (x.instrument.replace("_", " "), x.type, x.net))
            for n in sorted_nets:
                uid = n.key()
                if uid in seen:
                    continue
                seen.add(uid)
                self.tbl.add_row(*n.as_row_main(), key=uid)
        else:
            self.tbl.visible = False
            self.no_saved.visible = True
            self.del_all_btn.visible = False

    def _sync_saved_from_disk(self) -> None:
        # Retrieve saved nets from disk via net.py list
        try:
            output = _run_script(self.ctx, "net.py", self.dut, "list")
            saved_from_disk = _parse_backend_json_tui(output) if output.strip() else []
        except (json.JSONDecodeError, AttributeError) as e:
            # Show error message to user but continue with empty list
            self.show_error(f"Error loading saved nets: {str(e)}")
            saved_from_disk = []
        except Exception as e:
            # Handle any other unexpected errors
            self.show_error(f"Unexpected error: {str(e)}")
            saved_from_disk = []

        # Keep unsaved nets and replace saved nets with those from disk
        self.nets = [n for n in self.nets if not n.saved] + [
            Net(
                instrument=rec.get("instrument", "NA"),
                chan=rec.get("pin", "NA"),
                type=rec.get("role", "NA"),
                net=rec.get("name"),
                addr=rec.get("address", "NA"),
                saved=True,
            ) for rec in saved_from_disk
        ]
        self._ensure_autogen_unsaved()

    def show_error(self, message: str) -> None:
        """Show error message to user."""
        error_msg = Static(f"Error: {message}", classes="error")
        self.mount(error_msg)
        # Auto-remove error after 5 seconds
        self.set_timer(5.0, lambda: error_msg.remove())

    def show_success(self, message: str) -> None:
        """Show success message to user."""
        success_msg = Static(message, classes="success")
        self.mount(success_msg)
        # Auto-remove success after 3 seconds
        self.set_timer(3.0, lambda: success_msg.remove())

    def _ensure_autogen_unsaved(self) -> None:
        # Track which channels have unsaved placeholders
        unsaved_keys = {(n.type, n.instrument, n.chan, n.addr) for n in self.nets if not n.saved}
        role_counter: dict[str, int] = defaultdict(int)
        idx_re = re.compile(r"^([A-Za-z]+)(\d+)$")

        # Track highest auto-index for each role already present
        for n in self.nets:
            m = idx_re.match(n.net)
            if m and _first_word(n.type) == m.group(1):
                role_counter[n.type] = max(role_counter[n.type], int(m.group(2)))

        # Add placeholder unsaved nets for ALL channels (even if saved versions exist)
        for dev in self.inst_list:
            instr = dev.get("name", "Unknown")
            addr = dev.get("address", "NA")
            channel_map = dev.get("channels", {})
            for role, channels in (channel_map or {}).items():
                # Sort channels to ensure consistent ordering
                sorted_channels = sorted(channels, key=lambda ch: str(ch))
                for ch in sorted_channels:
                    key = (role, instr, ch, addr)
                    # Only skip if an UNSAVED placeholder already exists
                    if key in unsaved_keys:
                        continue
                    role_counter[role] += 1
                    auto_name = f"{_first_word(role)}{role_counter[role]}"
                    self.nets.append(Net(instr, ch, role, auto_name, addr, saved=False))
                    unsaved_keys.add(key)

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        key = event.cell_key.row_key.value  # type: ignore[attr-defined]
        col = event.coordinate.column
        net = next(x for x in self.nets if x.key() == key)
        if col == 5:  # Rename column
            self.push_screen(RenameDialog(net))
        elif col == 6:  # Delete column
            self.push_screen(ConfirmDelete(net))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle *Add Nets*, *Delete All Nets*, and *Save & Exit* buttons."""
        if event.button.id == "add_btn":
            self.push_screen(AddScreen(self.nets, self.multi_labjack))
            return
        if event.button.id == "del_all_btn":
            self.push_screen(ConfirmDeleteAll())
            return
        if event.button.id == "exit_btn":
            self.action_quit()
            return


    def action_quit(self) -> None:
        self.exit()

def launch_tui(ctx: click.Context, dut: str) -> None:
    # Query connected instruments and saved nets
    try:
        inst_result = _run_script(ctx, "query_instruments.py", dut)
        inst_list = json.loads(inst_result) if inst_result.strip() else []
    except (json.JSONDecodeError, AttributeError):
        inst_list = []

    try:
        saved_result = _run_script(ctx, "net.py", dut, "list")
        saved_list = _parse_backend_json_tui(saved_result) if saved_result.strip() else []
    except (json.JSONDecodeError, AttributeError):
        saved_list = []

    # Sort instruments by their first channel to ensure consistent ordering
    # This ensures UART devices are processed in order (ttyUSB0, ttyUSB1, ttyUSB2, etc.)
    def sort_key(dev):
        channels = dev.get("channels", {})
        # Get the first channel from any role, or empty string if none
        for role_channels in channels.values():
            if role_channels:
                return str(sorted(role_channels)[0])
        return ""

    inst_list.sort(key=sort_key)

    role_counter: dict[str, int] = defaultdict(int)
    nets: list[Net] = []
    idx_re = re.compile(r"^([A-Za-z]+)(\d+)$")

    # First, load saved nets and track highest number for each role
    for rec in saved_list:
        net_name = rec.get("name", "")
        role = rec.get("role", "NA")

        # Track highest auto-index for each role already present in saved nets
        m = idx_re.match(net_name)
        if m and _first_word(role) == m.group(1):
            role_counter[role] = max(role_counter[role], int(m.group(2)))

        nets.append(Net(
            instrument=rec.get("instrument", "NA"),
            chan=rec.get("pin", "NA"),
            type=role,
            net=net_name,
            addr=rec.get("address", "NA"),
            saved=True,
        ))

    # Now generate auto-names for new devices, continuing from highest saved number
    for dev in inst_list:
        instr = dev.get("name", "Unknown")
        addr = dev.get("address", "NA")
        channel_map = dev.get("channels", {})
        for role, channels in (channel_map or {}).items():
            # Sort channels to ensure consistent ordering (e.g., /dev/ttyUSB0 before /dev/ttyUSB1)
            sorted_channels = sorted(channels, key=lambda ch: str(ch))
            for ch in sorted_channels:
                # Check if this exact net already exists - skip counter increment if so
                already_exists = any(
                    n.type == role
                    and n.instrument == instr
                    and str(n.chan) == str(ch)
                    and n.addr == addr
                    and n.saved
                    for n in nets
                )

                if not already_exists:
                    role_counter[role] += 1

                auto_name = f"{_first_word(role)}{role_counter[role]}"
                nets.append(Net(instr, ch, role, auto_name, addr, saved=False))

    # Launch the Textual TUI
    NetApp(ctx, dut, inst_list, nets).run()
