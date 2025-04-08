from jnpr.junos.utils.config import Config
from jnpr.junos.exception import RpcTimeoutError
from utils import render_template, check_config

def configure_interfaces(username, password, host_ips, hosts, template_name, connect_to_hosts, disconnect_from_hosts):
    """Apply interface configurations to specified devices."""
    # Connect to all specified devices
    connections = connect_to_hosts(username=username, password=password, host_ips=host_ips)
    if not connections:
        print("No devices connected for interface configuration.")
        return

    # Create a lookup dictionary for host data by IP
    host_lookup = {h['ip_address']: h for h in hosts}
    for dev in connections:
        # Get config data for this device
        host_data = host_lookup.get(dev.hostname)
        if not host_data or 'interfaces' not in host_data:
            print(f"No interface config data for {dev.hostname}. Skipping.")
            continue
        try:
            # Render the configuration template
            config = render_template(host_data, template_name)
            if not config:
                print(f"Failed to render template for {dev.hostname}. Skipping.")
                continue
            # Show the config to be applied
            print(f"\nConfiguration to be applied to {dev.hostname} ({dev.hostname}):\n{config}")
            # Validate the config
            check_passed, check_message = check_config(dev, config)
            print(check_message)
            if not check_passed:
                print(f"Skipping commit on {dev.hostname} due to configuration errors.")
                continue
            # Apply and commit the config
            configuration = Config(dev)
            configuration.load(config, format='set', merge=False)
            configuration.commit(comment="Change CHG0123456 - interfaces", timeout=120)  # 120s timeout
            print(f"Interfaces configured on {dev.hostname}")
        except RpcTimeoutError as error:
            # Handle timeout during commit
            print(f"Timeout during commit to {dev.hostname}: {error}")
            print("Config may have applied; verify on device.")
        except Exception as error:
            # Handle other errors
            print(f"Failed to configure interfaces on {dev.hostname}: {error}")

    # Disconnect from all devices
    disconnect_from_hosts(connections)
