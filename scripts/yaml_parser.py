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
    parser.add_argument('--actions', nargs='+', choices=['interfaces', 'bgp', 'ospf', 'ldp', 'rsvp', 'mpls'], help='Actions to perform')
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

    # Execute actions based on user input
    if 'interfaces' in args.actions:
        from interface_actions import configure_interfaces
        configure_interfaces(
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            template_name='interface_template.j2',
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts
        )
    if any(action in ['bgp', 'ospf', 'ldp', 'rsvp', 'mpls'] for action in args.actions):
        from routing_protocols import configure_routing  # Updated import
        protocols = [action for action in args.actions if action in ['bgp', 'ospf', 'ldp', 'rsvp', 'mpls']]
        configure_routing(
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts,
            protocols=protocols
        )

if __name__ == "__main__":
    main()
