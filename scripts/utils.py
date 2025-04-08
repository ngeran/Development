# scripts/utils.py
import os
import yaml
import jinja2
from jnpr.junos.utils.config import Config

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, '../templates')

def load_yaml(file_path):
    """Load a YAML file and return its contents as a Python object."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return None
    try:
        with open(file_path, 'r') as file:
            raw_content = file.read()
            print(f"Debug: Raw content of '{file_path}':\n{raw_content}")
            return yaml.load(raw_content, Loader=yaml.SafeLoader)  # Explicit SafeLoader
    except yaml.YAMLError as error:
        print(f"Error: Invalid YAML syntax in '{file_path}': {error}")
        return None
    except Exception as error:
        print(f"Unexpected Error loading '{file_path}': {error}")
        return None

def group_devices(devices, attribute):
    """Group a list of devices by a specific attribute (e.g., 'location' or 'vendor')."""
    grouped = {}
    for device in devices:
        value = device.get(attribute, 'Unknown')
        if value not in grouped:
            grouped[value] = []
        grouped[value].append(device)
    return grouped

def render_template(host, template_name):
    """Render a Jinja2 template with host data (e.g., to generate config commands)."""
    if not os.path.exists(TEMPLATE_DIR):
        print(f"Error: Template directory '{TEMPLATE_DIR}' does not exist.")
        return None
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))
    try:
        template = env.get_template(template_name)
    except jinja2.exceptions.TemplateNotFound as error:
        print(f"Error loading template '{template_name}' in '{TEMPLATE_DIR}': {error}")
        return None
    config = template.render(hosts=[host])
    return config

def check_config(device, config_str):
    try:
        config = Config(device)
        config.load(config_str, format='set', merge=False)
        diff = config.diff()
        diff_msg = "No changes to apply." if diff is None else f"Configuration diff:\n{diff}"
        if config.commit_check(timeout=60):  # Increase to 60 seconds
            return True, diff_msg
        else:
            return False, "Commit check failed - configuration has errors."
    except Exception as error:
        return False, f"Error checking configuration: {error}"

def merge_host_data(inventory_file, config_file=None):
    inventory_data = load_yaml(inventory_file)
    if not inventory_data:
        return None
    print(f"Debug: Loading from path = {os.path.abspath(inventory_file)}")
    print(f"Debug: Loaded inventory_data = {inventory_data}")
    if 'locations' in inventory_data:
        inventory_data = inventory_data['locations']  # Extract the list
    if isinstance(inventory_data, dict):
        print("Debug: inventory_data is a dict, wrapping it in a list")
        inventory_data = [inventory_data]
    elif not isinstance(inventory_data, list):
        print(f"Error: Expected 'inventory.yml' to be a list or dict, got {type(inventory_data)}.")
        return None

    # Build a flat list of all devices from inventory
    all_hosts = []
    for location_dict in inventory_data:
        print(f"Debug: Processing location_dict = {location_dict}")
        if not isinstance(location_dict, dict) or 'location' not in location_dict:
            print("Error: Invalid format in 'inventory.yml' - each entry must have a 'location' key.")
            return None
        for dev_type in ['switches', 'routers', 'firewalls']:
            print(f"Debug: Checking dev_type = {dev_type}")
            if dev_type in location_dict:
                print(f"Debug: Found {len(location_dict[dev_type])} devices in {dev_type}")
                for dev in location_dict[dev_type]:
                    all_hosts.append({
                        'host_name': dev['host_name'],
                        'ip_address': dev['ip_address'],
                        'location': location_dict['location'],
                        'device_type': dev_type[:-1],
                        'vendor': dev.get('vendor', 'Unknown')
                    })

    print(f"Debug: Collected {len(all_hosts)} hosts: {[h['host_name'] for h in all_hosts]}")

    # If no config file, return all inventory hosts (for non-config actions)
    if not config_file:
        return {
            'username': 'admin',
            'password': 'password',
            'hosts': all_hosts
        }

    # Load config file (hosts_data.yml)
    config_data = load_yaml(config_file)
    if not config_data:
        return None

    print(f"Debug: Loaded config_data = {config_data}")

    # Only include hosts from inventory that match hosts_data.yml
    host_lookup = {h['host_name']: h for h in all_hosts}
    merged_hosts = []
    for config_host in config_data.get('hosts', []):
        host_name = config_host['host_name']
        if host_name in host_lookup:
            merged_host = host_lookup[host_name].copy()
            merged_host.update(config_host)
            merged_hosts.append(merged_host)
        else:
            print(f"Warning: Host '{host_name}' in hosts_data.yml not found in inventory.yml")

    if not merged_hosts:
        print("Error: No hosts from hosts_data.yml matched inventory.yml")
        return None

    print(f"Debug: Merged {len(merged_hosts)} hosts: {[h['host_name'] for h in merged_hosts]}")

    return {
        'username': config_data.get('username', 'admin'),
        'password': config_data.get('password', 'password'),
        'hosts': merged_hosts
    }
