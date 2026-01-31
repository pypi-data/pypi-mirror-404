"""
CLI commands package.

This package contains grouped command modules organized by domain:
- measurement/: ADC, DAC, GPI, GPO, scope, logic, thermocouple, watt commands
- power/: Power supply, battery, solar, eload commands
- communication/: UART, BLE, WiFi, USB commands
- development/: Debug, ARM, Python commands
- box/: Hello, status, boxes, instruments, nets, SSH commands
- utility/: Defaults, binaries, update, pip, exec, logs, webcam commands
"""

# Import measurement commands
from .measurement import (
    adc,
    dac,
    gpi,
    gpo,
    scope,
    logic,
    thermocouple,
    watt,
)

# Import communication commands
from .communication import (
    uart,
)

# Power commands will be imported here once migrated:
# from .power import supply, battery, solar, eload

# Import box commands
from .box import (
    hello,
    status,
    boxes,
    instruments,
    nets,
    ssh,
)

# Import utility commands
from .utility import (
    defaults,
    binaries,
    update,
    pip,
    exec_,
    logs,
    webcam,
)

__all__ = [
    # Measurement commands
    "adc",
    "dac",
    "gpi",
    "gpo",
    "scope",
    "logic",
    "thermocouple",
    "watt",
    # Communication commands
    "uart",
    # Power commands (to be added):
    # "supply",
    # "battery",
    # "solar",
    # "eload",
    # Box commands
    "hello",
    "status",
    "boxes",
    "instruments",
    "nets",
    "ssh",
    # Utility commands
    "defaults",
    "binaries",
    "update",
    "pip",
    "exec_",
    "logs",
    "webcam",
]
