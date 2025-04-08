# scripts/yaml_parser.py
import os
import sys
import argparse
import importlib

from utils import merge_host_data

try:
    from connect_to_hosts import connect_to_hosts, disconnect_from_hosts
except ModuleNotFoundError as error:
    print(f'Error: Could not import connect_to_hosts: {error}')
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

def main(locations=None, device_types=None, vendors=None, actions=None):
    """Main function to process command-line args and execute actions."""
    inventory_file = os.path.join(SCRIPT_DIR, "../data/inventory.yml")
    config_file = os.path.join(SCRIPT_DIR, "../data/hosts_data.yml") if any(a in ['interfaces', 'bgp'] for a in actions) else None

    if not os.path.exists(inventory_file):
        print(f"Error: Inventory file not found at '{inventory_file}'. Please ensure it exists in the 'data/' directory.")
        return

    host_data = merge_host_data(inventory_file, config_file)
    if not host_data:
        print("Failed to load host data. Check files for errors.")
        return

    filtered_hosts = host_data['hosts']
    if locations:
        filtered_hosts = [h for h in filtered_hosts if h['location'] in locations]
    if device_types:
        filtered_hosts = [h for h in filtered_hosts if h['device_type'] in device_types]
    if vendors:
        filtered_hosts = [h for h in filtered_hosts if h['vendor'] in vendors]

    if not filtered_hosts:
        print("No matching hosts found.")
        return

    action_scripts = {
        'interfaces': ('interface_actions', 'configure_interfaces', 'interface_template.j2'),
    }

    for action in actions:
        if action not in action_scripts:
            print(f"Action '{action}' not yet implemented. Skipping.")
            continue

        module_name, func_name, template_name = action_scripts[action]
        try:
            print(f"Importing {module_name}...")
            module = importlib.import_module(module_name)
            action_func = getattr(module, func_name)
        except ImportError as error:
            print(f"Failed to import {module_name}: {error}")
            continue
        except AttributeError as error:
            print(f"Function {func_name} not found in {module_name}: {error}")
            continue

        # Use all IPs from filtered_hosts, which are tied to hosts_data.yml when config_file is provided
        host_ips = [h['ip_address'] for h in filtered_hosts]
        print(f"Debug: Targeting IPs = {host_ips}")

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
    parser = argparse.ArgumentParser(description="Perform tasks on devices from inventory.yml and optionally hosts_data.yml.")
    parser.add_argument('--locations', nargs='+', help="List of locations (e.g., SP1 ORION)")
    parser.add_argument('--device-types', nargs='+', choices=['switch', 'router', 'firewall'], help="List of device types")
    parser.add_argument('--vendors', nargs='+', choices=['Juniper', 'Cisco', 'Palo_Alto', 'F5'], help="List of vendors")
    parser.add_argument('--actions', nargs='+', choices=['interfaces'], required=True, help="List of actions to perform")
    args = parser.parse_args()

    main(locations=args.locations, device_types=args.device_types, vendors=args.vendors, actions=args.actions)
