import sys
import os
import json
from lager.nets.net import Net, NetType

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def main() -> int:
    try:
        data = json.loads(sys.argv[1])
        netname = data["netname"]
        action = data["action"]
        net = Net.get(netname, type=NetType.GPIO)

        if action == "input":
            value = int(net.input())
            level_str = "HIGH" if value == 1 else "LOW"
            sys.stdout.write(f"{GREEN}GPIO '{netname}': {level_str} ({value}){RESET}\n")
            sys.stdout.flush()
            return 0

        if action == "output":
            level = data.get("level")
            if level is None:
                raise ValueError("No level provided for GPIO output")

            # Handle toggle - read current state and invert
            if level.lower() == "toggle":
                current_value = int(net.input())
                new_value = 1 if current_value == 0 else 0
                net.output(str(new_value))
                level_str = "HIGH" if new_value == 1 else "LOW"
                sys.stdout.write(f"{GREEN}GPIO '{netname}' toggled to {level_str}{RESET}\n")
            else:
                net.output(level)
                # Normalize level for display
                if level in ["1", "on", "high"]:
                    level_str = "HIGH"
                else:
                    level_str = "LOW"
                sys.stdout.write(f"{GREEN}GPIO '{netname}' set to {level_str}{RESET}\n")
            sys.stdout.flush()
            return 0

        raise ValueError(f"Invalid action '{action}'")

    except KeyError as e:
        # Handle invalid net names specifically
        sys.stderr.write(f"{RED}Error: Net '{netname}' not found{RESET}\n")
        sys.stderr.write(f"Use 'lager nets --box <box>' to list available nets\n")
        if os.getenv('LAGER_DEBUG') or os.getenv('DEBUG'):
            import traceback
            sys.stderr.write(f"\nDebug traceback:\n{traceback.format_exc()}\n")
        sys.stderr.flush()
        return 1
    except ValueError as e:
        # Handle type mismatches and value errors
        error_msg = str(e)
        if "wrong type" in error_msg.lower() or "expected" in error_msg.lower():
            sys.stderr.write(f"{RED}Error: Invalid net type for '{netname}'{RESET}\n")
            sys.stderr.write(f"This command requires a GPIO net. Use 'lager nets --box <box>' to verify net types\n")
        else:
            sys.stderr.write(f"{RED}Error: {e}{RESET}\n")
        if os.getenv('LAGER_DEBUG') or os.getenv('DEBUG'):
            import traceback
            sys.stderr.write(f"\nDebug traceback:\n{traceback.format_exc()}\n")
        sys.stderr.flush()
        return 1
    except Exception as e:
        import traceback

        # Show user-friendly error message
        sys.stderr.write(f"{RED}Error: {e}{RESET}\n")

        # Only show full traceback in debug mode
        if os.getenv('LAGER_DEBUG') or os.getenv('DEBUG'):
            sys.stderr.write(f"\nDebug traceback:\n{traceback.format_exc()}\n")
            sys.stderr.write("(Set LAGER_DEBUG=0 to hide traceback)\n")
        else:
            sys.stderr.write(f"(Set LAGER_DEBUG=1 to see full traceback)\n")

        sys.stderr.flush()
        return 1

if __name__ == "__main__":
    sys.exit(main())
