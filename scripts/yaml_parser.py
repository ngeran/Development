import os
import argparse
from utils import merge_host_data
from connect_to_hosts import connect_to_hosts, disconnect_from_hosts

# Define the script directory for relative file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    """Parse arguments and execute specified actions."""
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description='Network device configuration script')
    parser.add_argument('--actions', nargs='+', choices=['interfaces'], help='Actions to perform')
    args = parser.parse_args()

    # Define paths to inventory and config files
    inventory_file = os.path.join(SCRIPT_DIR, "../data/inventory.yml")
    config_file = os.path.join(SCRIPT_DIR, "../data/hosts_data.yml")

    # Merge data from inventory and config files
    merged_data = merge_host_data(inventory_file, config_file)
    if not merged_data:
        print("Failed to merge host data. Exiting.")
        return

    # Extract credentials and host list
    username = merged_data.get('username')
    password = merged_data.get('password')
    hosts = merged_data.get('hosts', [])
    host_ips = [host['ip_address'] for host in hosts]

    # Execute the interfaces action if specified
    if 'interfaces' in args.actions:
        from interface_actions import configure_interfaces
        configure_interfaces(
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            template_name='interface_template.j2',  # Template file for interface configs
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts
        )

if __name__ == "__main__":
    main()
