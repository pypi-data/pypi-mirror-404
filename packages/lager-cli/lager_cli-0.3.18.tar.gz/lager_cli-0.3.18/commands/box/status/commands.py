"""
status_commands.py – "lager status …" CLI group
-------------------------------------------
Status monitoring TUI and GUI commands.
"""

from __future__ import annotations

import time
from typing import Dict, Any, Optional

import click
import requests
import shutil
from texttable import Texttable

from .status_tui import launch_status_tui
from ....box_storage import list_boxes, get_box_ip
from ....core.net_storage import load_nets
# GUI import moved to function to avoid tkinter import on every CLI command


def _check_box_connectivity(box_ip: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Check if a box is online and responsive.

    Args:
        box_ip: IP address of the box
        timeout: Request timeout in seconds

    Returns:
        Dict with status, response_time, error info, and error_type
    """
    import subprocess
    import ipaddress
    import socket

    # First check if this is an IP address
    try:
        ipaddress.ip_address(box_ip)
        is_ip = True
    except ValueError:
        is_ip = False

    if is_ip:
        # For direct IP connections (like Tailscale), use ping like the hello command
        try:
            start_time = time.time()
            result = subprocess.run([
                'ping', '-c', '3', '-W', '2000', box_ip
            ], capture_output=True, text=True, timeout=timeout)
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            if result.returncode == 0:
                return {
                    "status": "Online",
                    "response_time": response_time,
                    "error": None,
                    "error_type": None
                }
            else:
                # Parse ping output for more specific error
                stderr_lower = result.stderr.lower() if result.stderr else ""
                stdout_lower = result.stdout.lower() if result.stdout else ""
                output_lower = stderr_lower + stdout_lower

                if "no route to host" in output_lower or "network is unreachable" in output_lower:
                    error_msg = "No route to host"
                    error_type = "no_route"
                elif "host unreachable" in output_lower:
                    error_msg = "Host unreachable"
                    error_type = "unreachable"
                elif "request timeout" in output_lower or "100% packet loss" in output_lower:
                    error_msg = "Ping timeout - host not responding"
                    error_type = "timeout"
                else:
                    error_msg = "Ping failed"
                    error_type = "ping_failed"

                return {
                    "status": "Offline",
                    "response_time": response_time,
                    "error": error_msg,
                    "error_type": error_type
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "Offline",
                "response_time": timeout * 1000,
                "error": "Ping timeout - command timed out",
                "error_type": "timeout"
            }
        except FileNotFoundError:
            return {
                "status": "Error",
                "response_time": 0,
                "error": "Ping command not found",
                "error_type": "missing_tool"
            }
        except Exception as e:
            return {
                "status": "Error",
                "response_time": 0,
                "error": str(e),
                "error_type": "unknown"
            }
    else:
        # For box IDs, try the HTTP API
        try:
            start_time = time.time()
            # Try a simple HTTP request to the box health endpoint
            response = requests.get(f"http://{box_ip}:8000/health", timeout=timeout)
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            if response.status_code == 200:
                return {
                    "status": "Online",
                    "response_time": response_time,
                    "error": None,
                    "error_type": None
                }
            else:
                return {
                    "status": "Error",
                    "response_time": response_time,
                    "error": f"HTTP {response.status_code}",
                    "error_type": "http_error"
                }
        except requests.exceptions.Timeout:
            return {
                "status": "Offline",
                "response_time": timeout * 1000,
                "error": "Connection timed out",
                "error_type": "timeout"
            }
        except requests.exceptions.ConnectionError as e:
            error_str = str(e).lower()
            if 'connection refused' in error_str:
                return {
                    "status": "Offline",
                    "response_time": 0,
                    "error": "Connection refused - service not running",
                    "error_type": "connection_refused"
                }
            elif 'no route to host' in error_str or 'network is unreachable' in error_str:
                return {
                    "status": "Offline",
                    "response_time": 0,
                    "error": "No route to host - check VPN connection",
                    "error_type": "no_route"
                }
            elif 'name or service not known' in error_str or 'nodename nor servname' in error_str:
                return {
                    "status": "Offline",
                    "response_time": 0,
                    "error": "DNS resolution failed - hostname not found",
                    "error_type": "dns_error"
                }
            else:
                return {
                    "status": "Offline",
                    "response_time": 0,
                    "error": f"Connection error: {e}",
                    "error_type": "connection_error"
                }
        except Exception as e:
            return {
                "status": "Error",
                "response_time": 0,
                "error": str(e),
                "error_type": "unknown"
            }


def _get_box_nets(ctx: click.Context, box_name: str) -> Dict[str, Any]:
    """
    Get nets information for a specific box from local storage.

    Args:
        ctx: Click context (unused, kept for compatibility)
        box_name: Name of the box

    Returns:
        Dict with nets list and count
    """
    try:
        nets = load_nets(box_name)
        return {
            "nets": nets,
            "count": len(nets),
            "error": None
        }
    except Exception as e:
        return {"nets": [], "count": 0, "error": str(e)}


def _format_status_table(box_data: Dict[str, Dict[str, Any]]) -> None:
    """
    Display a formatted table of box status information.

    Args:
        box_data: Dictionary mapping box names to their status info
    """
    if not box_data:
        click.echo("No boxes found in .lager file. Add one with: lager boxes add --name <NAME> --ip <IP>")
        return

    table = Texttable()
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype(['t', 't', 't', 't', 't', 't'])
    table.set_cols_align(["l", "l", "r", "l", "r", "t"])

    # Calculate column widths
    term_width = shutil.get_terminal_size((120, 24)).columns
    col_widths = [12, 10, 15, 15, 6, max(20, term_width - 70)]
    table.set_cols_width(col_widths)

    table.add_row(['Box Name', 'Status', 'Response (ms)', 'IP Address', 'Nets', 'Last Error'])

    for box_name, data in sorted(box_data.items()):
        conn_info = data['connectivity']
        nets_info = data['nets']

        # Format response time
        response_str = f"{conn_info['response_time']:.1f}" if conn_info['response_time'] > 0 else "-"

        # Format error (truncate if too long)
        error_str = conn_info['error'] or ""
        if len(error_str) > col_widths[5]:
            error_str = error_str[:col_widths[5]-3] + "..."

        table.add_row([
            box_name,
            conn_info['status'],
            response_str,
            data['ip'],
            str(nets_info['count']),
            error_str
        ])

    # Color-code status in output
    table_output = table.draw()
    # Display with colors based on status
    for line in table_output.split('\n'):
        if 'Online' in line:
            click.secho(line, fg='green')
        elif 'Offline' in line or 'Error' in line:
            click.secho(line, fg='red')
        else:
            click.echo(line)


def _display_box_details(box_name: str, box_ip: str, box_data: Dict[str, Any]) -> None:
    """
    Display detailed information for a specific box.

    Args:
        box_name: Name of the box
        box_ip: IP address of the box
        box_data: Status and nets data for the box
    """
    conn_info = box_data['connectivity']
    nets_info = box_data['nets']

    click.echo(f"\nBox Status: {box_name}")
    click.echo("=" * (len(box_name) + 12))

    # Connectivity information
    click.echo(f"IP Address: {box_ip}")
    status_color = 'green' if conn_info['status'] == 'Online' else 'red'
    click.secho(f"Status: {conn_info['status']}", fg=status_color)

    if conn_info['response_time'] > 0:
        click.echo(f"Response Time: {conn_info['response_time']:.1f} ms")

    if conn_info['error']:
        click.secho(f"Error: {conn_info['error']}", fg='red')

    # Nets information
    click.echo(f"\nActive Nets: {nets_info['count']}")

    if nets_info['error']:
        click.secho(f"Nets Error: {nets_info['error']}", fg='red')
    elif nets_info['nets']:
        click.echo()
        _display_nets_table(nets_info['nets'])
    elif nets_info['count'] == 0:
        click.echo("No nets configured on this box.")


def _display_nets_table(nets: list) -> None:
    """
    Display a formatted table of nets (reusing logic from nets command).

    Args:
        nets: List of net dictionaries
    """
    if not nets:
        return

    # Calculate terminal width for responsive layout
    term_w = shutil.get_terminal_size((120, 24)).columns

    # Prepare data
    headers = ["Name", "Type", "Instrument", "Channel", "Address"]
    rows = [
        [
            net.get("name", ""),
            net.get("role", ""),
            net.get("instrument", "") or "",
            net.get("pin", "") or "",
            net.get("address", "") or "",
        ]
        for net in nets
    ]

    # Calculate column widths
    min_widths = [8, 10, 14, 7, 20]
    col_widths = [
        max(min_widths[i], max(len(str(r[i])) for r in rows + [headers]))
        for i in range(len(min_widths))
    ]

    # Adjust address column to fit terminal
    used_width = sum(col_widths[:-1]) + 4 * 2  # padding
    remaining_width = max(20, term_w - used_width - 2)
    col_widths[-1] = remaining_width

    # Format and display
    def format_row(row):
        return (
            f"{row[0]:<{col_widths[0]}}  "
            f"{row[1]:<{col_widths[1]}}  "
            f"{row[2]:<{col_widths[2]}}  "
            f"{row[3]:<{col_widths[3]}}  "
            f"{row[4]:<{col_widths[4]}}"
        )

    click.secho(format_row(headers), fg='green')
    click.echo("-" * sum(col_widths) + "-" * 8)  # separator
    for row in rows:
        click.secho(format_row(row), fg='green')


@click.group(
    name="status",
    invoke_without_command=True,
    help="Show box status and connectivity",
)
@click.option("--box", help="Lagerbox name or IP")
@click.pass_context
def status(ctx: click.Context, box: str | None) -> None:
    """
    Show box status and connectivity information
    """
    if ctx.invoked_subcommand is None:
        if box:
            _show_box_status(ctx, box)
        else:
            _show_all_boxes_status(ctx)


def _show_all_boxes_status(ctx: click.Context) -> None:
    """Show status overview for all configured boxes."""
    boxes = list_boxes()

    if not boxes:
        click.echo("No boxes found in .lager file. Add one with: lager boxes add --name <NAME> --ip <IP>")
        return

    click.echo("Checking box connectivity...")

    box_data = {}
    for box_name, box_info in boxes.items():
        # Handle both string (IP only) and dict formats
        if isinstance(box_info, dict):
            box_ip = box_info.get('ip', box_info.get('address', 'unknown'))
        else:
            box_ip = box_info

        if box_ip == 'unknown':
            continue

        # Check connectivity
        connectivity = _check_box_connectivity(box_ip)

        # Get nets info from local storage (regardless of connectivity)
        nets_info = _get_box_nets(ctx, box_name)

        box_data[box_name] = {
            'ip': box_ip,
            'connectivity': connectivity,
            'nets': nets_info
        }

    click.echo()  # Empty line before table
    _format_status_table(box_data)


def _show_box_status(ctx: click.Context, box_name: str) -> None:
    """Show detailed status for a specific box."""
    # First try to resolve as a local box name
    box_ip = get_box_ip(box_name)
    original_box_name = box_name

    if not box_ip:
        # Check if it might be an IP address directly
        try:
            import ipaddress
            ipaddress.ip_address(box_name)
            box_ip = box_name
            box_name = f"Direct IP ({box_name})"
        except ValueError:
            click.secho(f"Error: Box '{box_name}' not found in .lager file", fg='red', err=True)
            boxes = list_boxes()
            if boxes:
                click.echo("Available boxes:", err=True)
                for name in sorted(boxes.keys()):
                    click.echo(f"  - {name}", err=True)
            else:
                click.echo("No boxes configured. Add one with:", err=True)
                click.echo("  lager boxes add --name <NAME> --ip <IP>", err=True)
            ctx.exit(1)

    click.echo(f"Checking status for {box_name}...")

    # Check connectivity
    connectivity = _check_box_connectivity(box_ip)

    # Get nets information from local storage using original box name
    nets_info = _get_box_nets(ctx, original_box_name)

    # Display detailed information
    box_data = {
        'connectivity': connectivity,
        'nets': nets_info
    }

    _display_box_details(box_name, box_ip, box_data)


@status.command("tui", help="Launch status monitoring TUI")
@click.option("--refresh-interval", type=float, default=10.0,
              help="Refresh interval in seconds (s)")
@click.pass_context
def tui_cmd(ctx: click.Context, refresh_interval: float) -> None:
    """Launch the interactive status monitoring TUI."""
    launch_status_tui(ctx, None, refresh_interval)
