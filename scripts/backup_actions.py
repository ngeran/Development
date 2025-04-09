import os
from datetime import datetime

def backup_config(username, password, host_ips, hosts, connect_to_hosts, disconnect_from_hosts):
    """Backup device configurations to the backups folder."""
    backup_dir = os.path.join(os.path.dirname(__file__), '../backups')
    os.makedirs(backup_dir, exist_ok=True)  # Create if it doesn’t exist

    connections = connect_to_hosts(username=username, password=password, host_ips=host_ips)
    if not connections:
        print("No devices connected for backup.")
        return

    date_str = datetime.now().strftime('%Y%m%d')
    host_lookup = {h['ip_address']: h['host_name'] for h in hosts}  # Map IP to host_name
    for dev in connections:
        try:
            config = dev.rpc.get_config(options={'format': 'text'})
            config_text = config.text
            host_name = host_lookup.get(dev.hostname, dev.hostname)  # Fallback to IP if not found
            filename = f"{host_name}_{date_str}.cfg"
            filepath = os.path.join(backup_dir, filename)
            with open(filepath, 'w') as f:
                f.write(config_text)
            print(f"Configuration backed up for {host_name} to {filepath}")
        except Exception as error:
            print(f"Failed to backup {dev.hostname}: {error}")

    disconnect_from_hosts(connections)

def capture_device_baseline(username, password, host_ips, hosts, connect_to_hosts, disconnect_from_hosts):
    """Capture a device baseline similar to 'request support information'."""
    backup_dir = os.path.join(os.path.dirname(__file__), '../backups')
    os.makedirs(backup_dir, exist_ok=True)

    connections = connect_to_hosts(username=username, password=password, host_ips=host_ips)
    if not connections:
        print("No devices connected for baseline capture.")
        return

    date_str = datetime.now().strftime('%Y%m%d')
    host_lookup = {h['ip_address']: h['host_name'] for h in hosts}  # Map IP to host_name
    for dev in connections:
        try:
            baseline = ""
            config = dev.rpc.get_config(options={'format': 'text'})
            baseline += "=== Configuration ===\n" + config.text + "\n\n"
            sys_info = dev.rpc.cli('show version', format='text')
            baseline += "=== System Version ===\n" + sys_info.text + "\n\n"
            intf_status = dev.rpc.cli('show interfaces terse', format='text')
            baseline += "=== Interface Status ===\n" + intf_status.text + "\n\n"
            route_info = dev.rpc.cli('show route summary', format='text')
            baseline += "=== Routing Summary ===\n" + route_info.text + "\n"

            host_name = host_lookup.get(dev.hostname, dev.hostname)  # Fallback to IP if not found
            filename = f"{host_name}_{date_str}_baseline.txt"
            filepath = os.path.join(backup_dir, filename)
            with open(filepath, 'w') as f:
                f.write(baseline)
            print(f"Baseline captured for {host_name} to {filepath}")
        except Exception as error:
            print(f"Failed to capture baseline for {dev.hostname}: {error}")

    disconnect_from_hosts(connections)
