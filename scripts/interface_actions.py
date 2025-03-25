import yaml
import os
import sys
from jinja2 import Environment, FileSystemLoader

# Define the directory where this script lives (scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get absolute path of current script's directory

# Add SCRIPT_DIR to sys.path if not already present, so we can import local modules
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)  # Insert at the start of sys.path for priority


# Import connection functions from connect_to_hosts.py (in scripts/)
try:
    from connect_to_hosts import connect_to_hosts, disconnect_from_hosts
except ModuleNotFoundError as error:
    print(f"Error: Could not import connect_to_hosts: {error}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)  # Exit if import fails


# Load YAML file from data/hosts.yaml
def load_yaml(file_path: str):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Render the jinja2 templates
def render_template(template_path: str, data: dict) -> str:
    env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
    template = env.get_template(os.path.basename(template_path))
    return template.render(data)

# Configure the Device
def yaml_parser():
    file_path = os.path.join(SCRIPT_DIR, "../data/hosts.yml")
    host_data = load_yaml(file_path)
    if not host_data:
        return
    # Access the top level keys ( username, password, tables exit
    print("===Top-Level Data===")
    username = host_data.get('username')
    password = host_data.get('password')
    routing_tables = host_data.get('tables')
    monitor_interval = host_data.get('monitor_interval')

    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Tables: {routing_tables}")
    print(f"Monitor Interval: {monitor_interval} seconds")

    # Accessing nested 'hosts' dictionary
    print("\n===Host Data==")
    hosts = host_data.get('hosts', {}) # Defdult to empty dictonary if 'hosts' missing

    # Process 'routers' list
    if 'routers' in hosts:
        print("\nRouters:")
        for router in hosts['routers']: # iterate over list of router dictionary
            host_name = router.get('host_name')
            host_ip = router.get('host_ip')
            host_location = router.get('host_location')
            function = router.get('function')
            product_family = router.get('product_family')
            print(f"  - {host_name} ({host_ip})")
            print(f"    Location: {host_location}")
            print(f"    Function: {function}")
            print(f"    Product Family: {product_family}")

    if 'switches' in hosts:
        print("\nSwitches")
        for switch in hosts['switches']: # iterate over list of dictionaries
            host_name = switch.get('host_name')
            host_ip = switch.get('host_ip')
            host_location = switch.get('host_location')
            function = switch.get('function')
            product_family = switch.get('product_family')
            print(f"  - {host_name} ({host_ip})")
            print(f"    Location: {host_location}")
            print(f"    Function: {function}")
            print(f"    Product Family: {product_family}")
    # Example: Using the data (e.g., connecting to devices)
    print("\n=== Example Usage ===")
    all_devices = []
    for category in ['routers', 'switches']:  # Combine all devices into one list
        if category in hosts:
            all_devices.extend(hosts[category])  # Add devices from this category

    print("All devices to connect to:")
    for device in all_devices:
        print(f"Connecting to {device['host_name']} at {device['host_ip']} with username '{username}'")


        connect_to_hosts(username, password)

if __name__ == "__main__":
    yaml_parser()
