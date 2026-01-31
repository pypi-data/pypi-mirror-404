"""
Core utilities for the Lager CLI.

This package consolidates shared functionality used across CLI commands,
providing a single import point for common utilities. It replaces scattered
helper modules to reduce code duplication and improve maintainability.

Submodules:
    net_helpers: Net resolution, validation, and command execution helpers
    box_helpers: Box resolution, connection validation utilities
    display: Table display and output formatting utilities
    param_types: Custom Click parameter types
    utils: General utility functions (SSH, file operations, etc.)

Example usage:
    from cli.core import require_netname, resolve_box, run_net_py
    from cli.core import display_nets_table
    from cli.core.param_types import AddressType

Note:
    For backward compatibility, the original module locations (e.g.,
    cli.shared.net_commands, cli.paramtypes, cli.util) continue to work
    via re-export stubs.
"""

# Submodule status:
#
# IMPLEMENTED:
#   - param_types (Session 1, Part 1.3): Custom Click parameter types
#   - utils (Session 1, Part 1.4): Stream output, heartbeat, zip_dir, etc.
#   - ssh_utils (Session 1, Part 1.4): SSH connection pool management
#   - matchers (Session 1, Part 1.5): Test output matchers
#   - net_storage (Session 1, Part 1.5): Net storage utilities
#   - net_helpers (Session 1, Part 1.2): Net resolution, validation, command execution
#
# FUTURE:
#   - box_helpers: resolve_box_address, validate_box_connection, get_box_info
#   - display: format_table, print_status, format_error

# param_types - Custom Click parameter types (Session 1, Part 1.3)
from .param_types import (
    MemoryAddressType,
    HexParamType,
    HexArrayType,
    VarAssignmentType,
    EnvVarType,
    Binfile,
    BinfileType,
    CanFrame,
    CanFilter,
    PortForwardSpecifier,
    CanFrameType,
    CanFilterType,
    ADCChannelType,
    CanbusRange,
    PortForwardType,
    grouper,
    parse_can_data,
    parse_can2,
    parse_canfd,
)

# utils - General utility functions (Session 1, Part 1.4)
from .utils import (
    FAILED_TO_RETRIEVE_EXIT_CODE,
    SIGTERM_EXIT_CODE,
    SIGKILL_EXIT_CODE,
    EXIT_FILENO,
    STDOUT_FILENO,
    STDERR_FILENO,
    OUTPUT_CHANNEL_FILENO,
    StreamDatatypes,
    OutputHandler,
    SizeLimitExceeded,
    stream_output,
    stdout_is_stderr,
    identity,
    stream_python_output_v1,
    stream_python_output,
    heartbeat,
    handle_error,
    zip_dir,
)

# ssh_utils - SSH connection management (Session 1, Part 1.4)
from .ssh_utils import (
    SSHConnectionPool,
    get_ssh_connection_pool,
    get_reusable_ssh_command,
)

# matchers - Test output matchers (Session 1, Part 1.5)
from .matchers import (
    test_matcher_factory,
    echo_line,
    V1ParseStates,
    iter_streams,
    UnityMatcher,
    FixtureMatcher,
    PTTYMatcher,
    EmptyMatcher,
    safe_decode,
    EndsWithMatcher,
)

# net_storage - Net storage utilities (Session 1, Part 1.5)
from .net_storage import (
    get_lager_file_path,
    load_nets,
    save_nets,
    add_net,
    delete_net,
    list_nets,
)

# net_helpers - Net resolution, validation, and command execution (Session 1, Part 1.2)
from .net_helpers import (
    # Box operations
    resolve_box,
    # Netname operations
    require_netname,
    get_netname_or_none,
    # Net operations
    run_net_py,
    list_nets_by_role,
    validate_net,
    find_net_by_name,
    # Display operations
    display_nets,
    display_nets_table,
    # Backend execution
    run_backend,
    run_backend_with_env,
    run_impl_script,
    # Validation helpers
    validate_positive_float,
    validate_positive_parameters,
    validate_protection_limits,
    # Callback helpers
    parse_value_with_negatives,
    # Role constants
    NET_ROLES,
    get_role,
)

__all__ = [
    # param_types exports
    'MemoryAddressType',
    'HexParamType',
    'HexArrayType',
    'VarAssignmentType',
    'EnvVarType',
    'Binfile',
    'BinfileType',
    'CanFrame',
    'CanFilter',
    'PortForwardSpecifier',
    'CanFrameType',
    'CanFilterType',
    'ADCChannelType',
    'CanbusRange',
    'PortForwardType',
    'grouper',
    'parse_can_data',
    'parse_can2',
    'parse_canfd',
    # utils exports
    'FAILED_TO_RETRIEVE_EXIT_CODE',
    'SIGTERM_EXIT_CODE',
    'SIGKILL_EXIT_CODE',
    'EXIT_FILENO',
    'STDOUT_FILENO',
    'STDERR_FILENO',
    'OUTPUT_CHANNEL_FILENO',
    'StreamDatatypes',
    'OutputHandler',
    'SizeLimitExceeded',
    'stream_output',
    'stdout_is_stderr',
    'identity',
    'stream_python_output_v1',
    'stream_python_output',
    'heartbeat',
    'handle_error',
    'zip_dir',
    # ssh_utils exports
    'SSHConnectionPool',
    'get_ssh_connection_pool',
    'get_reusable_ssh_command',
    # matchers exports
    'test_matcher_factory',
    'echo_line',
    'V1ParseStates',
    'iter_streams',
    'UnityMatcher',
    'FixtureMatcher',
    'PTTYMatcher',
    'EmptyMatcher',
    'safe_decode',
    'EndsWithMatcher',
    # net_storage exports
    'get_lager_file_path',
    'load_nets',
    'save_nets',
    'add_net',
    'delete_net',
    'list_nets',
    # net_helpers exports - Box operations
    'resolve_box',
    # net_helpers exports - Netname operations
    'require_netname',
    'get_netname_or_none',
    # net_helpers exports - Net operations
    'run_net_py',
    'list_nets_by_role',
    'validate_net',
    'find_net_by_name',
    # net_helpers exports - Display operations
    'display_nets',
    'display_nets_table',
    # net_helpers exports - Backend execution
    'run_backend',
    'run_backend_with_env',
    'run_impl_script',
    # net_helpers exports - Validation
    'validate_positive_float',
    'validate_positive_parameters',
    'validate_protection_limits',
    # net_helpers exports - Callback helpers
    'parse_value_with_negatives',
    # net_helpers exports - Role constants
    'NET_ROLES',
    'get_role',
]
