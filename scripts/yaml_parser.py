# scripts/yaml_parser.py
import os
import sys
import argparse
from typing import List
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import RpcTimeoutError

# Import for utils and connect_to_hosts
from utils import load_yaml, render_template, group_devices

try:
    from connect_to_hosts import connect_to_hosts, disconnect_from_hosts
except ModuleNotFoundError as error:
    print(f'Error: Could not import connect_to_hosts: {error}')
    sys.exit(1)

# Get absolute path of current script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add SCRIPT_DIR to sys.path if not already present, so we can import local modules
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

def yaml_parser(file_path=os.path.join(SCRIPT_DIR, "../data/hosts_data.yml")):
    """
    Parse a YAML file and process its data flexibly with grouping.
    Args:
        file_path (str): Path to the YAML file
    """
    # Load the YAML data
    data = load_yaml(file_path)
    if not data:
        # print("Failed to load YAML.")
        return None

    # Extract the 'hosts' data from the YAML
    hosts = data.get('hosts', [])
    if not hosts:
        # print("No Hosts found in YAML.")
        return None

    username = data.get('username', 'N/A')
    password = data.get('password', 'N/A')
    # tables = data.get('tables', [])

    # Removed debug prints
    # print("\n=== Top-Level Keys ===")
    # print(f"Username: {username}")
    # print(f"Password: {password}")
    # print(f"Tables: {tables}")
    # for routing_table in data['tables']:
    #     print(f" - {routing_table}")
    # print("==== Hosts Data ====")
    # for host in hosts:
    #     host_name = host['host_name']
    #     host_ip = host['host_ip']
    #     print(f" HOST NAME: {host_name}")
    #     print(f"HOST_IP: {host_ip}")
    #     for interface in host['interfaces']:
    #         interface_name = interface['name']
    #         interface_description = interface['description']
    #         unit = interface['unit']
    #         interface_ip = interface['ip_address']
    #         print(f"  Name: {interface_name}")
    #         print(f"  Description: {interface_description}")
    #         print(f"  Unit: {unit}")
    #         print(f"  IP Address: {interface_ip}")

    # Return the host data to use it in rendering the template
    return {'hosts': hosts, 'username': username, 'password': password}

def apply_configuration(username: str, password: str, host_ips: List[str], config: str):
    """
    Connect to hosts, apply the configuration, and disconnect.
    """
    # Connect to all devices using credentials and the host_ips
    connections = connect_to_hosts(username=username, password=password, host_ips=host_ips)

    # Check if any connections were successful
    if not connections:
        # print("No devices connected. Exiting.")
        sys.exit(0)

    # Removed debug prints
    # print(f"Applying to IPs: {host_ips}\nConfig:\n{config}")

    # Apply the configuration to each connected host
    for host in connections:
        try:
            configuration = Config(host)
            # Load configuration to the devices - overwrite to prevent duplicates
            configuration.load(config, format='set', merge=False)
            # Preview Change - only output we want
            configuration.pdiff()
            # Validate config syntax
            configuration.commit(comment="Change CHG0123456", timeout=120)
            # print(f"Configuration applied to {host.hostname}")
        except RpcTimeoutError as error:
            print(f"Timeout during commit to {host.hostname}: {error}")
            print(f"Config may have applied; verify on device.")
        except Exception as error:
            print(f"Failed to apply configuration to {host.hostname}: {error}")

    # Disconnect from hosts after applying the configuration
    disconnect_from_hosts(connections)

def main(filter_by=None, filter_value=None, template_name=None):
    """Apply configurations to devices matching a filter using a user-specified template."""
    host_data = yaml_parser()
    if not host_data:
        return

    hosts = host_data['hosts']
    if filter_by and filter_value:
        grouped = group_devices(hosts, filter_by)
        filtered_hosts = grouped.get(filter_value, [])
        if not filtered_hosts:
            # print(f"No devices found with {filter_by}='{filter_value}'.")
            return
        # print(f"Applying configuration to {len(filtered_hosts)} devices with {filter_by}='{filter_value}':")
    else:
        filtered_hosts = hosts
        # print("Applying configuration to all devices:")

    for host in filtered_hosts:
        # print(f"Processing {host['host_name']} ({host['host_ip']})...")
        config = render_template(host, template_name)
        if config:
            apply_configuration(
                username=host_data['username'],
                password=host_data['password'],
                host_ips=[host['host_ip']],
                config=config
            )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply configurations from hosts_data.yml using a specified template.")
    parser.add_argument('--template', required=True, help="Name of the Jinja2 template file (e.g., 'interface_template.j2')")
    parser.add_argument('--filter-by', choices=['function', 'product_family'], help="Filter devices by this attribute")
    parser.add_argument('--filter-value', help="Value to filter by (e.g., 'Firewall', 'SRX320')")
    args = parser.parse_args()

    main(filter_by=args.filter_by, filter_value=args.filter_value, template_name=args.template)
