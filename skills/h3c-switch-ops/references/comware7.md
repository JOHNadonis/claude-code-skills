# Comware 7 Quick Reference

Use this reference when the target is an H3C switch running `Comware 7`.

## Core Session Commands

- Disable paging: `screen-length disable`
- Enter config mode: `system-view`
- Show version: `display version`
- Show running config: `display current-configuration`
- Show VLANs: `display vlan` or `display vlan brief`
- Show interfaces: `display interface brief`
- Show aggregation: `display link-aggregation summary`

## Common Layer 2 Patterns

```text
system-view
sysname ACCESS-SW02
vlan 20
 name VOICE
 quit
interface GigabitEthernet1/0/2
 description PHONE-01
 port link-type access
 port access vlan 20
 undo shutdown
 quit
interface Bridge-Aggregation1
 description UPLINK-LACP
 link-aggregation mode dynamic
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
 undo shutdown
 quit
ip route-static 0.0.0.0 0.0.0.0 192.168.99.1
```

## Operational Notes

- `display link-aggregation summary` is a reliable baseline verification command.
- The `port link-aggregation group` command assigns member links into the aggregate interface number.
- For strict trunk pruning, inspect current permitted VLANs first; do not guess what can be removed.
- If the user asks for `ACL/QoS/IRF/OSPF/BGP`, verify against the target release before generating commands.

## Official H3C References Used

- CLI basics and `screen-length disable`: https://www.h3c.com/en/d_201906/1191102_294551_0.htm
- VLAN `port link-type` and interface behavior: https://www.h3c.com/en/d_201906/1198227_294551_0.htm
- VLAN `interface vlan-interface`: https://www.h3c.com/en/d_201910/1234781_294551_0.htm
- Aggregation summary and behavior: https://www.h3c.com/en/d_201906/1198224_294551_0.htm
- `port link-aggregation group`: https://www.h3c.com/en/d_202001/1262039_294551_0.htm
- Static route syntax: https://www.h3c.com/en/d_201905/1177695_294551_0.htm
