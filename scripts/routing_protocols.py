from jnpr.junos.utils.config import Config
from jnpr.junos.exception import RpcTimeoutError
from utils import render_template, check_config

def configure_routing(username, password, host_ips, hosts, connect_to_hosts, disconnect_from_hosts, protocols):
    """Apply routing protocol configurations to specified devices."""
    # Map protocol names to their template files
    protocol_templates = {
        'bgp': 'bgp_template.j2',
        'ospf': 'ospf_template.j2',
        'ldp': 'ldp_template.j2',
        'rsvp': 'rsvp_template.j2',
        'mpls': 'mpls_template.j2'
    }

    # Connect to all specified devices
    connections = connect_to_hosts(username=username, password=password, host_ips=host_ips)
    if not connections:
        print("No devices connected for routing configuration.")
        return

    # Create a lookup dictionary for host data by IP
    host_lookup = {h['ip_address']: h for h in hosts}
    for dev in connections:
        host_data = host_lookup.get(dev.hostname)
        if not host_data:
            print(f"No routing config data for {dev.hostname}. Skipping.")
            continue

        # Filter protocols to configure based on user input and host data
        protocols_to_config = [p for p in protocols if p in host_data and p in protocol_templates]
        if not protocols_to_config:
            print(f"No specified routing protocols to configure for {dev.hostname}. Skipping.")
            continue

        # Build combined config for selected protocols
        combined_config = ""
        for protocol in protocols_to_config:
            config = render_template(host_data, protocol_templates[protocol])
            if not config:
                print(f"Failed to render {protocol} template for {dev.hostname}. Skipping protocol.")
                continue
            combined_config += config + "\n"

        if not combined_config.strip():
            print(f"No valid configuration generated for {dev.hostname}. Skipping.")
            continue

        try:
            print(f"\nConfiguration to be applied to {dev.hostname} ({dev.hostname}):\n{combined_config.strip()}")
            # Validate the combined config
            check_passed, check_message = check_config(dev, combined_config)
            print(check_message)
            if not check_passed:
                print(f"Skipping commit on {dev.hostname} due to configuration errors.")
                continue
            # Apply and commit the config
            configuration = Config(dev)
            configuration.load(combined_config, format='set', merge=False)
            configuration.commit(comment="Change CHG0123456 - routing protocols", timeout=120)
            print(f"Routing protocols configured on {dev.hostname}")
        except RpcTimeoutError as error:
            print(f"Timeout during commit to {dev.hostname}: {error}")
            print(f"Config may have applied; verify on device.")
        except Exception as error:
            print(f"Failed to configure routing protocols on {dev.hostname}: {error}")

    # Disconnect from all devices
    disconnect_from_hosts(connections)
