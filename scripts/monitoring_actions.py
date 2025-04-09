import subprocess


def ping_host(ip_address, timeout=2, count=4):
    try:
        # Linux/macOS ping syntax; adjust for Windows with '-n', '-w' if needed
        result = subprocess.run(
            ['ping', '-c', str(count), '-W', str(timeout), ip_address],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0
    except Exception as error:
        print(f"Error pinging {ip_address}: {error}")
        return False

def verify_bgp(device, host_name):
    """Verify BGP state on the device."""
    try:
        # Run 'show bgp summary' and parse output
        bgp_output = device.rpc.cli('show bgp summary', format='text')
        bgp_text = bgp_output.text
        if "Establ" in bgp_text:
            return f"{host_name} ({device.hostname}): BGP is Established"
        else:
            return f"{host_name} ({device.hostname}): BGP is NOT Established"
    except Exception as error:
        return f"{host_name} ({device.hostname}): BGP verification failed - {error}"

def verify_ospf(device, host_name):
    """Verify OSPF state on the device."""
    try:
        # Run 'show ospf neighbor' and parse output
        ospf_output = device.rpc.cli('show ospf neighbor', format='text')
        ospf_text = ospf_output.text
        if "Full" in ospf_text:
            return f"{host_name} ({device.hostname}): OSPF is Full"
        else:
            return f"{host_name} ({device.hostname}): OSPF is NOT Full"
    except Exception as error:
        return f"{host_name} ({device.hostname}): OSPF verification failed - {error}"

def monitor_actions(username, password, host_ips, hosts, connect_to_hosts, disconnect_from_hosts, actions):
    """Execute specified monitoring actions."""
    # Ping action (no SSH needed)
    if 'ping' in actions:
        reachable = []
        unreachable = []
        for host in hosts:
            ip = host['ip_address']
            host_name = host['host_name']
            if ping_host(ip):
                reachable.append(f"{host_name} ({ip})")
            else:
                unreachable.append(f"{host_name} ({ip})")
        print("\nPing Results:")
        print("Reachable Devices:")
        for device in reachable:
            print(f"  - {device}")
        print("Unreachable Devices:")
        for device in unreachable:
            print(f"  - {device}")

    # SSH-based actions (BGP, OSPF)
    if 'bgp_verification' in actions or 'ospf_verification' in actions:
        connections = connect_to_hosts(username=username, password=password, host_ips=host_ips)
        if not connections:
            print("No devices connected for protocol verification.")
            return

        host_lookup = {h['ip_address']: h['host_name'] for h in hosts}
        results = []

        for dev in connections:
            host_name = host_lookup.get(dev.hostname, dev.hostname)
            if 'bgp_verification' in actions:
                results.append(verify_bgp(dev, host_name))
            if 'ospf_verification' in actions:
                results.append(verify_ospf(dev, host_name))

        # Print verification results
        print("\nProtocol Verification Results:")
        for result in results:
            print(f"  - {result}")

        disconnect_from_hosts(connections)
