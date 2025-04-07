# scripts/yaml_parser.py
import os  # For file path handling
import sys  # For system path and exit
import argparse  # For command-line argument parsing
import importlib  # For dynamically importing action scripts

from utils import merge_host_data  # Import our utility function

# Try to import connection functions; fail gracefully if missing
try:
    from connect_to_hosts import connect_to_hosts, disconnect_from_hosts
except ModuleNotFoundError as error:
    print(f'Error: Could not import connect_to_hosts: {error}')
    sys.exit(1)

# Define the directory where this script lives (scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Add it to sys.path so imports work from anywhere
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

def main(locations=None, device_types=None, vendors=None, actions=None):
    """Main function to process command-line args and execute actions."""
    # Define file paths relative to the script’s location
    inventory_file = os.path.join(SCRIPT_DIR, "../data/inventory.yml")
    # Only load config file if the action needs it (e.g., 'interfaces' or 'bgp')
    config_file = os.path.join(SCRIPT_DIR, "../data/hosts_data.yml") if any(a in ['interfaces', 'bgp'] for a in actions) else None

    # Check if inventory file exists before proceeding
    if not os.path.exists(inventory_file):
        print(f"Error: Inventory file not found at '{inventory_file}'. Please ensure it exists in the 'data/' directory.")
        return

    # Load and merge data from inventory and (optionally) config files
    host_data = merge_host_data(inventory_file, config_file)
    if not host_data:
        return  # Exit if data loading failed

    # Start with all hosts from the merged data
    filtered_hosts = host_data['hosts']
    # Filter by location if specified (e.g., --locations DC1 SP1)
    if locations:
        filtered_hosts = [h for h in filtered_hosts if h['location'] in locations]
    # Filter by device type if specified (e.g., --device-types switch)
    if device_types:
        filtered_hosts = [h for h in filtered_hosts if h['device_type'] in device_types]
    # Filter by vendor if specified (e.g., --vendors Juniper)
    if vendors:
        filtered_hosts = [h for h in filtered_hosts if h['vendor'] in vendors]

    # If no hosts match the filters, stop here
    if not filtered_hosts:
        print("No matching hosts found.")
        return

    # Map actions to their scripts, functions, and templates
    action_scripts = {
        'interfaces': ('interface_actions', 'configure_interfaces', 'interface_template.j2'),
        # More actions will go here later, e.g., 'bgp': ('routing_actions', 'configure_bgp', 'bgp_template.j2')
    }

    # Process each requested action
    for action in actions:
        if action not in action_scripts:
            print(f"Action '{action}' not yet implemented. Skipping.")
            continue

        # Get the module, function, and template for this action
        module_name, func_name, template_name = action_scripts[action]
        try:
            # Dynamically import the action script (e.g., interface_actions)
            module = importlib.import_module(module_name)
            # Get the specific function (e.g., configure_interfaces)
            action_func = getattr(module, func_name)
        except ImportError as error:
            print(f"Failed to import {module_name}: {error}")
            continue
        except AttributeError as error:
            print(f"Function {func_name} not found in {module_name}: {error}")
            continue

        # For now, only target IPs 172.27.200.200 and 172.27.200.201
        host_ips = [h['ip_address'] for h in filtered_hosts if h['ip_address'] in ['172.27.200.200', '172.27.200.201']]
        if not host_ips:
            print(f"No matching IPs (172.27.200.200, 172.27.200.201) for {action}. Skipping.")
            continue

        # Call the action function with all required arguments
        action_func(
            username=host_data['username'],
            password=host_data['password'],
            host_ips=host_ips,
            hosts=filtered_hosts,
            template_name=template_name,
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts
        )

if __name__ == "__main__":
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Perform tasks on devices from inventory.yml and optionally hosts_data.yml.")
    parser.add_argument('--locations', nargs='+', help="List of locations (e.g., SP1 ORION)")
    parser.add_argument('--device-types', nargs='+', choices=['switch', 'router', 'firewall'], help="List of device types")
    parser.add_argument('--vendors', nargs='+', choices=['Juniper', 'Cisco', 'Palo_Alto', 'F5'], help="List of vendors")
    parser.add_argument('--actions', nargs='+', choices=['interfaces'], required=True, help="List of actions to perform")
    # Parse the arguments from the command line
    args = parser.parse_args()

    # Run the main function with the parsed arguments
    main(locations=args.locations, device_types=args.device_types, vendors=args.vendors, actions=args.actions)
