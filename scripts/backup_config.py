# scripts/backup_config.py
import os
import sys
from datetime import datetime
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import LockError, UnlockError

try:
    from connect_to_hosts import connect_to_hosts, disconnect_from_hosts
except ModuleNotFoundError as e:
    print(f"Error: Could not import connect_to_hosts: {e}")
    sys.exit(1)

from utils import load_yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

def backup_device_config(dev, backup_dir, timestamp):
    try:
        hostname = dev.facts.get('hostname', dev._hostname if dev._hostname else 'unknown_host')
        print(f"Backing up configuration for {hostname} ({dev._hostname})")
        config = Config(dev)
        config.lock()
        json_config = config.rpc.get_config(options={'format': 'json'})
        json_filename = os.path.join(backup_dir, f"{hostname}_{timestamp}.json")
        with open(json_filename, 'w') as json_file:
            import json
            json.dump(json_config, json_file, indent=4)
        print(f"Saved JSON backup: {json_filename}")
        set_config = config.rpc.get_config(options={'format': 'set'})
        set_filename = os.path.join(backup_dir, f"{hostname}_{timestamp}.set")
        with open(set_filename, 'w') as set_file:
            set_file.write(set_config.text)
        print(f"Saved set backup: {set_filename}")
        config.unlock()
    except LockError as e:
        print(f"Failed to lock config for {dev._hostname}: {e}")
    except UnlockError as e:
        print(f"Failed to unlock config for {dev._hostname}: {e}")
    except Exception as e:
        print(f"Failed to backup {dev._hostname}: {e}")
        try:
            if 'config' in locals() and config.is_locked():
                config.unlock()
        except Exception as unlock_error:
            print(f"Error unlocking config for {dev._hostname}: {unlock_error}")

def main():
    yaml_file = os.path.join(SCRIPT_DIR, "../data/hosts_data.yml")
    data = load_yaml(yaml_file)
    if not data:
        sys.exit(1)

    username = data.get('username', 'N/A')
    password = data.get('password', 'N/A')
    hosts = data.get('hosts', [])
    if not hosts:
        print("No hosts found in YAML. Exiting.")
        sys.exit(0)

    host_ips = [host['host_ip'] for host in hosts]
    print(f"Connecting to {len(host_ips)} devices: {host_ips}")
    connections = connect_to_hosts(username=username, password=password, host_ips=host_ips)
    if not connections:
        print("No devices connected. Exiting.")
        sys.exit(0)

    backup_dir = os.path.join(os.path.dirname(SCRIPT_DIR), "backups")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"Created backup directory: {backup_dir}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for dev in connections:
        backup_device_config(dev, backup_dir, timestamp)

    disconnect_from_hosts(connections)
    print("\nAll connections closed.")

if __name__ == "__main__":
    main()
