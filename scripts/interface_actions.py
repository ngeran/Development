# scripts/interface_actions.py
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import RpcTimeoutError
from utils import render_template, check_config

def configure_interfaces(username, password, host_ips, hosts, template_name, connect_to_hosts, disconnect_from_hosts):
    connections = connect_to_hosts(username=username, password=password, host_ips=host_ips)
    if not connections:
        print("No devices connected for interface configuration.")
        return
    print(f"Debug: Connected to {[dev.hostname for dev in connections]}")
    host_lookup = {h['ip_address']: h for h in hosts}
    for dev in connections:
        host_data = host_lookup.get(dev.hostname)
        if not host_data or 'interfaces' not in host_data:
            print(f"No interface config data for {dev.hostname}. Skipping.")
            continue
        try:
            config = render_template(host_data, template_name)
            if not config:
                print(f"Failed to render template for {dev.hostname}. Skipping.")
                continue
            print(f"\nConfiguration to be applied to {dev.hostname} ({dev.hostname}):\n{config}")
            check_passed, check_message = check_config(dev, config)
            print(check_message)  # Diff from check_config
            if not check_passed:
                print(f"Skipping commit on {dev.hostname} due to configuration errors.")
                continue
            configuration = Config(dev)
            configuration.load(config, format='set', merge=False)
            # Remove pdiff() to avoid double print
            configuration.commit(comment="Change CHG0123456 - interfaces", timeout=120)
            print(f"Interfaces configured on {dev.hostname}")
        except RpcTimeoutError as error:
            print(f"Timeout during commit to {dev.hostname}: {error}")
        except Exception as error:
            print(f"Failed to configure interfaces on {dev.hostname}: {error}")
    disconnect_from_hosts(connections)
