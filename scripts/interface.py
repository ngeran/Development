import os  # For file and directory operations
import sys  # For modifying sys.path to import connect_to_hosts
from jnpr.junos.utils.config import Config  # PyEZ Config class for managing configurations

# Adjust sys.path to include the scripts directory where connect_to_hosts.py resides
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of this script (scripts/)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)  # Add scripts/ to sys.path for importing

# Import connection functions from connect_to_hosts.py (in scripts/)
try:
    from connect_to_hosts import connect_to_hosts, disconnect_from_hosts
except ModuleNotFoundError as e:
    print(f"Error: Could not import connect_to_hosts: {e}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)  # Exit if import fails

# Import menu functions from menu_formater.py
try:
    from menu_formater import load_interface_actions, display_action_menu
except ModuleNotFoundError as e:
    print(f"Error: Could not import menu_formater: {e}")
    sys.exit(1)

def process_interface(dev, action):
    """Process the selected interface action on the device.

    Args:
        dev (Device): Connected PyEZ Device object.
        action (str): Action to perform ('configure', 'edit', 'delete', 'view', 'description').
    """
    hostname = dev.facts.get('hostname', 'unknown_host')
    print(f"\nProcessing {action} on {hostname} ({dev._hostname})")

    # Prompt for interface name (e.g., ge-0/0/1)
    interface = input("Enter interface name (e.g., ge-0/0/1): ").strip()

    # Create Config object for configuration changes
    config = Config(dev)

    try:
        if action == "view":
            # View interface details
            interface_data = dev.rpc.get_interface_information(interface=interface, terse=True)
            print(f"Interface {interface} details:\n{interface_data.text.strip()}")

        else:
            # Lock config for changes
            config.lock()

            if action == "configure" or action == "edit":
                # Delete existing config first for both configure and edit
                config.load(f"delete interfaces {interface}", format='set')
                print(f"Deleted existing config for {interface}")

                # Prompt for basic interface config (description and IP)
                description = input(f"Enter description for {interface}: ").strip()
                ip_address = input(f"Enter IP address for {interface} (e.g., 192.168.1.1/24) or press Enter to skip: ").strip()

                # Build set commands
                config_commands = [f"set interfaces {interface} description \"{description}\""]
                if ip_address:
                    config_commands.append(f"set interfaces {interface} unit 0 family inet address {ip_address}")

                # Load and apply config
                config.load("\n".join(config_commands), format='set')
                print(f"Configuration diff:\n{config.diff()}")
                config.commit(comment=f"{action} interface {interface} via interface.py", timeout=60)  # Increased timeout
                print(f"Interface {interface} {action}d successfully")

            elif action == "delete":
                # Delete interface config
                config.load(f"delete interfaces {interface}", format='set')
                print(f"Configuration diff:\n{config.diff()}")
                config.commit(comment=f"Deleted interface {interface} via interface.py", timeout=60)  # Increased timeout
                print(f"Interface {interface} deleted successfully")

            elif action == "description":
                # Set or update interface description only
                description = input(f"Enter description for {interface}: ").strip()
                config.load(f"set interfaces {interface} description \"{description}\"", format='set')
                print(f"Configuration diff:\n{config.diff()}")
                config.commit(comment=f"Set description for {interface} via interface.py", timeout=60)  # Increased timeout
                print(f"Interface {interface} description updated successfully")

            # Unlock config after changes
            config.unlock()

    except Exception as e:
        print(f"Failed to {action} interface {interface} on {dev._hostname}: {e}")
        # Ensure config is unlocked if an error occurs
        try:
            if 'config' in locals():
                config.unlock()
        except Exception as unlock_error:
            print(f"Error unlocking config for {dev._hostname}: {unlock_error}")

# Prompt user for SSH credentials
username = input("Enter SSH username: ")
password = input("Enter SSH password: ")

# Connect to devices
connections = connect_to_hosts(username=username, password=password)

if not connections:
    print("No devices connected. Exiting.")
    disconnect_from_hosts(connections)
    sys.exit(0)

# Load and display interface actions using menu_formater
actions = load_interface_actions()
selected_action = display_action_menu(actions)

if selected_action:
    # Process each connected device with the selected action
    for dev in connections:
        process_interface(dev, selected_action)

# Disconnect from all devices
disconnect_from_hosts(connections)
print("\nAll connections closed.")
