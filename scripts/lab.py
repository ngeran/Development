import os
import yaml
# Load the YAML file
def load_yaml(file_path: str):

    # Step 1: Verify file existence
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exists.")
        return None
    if not os.path.isfile(file_path):
        print(f"Error: '{file_path}' is not a file.")
        return None

    # Step 2: Load and parse the YAML file
    try:
        # Open file in read mode
        with open(file_path, 'r') as file:
        # Parse YAML into Python object
            yaml_data = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' could not be opened.")
        return None
    except yaml.YAMLError as error:
        print(f"Error: Invalid YAML format in '{file_path}' : {error}")
        return None
    except Exception as e:
        print(f"Error: Unexpected issue loading '{file_path}': {e}")
        return None

    # Step 3: Basic validation - check if data was loaded
    if yaml_data is None:
        print(f"Error: '{file_path}' is empty or contains no valid YAML data.")
        return None
    if not isinstance(yaml_data, dict):
        print(f"Error: '{file_path}' must parse to a dictionary, got {type(yaml_data)} instead.")
        return None
    # Success: Return the parsed data
    print(f"Successfully loaded and validated '{file_path}'.")
    return yaml_data


def yaml_parser():
    yaml_path = "../data/host.yml"
    data = load_yaml(yaml_path)
    print(f" YAML: '{data}'")
    if not data:
        return
    # Access The top Level Keys.return
    print("====Top Level Keys====")
    username = data.get('username')
    password = data.get('password')

    print(f"Username: {username}")
    print(f"Password: {password}")

    # Accessing nested 'host' dictionary
    print("\n=== Hosts Data ===")
    hosts = data.get('hosts', {})

    # Process
    if 'switches' in hosts:
        print("\nSwitch Data:")
        for switch in hosts['switches']:
            host_name = switch.get('host_name')
            host_ip = switch.get('host_ip')
            ssh_port = switch.get('ssh_port')
            print(f"  - {host_name} ({host_ip})")
            print(f"    SSH_Port: {ssh_port}")

    # Example: Using the data (e.g., connecting to devices)
    print("\n=== Example Usage ===")
    all_hosts = []
    for host in ['routers', 'switches']:
        if host in hosts:
            all_hosts.extend(hosts[host])

    print(f"All devices to connect to: {all_hosts}'")
    for host in all_hosts:
        print(f"Connecting to {host['host_name']} at {host['host_ip']} with username '{username}' ")


def main():
   yaml_parser()

if __name__ == '__main__':
    main()
