"""
Communication Commands Package

This package groups communication-related CLI commands:
- uart: UART serial port connection and communication
- ble: Bluetooth Low Energy scanning and device interaction
- wifi: WiFi network management and configuration
- usb: USB hub port control (enable/disable/toggle)
- spi: SPI (Serial Peripheral Interface) communication

All commands handle serial, wireless, and USB communication with devices
connected to the Lager box.
"""

from .uart import uart
from .ble import ble
from .wifi import _wifi
from .usb import usb
from .spi import spi

__all__ = [
    "uart",
    "ble",
    "_wifi",
    "usb",
    "spi",
]
