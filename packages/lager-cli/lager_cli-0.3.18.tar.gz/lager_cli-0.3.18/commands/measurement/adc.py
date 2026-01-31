"""
ADC (Analog-to-Digital Converter) command for reading analog voltages.

This module provides the `lager adc` command for reading voltage from ADC nets
on LabJack devices.
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


ADC_ROLE = "adc"


@click.command(name="adc", help="Read voltage from ADC net")
@click.pass_context
@click.option("--box", required=False, help="Lagerbox name or IP")
@click.argument("netname", required=False)
def adc(ctx, box, netname):
    """Read voltage from an ADC (analog-to-digital converter) net.

    If no netname is provided, lists available ADC nets.
    """
    # Use provided netname, or fall back to default if not provided
    if netname is None:
        netname = get_default_net(ctx, 'adc')

    box_ip = resolve_box(ctx, box)

    # If still no netname, list available ADC nets
    if netname is None:
        nets = list_nets_by_role(ctx, box_ip, ADC_ROLE)
        display_nets_table(nets, empty_message="No ADC nets found on this box.")
        return

    # Validate net exists before executing
    if validate_net_exists(ctx, box_ip, netname, ADC_ROLE) is None:
        return

    box_image = os.environ.get("LAGER_GATEWAY_IMAGE", "python")
    payload = json.dumps({"netname": netname})

    run_impl_script(
        ctx=ctx,
        box=box_ip,
        impl_script="adc.py",
        args=(payload,),
        image=box_image,
        timeout=None,
    )
