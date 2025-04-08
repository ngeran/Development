import os
import yaml

def load_yaml(file_path):
    """Load a YAML file and return its contents as a Python object."""
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return None
    try:
        # Open and parse the YAML file safely
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as error:
        # Handle YAML syntax errors
        print(f"Error: Invalid YAML syntax in '{file_path}': {error}")
        return None
    except Exception as error:
        # Catch any unexpected errors during file loading
        print(f"Unexpected Error loading '{file_path}': {error}")
        return None

def merge_host_data(inventory_file, config_file=None):
    """Merge host data from inventory.yml and optionally hosts_data.yml."""
    # Load inventory data
    inventory_data = load_yaml(inventory_file)
    if not inventory_data:
        return None

    # Ensure inventory_data is a list (wrap single dict if needed)
    if isinstance(inventory_data, dict):
        inventory_data = [inventory_data]
    elif not isinstance(inventory_data, list):
        print(f"Error: Expected 'inventory.yml' to be a list or dict, got {type(inventory_data)}.")
        return None

    # Build a list of all hosts from inventory
    all_hosts = []
    for location_dict in inventory_data:
        # Validate each location entry has a 'location' key
        if not isinstance(location_dict, dict) or 'location' not in location_dict:
            print("Error: Invalid format in 'inventory.yml' - each entry must have a 'location' key.")
            return None
        # Iterate over device types (switches, routers, firewalls)
        for dev_type in ['switches', 'routers', 'firewalls']:
            if dev_type in location_dict:
                # Add each device to the host list with relevant details
                for dev in location_dict[dev_type]:
                    all_hosts.append({
                        'host_name': dev['host_name'],
                        'ip_address': dev['ip_address'],
                        'location': location_dict['location'],
                        'device_type': dev_type[:-1],  # Remove 's' (e.g., 'switches' -> 'switch')
                        'vendor': dev.get('vendor', 'Unknown')  # Default to 'Unknown' if vendor missing
                    })

    # If config_file is provided, merge with config data
    if config_file:
        config_data = load_yaml(config_file)
        if not config_data:
            print("Failed to load host data. Check files for errors.")
            return None
        # Extract credentials and host list from config
        config_hosts = config_data.get('hosts', [])
        username = config_data.get('username')
        password = config_data.get('password')
        if not (username and password):
            print("Error: 'username' and 'password' must be specified in hosts_data.yml.")
            return None

        # Merge inventory hosts with config hosts where names match
        merged_hosts = []
        config_host_names = {host['host_name'] for host in config_hosts}
        for inv_host in all_hosts:
            if inv_host['host_name'] in config_host_names:
                for config_host in config_hosts:
                    if config_host['host_name'] == inv_host['host_name']:
                        # Combine inventory and config data for matching hosts
                        merged_host = inv_host.copy()
                        merged_host.update(config_host)
                        merged_hosts.append(merged_host)
                        break
            else:
                print(f"Warning: Host '{inv_host['host_name']}' in inventory.yml not found in hosts_data.yml")
        return {'username': username, 'password': password, 'hosts': merged_hosts}

    # Return just inventory hosts if no config file
    return {'hosts': all_hosts}

def render_template(host_data, template_name):
    """Render a Jinja2 template with host data."""
    from jinja2 import Environment, FileSystemLoader
    template_dir = os.path.join(os.path.dirname(__file__), '../templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    try:
        template = env.get_template(template_name)
        return template.render(**host_data)
    except Exception as error:
        print(f"Error rendering template '{template_name}': {error}")
        print(f"Host data passed: {host_data}")
        return None

def check_config(device, config_str):
    """Check if the configuration can be applied to the device."""
    from jnpr.junos.utils.config import Config
    try:
        # Load config into a Config object for validation
        config = Config(device)
        config.load(config_str, format='set', merge=False)
        # Get the diff (changes to apply)
        diff = config.diff()
        diff_msg = "No changes to apply." if diff is None else f"Configuration diff:\n{diff}"
        # Perform a commit check with a 60-second timeout
        if config.commit_check(timeout=60):
            return True, diff_msg
        else:
            return False, "Commit check failed - configuration has errors."
    except Exception as error:
        return False, f"Error checking configuration: {error}"
