"""
Backward compatibility stub for cli.uart.websocket_client module.

This module has been moved to cli.commands.communication.websocket_client.
This stub provides re-exports for backward compatibility.
"""

from cli.commands.communication.websocket_client import (
    UARTWebSocketClient,
    connect_uart_interactive,
    connect_uart_readonly,
)

__all__ = [
    "UARTWebSocketClient",
    "connect_uart_interactive",
    "connect_uart_readonly",
]
