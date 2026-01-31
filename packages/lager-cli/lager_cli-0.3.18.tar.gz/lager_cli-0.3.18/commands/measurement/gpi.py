"""
GPI (GPIO Input) command for reading digital input states.

This module provides the `lager gpi` command for reading GPIO input state
(0 or 1) from LabJack devices.
"""
from __future__ import annotations

import json
import os

import click

from ...context import get_default_net
from ...core.net_helpers import (
    resolve_box,
    list_nets_by_role,
    display_nets_table,
    run_impl_script,
    validate_net_exists,
)


GPIO_ROLE = "gpio"


@click.command(name="gpi", help="Read GPIO input state (0 or 1)")
@click.pass_context
@click.option("--box", required=False, help="Lagerbox name or IP")
@click.argument("netname", required=False)
def gpi(ctx, box, netname):
    """Read the state of a GPIO input net.

    Returns 0 (low) or 1 (high).
    If no netname is provided, lists available GPIO nets.
    """
    # Use provided netname, or fall back to default if not provided
    if netname is None:
        netname = get_default_net(ctx, 'gpio')

    box_ip = resolve_box(ctx, box)

    # If still no netname, list available GPIO nets
    if netname is None:
        nets = list_nets_by_role(ctx, box_ip, GPIO_ROLE)
        display_nets_table(nets, empty_message="No GPIO nets found on this box.")
        return

    # Validate net exists with GPIO role
    net = validate_net_exists(ctx, box_ip, netname, GPIO_ROLE)
    if net is None:
        return  # Error already displayed

    box_image = os.environ.get("LAGER_GATEWAY_IMAGE", "python")
    payload = json.dumps({"netname": netname, "action": "input"})

    run_impl_script(
        ctx=ctx,
        box=box_ip,
        impl_script="gpio.py",
        args=(payload,),
        image=box_image,
        timeout=None,
    )
