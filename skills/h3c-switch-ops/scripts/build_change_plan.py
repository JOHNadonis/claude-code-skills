#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from common import collapse_vlan_list, dump_json, expand_vlan_expression, load_json, utc_now, write_text


SAFE_VERIFICATION_COMMANDS = [
    "display version",
    "display current-configuration",
    "display vlan",
    "display interface brief",
    "display link-aggregation summary",
]


def normalize_vlans(vlans: Any) -> list[dict]:
    result: list[dict] = []
    for vlan in vlans or []:
        if isinstance(vlan, int):
            result.append({"id": vlan, "name": None})
        elif isinstance(vlan, str) and vlan.isdigit():
            result.append({"id": int(vlan), "name": None})
        elif isinstance(vlan, dict) and vlan.get("id") is not None:
            result.append({"id": int(vlan["id"]), "name": vlan.get("name")})
    return sorted(result, key=lambda item: item["id"])


def normalize_interfaces(raw_interfaces: Any) -> dict[str, dict]:
    interfaces: dict[str, dict] = {}
    for item in raw_interfaces or []:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        name = item["name"].strip()
        if re.match(r"(?i)^vlan-interface", name) or re.match(r"(?i)^bridge-aggregation", name):
            continue
        interfaces[name] = {
            "name": name,
            "description": item.get("description"),
            "shutdown": item.get("shutdown"),
            "link_type": (item.get("link_type") or "").lower() or None,
            "access_vlan": item.get("access_vlan"),
            "trunk_pvid": item.get("trunk_pvid"),
            "trunk_vlans": expand_vlan_expression(item.get("trunk_vlans")),
            "aggregation_group": item.get("aggregation_group"),
            "ip_address": item.get("ip_address"),
            "mask": item.get("mask"),
        }
    return interfaces


def normalize_aggregations(raw_aggs: Any) -> dict[int, dict]:
    aggregations: dict[int, dict] = {}
    for item in raw_aggs or []:
        if not isinstance(item, dict) or item.get("id") is None:
            continue
        agg_id = int(item["id"])
        aggregations[agg_id] = {
            "id": agg_id,
            "description": item.get("description"),
            "mode": item.get("mode"),
            "link_type": (item.get("link_type") or "").lower() or None,
            "access_vlan": item.get("access_vlan"),
            "trunk_pvid": item.get("trunk_pvid"),
            "trunk_vlans": expand_vlan_expression(item.get("trunk_vlans")),
            "members": sorted(item.get("members") or []),
            "shutdown": item.get("shutdown"),
        }
    return aggregations


def normalize_svis(raw_svis: Any) -> dict[int, dict]:
    svis: dict[int, dict] = {}
    for item in raw_svis or []:
        if not isinstance(item, dict):
            continue
        vlan = item.get("vlan")
        if vlan is None:
            continue
        vlan_id = int(vlan)
        svis[vlan_id] = {
            "vlan": vlan_id,
            "description": item.get("description"),
            "ip_address": item.get("ip_address") or item.get("ip"),
            "mask": item.get("mask"),
            "shutdown": item.get("shutdown"),
        }
    return svis


def normalize_routes(raw_routes: Any) -> dict[tuple[str, str], dict]:
    routes: dict[tuple[str, str], dict] = {}
    for item in raw_routes or []:
        if not isinstance(item, dict):
            continue
        destination = item.get("destination")
        mask = item.get("mask")
        next_hop = item.get("next_hop")
        if not destination or not mask or not next_hop:
            continue
        routes[(destination, mask)] = {
            "destination": destination,
            "mask": mask,
            "next_hop": next_hop,
        }
    return routes


def normalize_state(raw_state: dict | None) -> dict:
    raw_state = raw_state or {}
    return {
        "hostname": raw_state.get("hostname"),
        "version_family": raw_state.get("version_family") or raw_state.get("metadata", {}).get("detected_version_family"),
        "vlans": normalize_vlans(raw_state.get("vlans")),
        "interfaces": normalize_interfaces(raw_state.get("interfaces")),
        "aggregations": normalize_aggregations(raw_state.get("aggregations")),
        "svis": normalize_svis(raw_state.get("svis")),
        "static_routes": normalize_routes(raw_state.get("static_routes")),
    }


def interface_header(name: str) -> list[str]:
    return [f"interface {name}"]


def aggregation_name(agg_id: int) -> str:
    return f"Bridge-Aggregation{agg_id}"


def build_link_type_change(current_type: str | None, target_type: str | None) -> list[str]:
    if not target_type or current_type == target_type:
        return []
    lines: list[str] = []
    if current_type in {"trunk", "hybrid"} and target_type in {"trunk", "hybrid"} and current_type != target_type:
        lines.append("port link-type access")
    lines.append(f"port link-type {target_type}")
    return lines


def render_interface_delta(current: dict | None, target: dict, risks: list[str]) -> tuple[list[str], list[str]]:
    current = current or {}
    lines: list[str] = []
    rollback: list[str] = []

    if target.get("description") != current.get("description"):
        if target.get("description"):
            lines.append(f"description {target['description']}")
        else:
            lines.append("undo description")
        if current.get("description"):
            rollback.append(f"description {current['description']}")
        else:
            rollback.append("undo description")

    if target.get("aggregation_group") != current.get("aggregation_group"):
        if target.get("aggregation_group"):
            lines.append(f"port link-aggregation group {target['aggregation_group']}")
        else:
            lines.append("undo port link-aggregation group")
        if current.get("aggregation_group"):
            rollback.append(f"port link-aggregation group {current['aggregation_group']}")
        else:
            rollback.append("undo port link-aggregation group")

    lines.extend(build_link_type_change(current.get("link_type"), target.get("link_type")))
    rollback = build_link_type_change(target.get("link_type"), current.get("link_type")) + rollback

    if target.get("link_type") == "access" and target.get("access_vlan") != current.get("access_vlan"):
        if target.get("access_vlan"):
            lines.append(f"port access vlan {target['access_vlan']}")
        if current.get("access_vlan"):
            rollback.append(f"port access vlan {current['access_vlan']}")
        else:
            rollback.append("undo port access vlan")

    current_trunk = set(current.get("trunk_vlans") or [])
    target_trunk = set(target.get("trunk_vlans") or [])
    to_add = sorted(target_trunk - current_trunk)
    to_remove = sorted(current_trunk - target_trunk)
    if to_add:
        expression = collapse_vlan_list(to_add)
        lines.append(f"port trunk permit vlan {expression}")
        rollback.append(f"undo port trunk permit vlan {expression}")
    if to_remove:
        expression = collapse_vlan_list(to_remove)
        lines.append(f"undo port trunk permit vlan {expression}")
        rollback.append(f"port trunk permit vlan {expression}")
        risks.append(f"Interface {target['name']} removes trunk VLANs: {expression}")

    if target.get("trunk_pvid") != current.get("trunk_pvid"):
        if target.get("trunk_pvid"):
            lines.append(f"port trunk pvid vlan {target['trunk_pvid']}")
        if current.get("trunk_pvid"):
            rollback.append(f"port trunk pvid vlan {current['trunk_pvid']}")
        elif target.get("trunk_pvid"):
            rollback.append("undo port trunk pvid vlan")

    target_ip = (target.get("ip_address"), target.get("mask"))
    current_ip = (current.get("ip_address"), current.get("mask"))
    if target_ip != current_ip and target.get("ip_address") and target.get("mask"):
        lines.append(f"ip address {target['ip_address']} {target['mask']}")
        if current.get("ip_address") and current.get("mask"):
            rollback.append(f"ip address {current['ip_address']} {current['mask']}")
        else:
            rollback.append("undo ip address")

    if target.get("shutdown") != current.get("shutdown") and target.get("shutdown") is not None:
        lines.append("shutdown" if target["shutdown"] else "undo shutdown")
        if current.get("shutdown") is not None:
            rollback.append("shutdown" if current["shutdown"] else "undo shutdown")

    if not lines:
        return [], []

    return interface_header(target["name"]) + lines + ["quit"], interface_header(target["name"]) + rollback + ["quit"]


def render_aggregation_delta(current: dict | None, target: dict, risks: list[str]) -> tuple[list[str], list[str]]:
    current = current or {}
    lines: list[str] = []
    rollback: list[str] = []

    if target.get("description") != current.get("description"):
        if target.get("description"):
            lines.append(f"description {target['description']}")
        else:
            lines.append("undo description")
        if current.get("description"):
            rollback.append(f"description {current['description']}")
        else:
            rollback.append("undo description")

    if target.get("mode") != current.get("mode") and target.get("mode"):
        lines.append(f"link-aggregation mode {target['mode']}")
        if current.get("mode"):
            rollback.append(f"link-aggregation mode {current['mode']}")

    lines.extend(build_link_type_change(current.get("link_type"), target.get("link_type")))
    rollback = build_link_type_change(target.get("link_type"), current.get("link_type")) + rollback

    if target.get("link_type") == "access" and target.get("access_vlan") != current.get("access_vlan"):
        lines.append(f"port access vlan {target['access_vlan']}")
        if current.get("access_vlan"):
            rollback.append(f"port access vlan {current['access_vlan']}")

    current_trunk = set(current.get("trunk_vlans") or [])
    target_trunk = set(target.get("trunk_vlans") or [])
    to_add = sorted(target_trunk - current_trunk)
    to_remove = sorted(current_trunk - target_trunk)
    if to_add:
        expression = collapse_vlan_list(to_add)
        lines.append(f"port trunk permit vlan {expression}")
        rollback.append(f"undo port trunk permit vlan {expression}")
    if to_remove:
        expression = collapse_vlan_list(to_remove)
        lines.append(f"undo port trunk permit vlan {expression}")
        rollback.append(f"port trunk permit vlan {expression}")
        risks.append(f"Aggregation {target['id']} removes trunk VLANs: {expression}")

    if target.get("trunk_pvid") != current.get("trunk_pvid"):
        if target.get("trunk_pvid"):
            lines.append(f"port trunk pvid vlan {target['trunk_pvid']}")
        if current.get("trunk_pvid"):
            rollback.append(f"port trunk pvid vlan {current['trunk_pvid']}")

    if target.get("shutdown") != current.get("shutdown") and target.get("shutdown") is not None:
        lines.append("shutdown" if target["shutdown"] else "undo shutdown")
        if current.get("shutdown") is not None:
            rollback.append("shutdown" if current["shutdown"] else "undo shutdown")

    if target.get("members") != current.get("members"):
        risks.append(f"Aggregation {target['id']} member set changes from {current.get('members') or []} to {target.get('members') or []}")

    if not lines:
        return [], []

    header = interface_header(aggregation_name(target["id"]))
    return header + lines + ["quit"], header + rollback + ["quit"]


def render_svi_delta(current: dict | None, target: dict) -> tuple[list[str], list[str]]:
    current = current or {}
    lines: list[str] = []
    rollback: list[str] = []

    if target.get("description") != current.get("description"):
        if target.get("description"):
            lines.append(f"description {target['description']}")
        else:
            lines.append("undo description")
        if current.get("description"):
            rollback.append(f"description {current['description']}")
        else:
            rollback.append("undo description")

    target_ip = (target.get("ip_address"), target.get("mask"))
    current_ip = (current.get("ip_address"), current.get("mask"))
    if target_ip != current_ip and target.get("ip_address") and target.get("mask"):
        lines.append(f"ip address {target['ip_address']} {target['mask']}")
        if current.get("ip_address") and current.get("mask"):
            rollback.append(f"ip address {current['ip_address']} {current['mask']}")
        else:
            rollback.append("undo ip address")

    if target.get("shutdown") != current.get("shutdown") and target.get("shutdown") is not None:
        lines.append("shutdown" if target["shutdown"] else "undo shutdown")
        if current.get("shutdown") is not None:
            rollback.append("shutdown" if current["shutdown"] else "undo shutdown")

    if not lines:
        return [], []

    name = f"Vlan-interface{target['vlan']}"
    header = interface_header(name)
    return header + lines + ["quit"], header + rollback + ["quit"]


def render_route(route: dict) -> str:
    return f"ip route-static {route['destination']} {route['mask']} {route['next_hop']}"


def render_full_target_config(target: dict) -> list[str]:
    lines = ["system-view"]
    if target.get("hostname"):
        lines.append(f"sysname {target['hostname']}")

    for vlan in target["vlans"]:
        lines.append(f"vlan {vlan['id']}")
        if vlan.get("name"):
            lines.append(f"name {vlan['name']}")
        lines.append("quit")

    for agg_id in sorted(target["aggregations"]):
        agg = target["aggregations"][agg_id]
        lines.append(f"interface {aggregation_name(agg_id)}")
        if agg.get("description"):
            lines.append(f"description {agg['description']}")
        if agg.get("mode"):
            lines.append(f"link-aggregation mode {agg['mode']}")
        if agg.get("link_type"):
            lines.append(f"port link-type {agg['link_type']}")
        if agg.get("link_type") == "access" and agg.get("access_vlan"):
            lines.append(f"port access vlan {agg['access_vlan']}")
        if agg.get("link_type") == "trunk" and agg.get("trunk_vlans"):
            lines.append(f"port trunk permit vlan {collapse_vlan_list(agg['trunk_vlans'])}")
        if agg.get("link_type") == "trunk" and agg.get("trunk_pvid"):
            lines.append(f"port trunk pvid vlan {agg['trunk_pvid']}")
        if agg.get("shutdown") is not None:
            lines.append("shutdown" if agg["shutdown"] else "undo shutdown")
        lines.append("quit")

    for name in sorted(target["interfaces"]):
        interface = target["interfaces"][name]
        lines.append(f"interface {name}")
        if interface.get("description"):
            lines.append(f"description {interface['description']}")
        if interface.get("aggregation_group"):
            lines.append(f"port link-aggregation group {interface['aggregation_group']}")
        if interface.get("link_type"):
            lines.append(f"port link-type {interface['link_type']}")
        if interface.get("link_type") == "access" and interface.get("access_vlan"):
            lines.append(f"port access vlan {interface['access_vlan']}")
        if interface.get("link_type") == "trunk" and interface.get("trunk_vlans"):
            lines.append(f"port trunk permit vlan {collapse_vlan_list(interface['trunk_vlans'])}")
        if interface.get("link_type") == "trunk" and interface.get("trunk_pvid"):
            lines.append(f"port trunk pvid vlan {interface['trunk_pvid']}")
        if interface.get("ip_address") and interface.get("mask"):
            lines.append(f"ip address {interface['ip_address']} {interface['mask']}")
        if interface.get("shutdown") is not None:
            lines.append("shutdown" if interface["shutdown"] else "undo shutdown")
        lines.append("quit")

    for vlan in sorted(target["svis"]):
        svi = target["svis"][vlan]
        lines.append(f"interface Vlan-interface{vlan}")
        if svi.get("description"):
            lines.append(f"description {svi['description']}")
        if svi.get("ip_address") and svi.get("mask"):
            lines.append(f"ip address {svi['ip_address']} {svi['mask']}")
        if svi.get("shutdown") is not None:
            lines.append("shutdown" if svi["shutdown"] else "undo shutdown")
        lines.append("quit")

    for key in sorted(target["static_routes"]):
        lines.append(render_route(target["static_routes"][key]))

    lines.append("return")
    return lines


def build_plan(current: dict, target: dict) -> dict:
    risks: list[str] = []
    change_commands: list[str] = ["system-view"]
    rollback_commands: list[str] = ["system-view"]

    if target.get("hostname") and target.get("hostname") != current.get("hostname"):
        change_commands.append(f"sysname {target['hostname']}")
        if current.get("hostname"):
            rollback_commands.append(f"sysname {current['hostname']}")

    current_vlans = {item["id"]: item for item in current["vlans"]}
    target_vlans = {item["id"]: item for item in target["vlans"]}
    for vlan_id in sorted(target_vlans):
        vlan = target_vlans[vlan_id]
        if vlan_id not in current_vlans:
            change_commands.extend([f"vlan {vlan_id}"])
            if vlan.get("name"):
                change_commands.append(f"name {vlan['name']}")
            change_commands.append("quit")
            rollback_commands.append(f"undo vlan {vlan_id}")
        elif vlan.get("name") and vlan.get("name") != current_vlans[vlan_id].get("name"):
            change_commands.extend([f"vlan {vlan_id}", f"name {vlan['name']}", "quit"])
            rollback_commands.extend([f"vlan {vlan_id}"])
            if current_vlans[vlan_id].get("name"):
                rollback_commands.append(f"name {current_vlans[vlan_id]['name']}")
            else:
                rollback_commands.append("undo name")
            rollback_commands.append("quit")

    for agg_id, agg in sorted(target["aggregations"].items()):
        delta, rollback = render_aggregation_delta(current["aggregations"].get(agg_id), agg, risks)
        change_commands.extend(delta)
        rollback_commands.extend(rollback)

    for name, interface in sorted(target["interfaces"].items()):
        delta, rollback = render_interface_delta(current["interfaces"].get(name), interface, risks)
        change_commands.extend(delta)
        rollback_commands.extend(rollback)

    for vlan, svi in sorted(target["svis"].items()):
        if vlan not in target_vlans and vlan not in current_vlans:
            change_commands.extend([f"vlan {vlan}", "quit"])
            rollback_commands.append(f"undo vlan {vlan}")
        delta, rollback = render_svi_delta(current["svis"].get(vlan), svi)
        change_commands.extend(delta)
        rollback_commands.extend(rollback)

    current_routes = current["static_routes"]
    target_routes = target["static_routes"]
    for key, route in sorted(target_routes.items()):
        current_route = current_routes.get(key)
        if not current_route:
            change_commands.append(render_route(route))
            rollback_commands.append(f"undo {render_route(route)}")
        elif current_route.get("next_hop") != route.get("next_hop"):
            change_commands.append(f"undo {render_route(current_route)}")
            change_commands.append(render_route(route))
            rollback_commands.append(f"undo {render_route(route)}")
            rollback_commands.append(render_route(current_route))

    target_config = render_full_target_config(target)

    for route in target_routes.values():
        if route["destination"] == "0.0.0.0" and route["mask"] == "0.0.0.0":
            risks.append("Default route is created or changed.")
    for name, interface in target["interfaces"].items():
        description = (interface.get("description") or "").lower()
        if "uplink" in description or name.lower().endswith("/24") or interface.get("aggregation_group"):
            risks.append(f"Interface {name} may be production-facing or uplink-sensitive.")
    for agg in target["aggregations"].values():
        if agg.get("members"):
            risks.append(f"Aggregation {agg['id']} touches member links: {', '.join(agg['members'])}")
    for svi in target["svis"].values():
        description = (svi.get("description") or "").lower()
        if "mgmt" in description or svi["vlan"] in {1, 99, 4094}:
            risks.append(f"SVI Vlan-interface{svi['vlan']} may carry management traffic.")

    verification_commands = list(SAFE_VERIFICATION_COMMANDS)
    for name in sorted(target["interfaces"]):
        verification_commands.append(f"display current-configuration interface {name}")
    for vlan in sorted(target["svis"]):
        verification_commands.append(f"display current-configuration interface Vlan-interface{vlan}")

    return {
        "metadata": {
            "generated_at": utc_now(),
            "version_family": target.get("version_family") or current.get("version_family") or "unknown",
        },
        "target_config": target_config,
        "change_commands": change_commands + ["return"],
        "rollback_commands": rollback_commands + ["return"],
        "verification_commands": verification_commands,
        "risks": sorted(set(risks)),
    }


def load_input_data(path: str | None) -> dict:
    if path:
        return load_json(path)
    if sys.stdin.isatty():
        raise SystemExit("Provide --input or pipe JSON into stdin.")
    return json.loads(sys.stdin.read())


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a cautious H3C change plan from parsed config or intent JSON.")
    parser.add_argument("--input", help="Path to input JSON. Reads stdin when omitted.")
    parser.add_argument("--output", help="Optional output file path.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    raw_data = load_input_data(args.input)
    current = normalize_state(raw_data.get("current"))
    target = normalize_state(raw_data.get("target") if raw_data.get("target") is not None else raw_data)
    if not target.get("version_family"):
        target["version_family"] = current.get("version_family") or "unknown"

    plan = build_plan(current, target)
    payload = dump_json(plan, pretty=args.pretty) + "\n"
    if args.output:
        write_text(args.output, payload)
    else:
        sys.stdout.write(payload)


if __name__ == "__main__":
    main()
