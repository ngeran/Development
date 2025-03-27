import os
import yaml


def load_yaml(file_path):
    """
    Load a YAML file and return its contents.
    Args:
        file_path (str): Path to the YAML file
    Returns:
        dict: Parsed YAML data, or None if loading fails
    """
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found. ")
        return None
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as error:
        print(f"Error: Invalid YAML syntax in '{file_path}': {error}")
        return None
    except Exception as error:
        print(f"Unexpected Error loading '{file_path}': {error} ")
        return None

def group_devices(devices, attribute):
    """
    Group devices by a specified attribute (e.g., 'host_location', 'product_family').
    Args:
        devices (list): List of device dictionaries
        attribute (str): Key to group by
    Returns:
        dict: Devices grouped by the attribute value
    """
    grouped = {}
    for device in devices:
        # Default to Unknown if attribute is missing
        value = device.get(attribute, 'Unknown')
        if value not in grouped:
            grouped[value] = []
        grouped[value].append(device)
    return grouped

def yaml_parser(file_path="../data/hosts.yml"):
    """
    Parse a YAML file and process its data flexibly with grouping.
    Args:
        file_path (str): Path to the YAML file
    """
    # Load the YAML data
    data = load_yaml(file_path)
    if not data:
        return

    # Print raw data for debugging
    # print(f"YAML Data: {data}")
    # Access top-level keys
    print("\n=== Top-Level Keys ===")
    username = data.get('username', 'N/A')
    password = data.get('password', 'N/A')
    tables = data.get('tables', [])
    monitor_interval = data.get('monitor_interval', 0)

    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Tables: {tables}")
    print(f"Monitor Interval: {monitor_interval} seconds")

    # Process 'host' dynamicaly
    print(f"==== Hosts Data ====")
    hosts = data.get('hosts', {})
    if not hosts:
        print("No Hosts found in YAML.")
        return
    all_devices = []
    for category in hosts.keys():  # Dynamically handle any category (routers, switches, etc.)
        print(f"\n{category.capitalize()} Data:")
        for device in hosts[category]:
            host_name = device.get('host_name', 'Unknown')
            host_ip = device.get('host_ip', 'Unknown')
            host_location = device.get('host_location', 'N/A')
            function = device.get('function', 'N/A')
            product_family = device.get('product_family', 'N/A')
            ssh_port = device.get('ssh_port', None)  # Optional field
            print(f"  - {host_name} ({host_ip})")
            print(f"    Location: {host_location}")
            print(f"    Function: {function}")
            print(f"    Product Family: {product_family}")
            if ssh_port:
                print(f"    SSH Port: {ssh_port}")
            all_devices.append(device)

    # Grouping examples
    print("\n==== Grouping Examples ====")

    # Group by host_location
    by_location = group_devices(all_devices, 'host_location')
    print("\nDevices by Location:")
    for location, devices in by_location.items():
        print(f"  {location}:")
        for device in devices:
            print(f"    - {device['host_name']} ({device['host_ip']})")
        print(f"    Action: Connecting to {len(devices)} device(s) in {location}")
if __name__ == "__main__":
    yaml_parser()
