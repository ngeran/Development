# scripts/interface_actions.py
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import RpcTimeoutError
from utils import render_template, check_config

def configure_interfaces(username, password, host_ips, hosts, template_name, connect_to_hosts, disconnect_from_hosts):
    """
    Apply interface configurations to specified devices.
    Args:
        username (str): SSH username for device login
        password (str): SSH password for device login
        host_ips (list): List of IP addresses to configure
        hosts (list): List of host dictionaries with config data
        template_name (str): Name of the Jinja2 template file (e.g., 'interface_template.j2')
        connect_to_hosts (callable): Function to connect to devices
        disconnect_from_hosts (callable): Function to disconnect from devices
    """
    # Connect to the devices using the provided IPs
    connections = connect_to_hosts(username=username, password=password, host_ips=host_ips)
    if not connections:
        print("No devices connected for interface configuration.")
        return

    # Debug: Show connected devices
    print(f"Debug: Connected to {[dev.hostname for dev in connections]}")

    # Create a lookup dictionary by IP address
    host_lookup = {h['ip_address']: h for h in hosts}
    # Loop through each connected device
    for dev in connections:
        # Use the IP address to find the host data (assuming dev.hostname is the IP)
        host_data = host_lookup.get(dev.hostname)
        if not host_data or 'interfaces' not in host_data:
            print(f"No interface config data for {dev.hostname} ({dev.hostname}). Skipping.")
            continue
        try:
            # Render the config using the template and host data
            config = render_template(host_data, template_name)
            if not config:
                print(f"Failed to render template for {dev.hostname}. Skipping.")
                continue
            # Show the user what’s about to be applied
            print(f"\nConfiguration to be applied to {dev.hostname} ({host_ips[0]}):\n{config}")
            # Check the config for errors
            check_passed, check_message = check_config(dev, config)
            print(check_message)
            if not check_passed:
                print(f"Skipping commit on {dev.hostname} due to configuration errors.")
                continue
            # Apply the config to the device
            configuration = Config(dev)
            configuration.load(config, format='set', merge=False)
            configuration.pdiff()
            configuration.commit(comment="Change CHG0123456 - interfaces", timeout=120)
            print(f"Interfaces configured on {dev.hostname}")
        except RpcTimeoutError as error:
            print(f"Timeout during commit to {dev.hostname}: {error}")
            print("Config may have applied; verify on device.")
        except Exception as error:
            print(f"Failed to configure interfaces on {dev.hostname}: {error}")
    # Disconnect from all devices
    disconnect_from_hosts(connections)
