# Comware 5 Quick Reference

Use this reference when the target is an older H3C switch running `Comware 5`.

## Core Session Commands

- Disable paging: `screen-length disable`
- Enter config mode: `system-view`
- Show version: `display version`
- Show running config: `display current-configuration`
- Show VLANs: `display vlan`
- Show interfaces: `display interface brief`
- Show link aggregation: `display link-aggregation summary`

## Common Layer 2 Patterns

```text
system-view
sysname ACCESS-SW01
vlan 10
 name OFFICE
 quit
interface GigabitEthernet1/0/1
 description USER-01
 port link-type access
 port access vlan 10
 quit
interface GigabitEthernet1/0/24
 description UPLINK-CORE
 port link-type trunk
 port trunk permit vlan 10 20 99
 quit
```

## Common Layer 3 Patterns

```text
vlan 99
 name MGMT
 quit
interface Vlan-interface99
 ip address 192.168.99.2 255.255.255.0
 quit
ip route-static 0.0.0.0 0.0.0.0 192.168.99.1
```

## Aggregation Pattern

```text
interface Bridge-Aggregation1
 description CORE-LACP
 link-aggregation mode dynamic
 port link-type trunk
 port trunk permit vlan 10 20 99
 quit
interface GigabitEthernet1/0/23
 port link-aggregation group 1
 quit
interface GigabitEthernet1/0/24
 port link-aggregation group 1
 quit
```

## Operational Notes

- `Trunk` and `Hybrid` should not be converted directly. Move through `access` first when changing types.
- Create the VLAN before creating `Vlan-interface`.
- When replacing old switches, parse the old config first and migrate by intent, not by blind copy.

## Official H3C References Used

- CLI basics and `screen-length disable`: https://www.h3c.com/en/d_201408/839360_294551_0.htm
- VLAN and `port access vlan`: https://www.h3c.com/en/d_201408/838810_294551_0.htm
- Legacy VLAN/interface reference: https://www.h3c.com/en/d_200712/211821_294551_0.htm
- Legacy aggregation summary: https://www.h3c.com/en/d_200901/624780_294551_0.htm
