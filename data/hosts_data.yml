username: 'admin'
password: 'manolis1'
interval: 300
tables:
  - inet.0
  - inet.3
  - mpls.0
hosts:
  - host_name: "DC1MX480PE-1"
    ip_address: "172.27.200.200"
    interfaces:
      - name: "ge-0/0/3"
        description: "ETH|DC1MX480PE-2|GE-0/0/4|1G|1G|_|WAN"
        unit: 0
        ip_address: "172.27.201.1/24"
      - name: "ge-0/0/4"
        description: "ETH|DC1MX480PE-3|GE-0/0/4|1G|1G|_|WAN"
        unit: 0
        ip_address: "172.27.202.1/24"
    bgp:
      local_as: 65001
      peers:
        - peer_ip: "172.27.202.2"
          peer_as: 65002
          interface: "ge-0/0/4"
    ospf:
      area: "0.0.0.0"
      interfaces:
        - name: "ge-0/0/3"
          metric: 10
        - name: "ge-0/0/4"
          metric: 20
    ldp:
      interfaces:
        - name: "ge-0/0/4"
    rsvp:
      interfaces:
        - name: "ge-0/0/4"
    mpls:
      interfaces:
        - name: "ge-0/0/4"
  - host_name: "SP1DCI106BJEX01"
    ip_address: "172.27.200.201"
    interfaces:
      - name: "ge-0/0/3"
        description: "ETH|SP1DCI106BJEX02|GE-0/0/4|1G|1G|_|WAN"
        unit: 0
        ip_address: "172.27.203.1/24"
      - name: "ge-0/0/4"
        description: "ETH|SP1DCI106BJEX03|GE-0/0/4|1G|1G|_|WAN"
        unit: 0
        ip_address: "172.27.204.1/24"
    bgp:
      local_as: 65003
      peers:
        - peer_ip: "172.27.204.2"
          peer_as: 65004
          interface: "ge-0/0/4"
    ospf:
      area: "0.0.0.1"
      interfaces:
        - name: "ge-0/0/4"
          metric: 15
