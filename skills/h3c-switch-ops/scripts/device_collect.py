#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import (
    DEFAULT_PROMPT_REGEX,
    disable_paging,
    dump_json,
    get_password,
    open_session,
    run_command,
    utc_now,
    write_json,
    write_text,
)

DEFAULT_COMMANDS = [
    "display version",
    "display current-configuration",
    "display vlan",
    "display interface brief",
    "display link-aggregation summary",
]


def protocol_order(requested_protocol: str) -> list[str]:
    if requested_protocol == "auto":
        return ["ssh", "telnet"]
    return [requested_protocol]


def resolve_port(protocol: str, port: int | None, ssh_port: int | None, telnet_port: int | None) -> int:
    if port is not None:
        return port
    if protocol == "ssh":
        return ssh_port or 22
    return telnet_port or 23


def prepare_output_dir(output_dir: str | None) -> Path | None:
    if not output_dir:
        return None
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    return target


def collect_device_state(
    host: str,
    username: str,
    password: str,
    protocol: str = "ssh",
    port: int | None = None,
    ssh_port: int | None = None,
    telnet_port: int | None = None,
    timeout: int = 15,
    prompt_regex: str = DEFAULT_PROMPT_REGEX,
    commands: list[str] | None = None,
    output_dir: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    commands = commands or list(DEFAULT_COMMANDS)
    selected_output_dir = prepare_output_dir(output_dir)
    payload: dict[str, Any] = {
        "metadata": {
            "generated_at": utc_now(),
            "mode": "execute",
            "host": host,
            "requested_protocol": protocol,
            "selected_protocol": None,
            "port": None,
            "output_dir": str(selected_output_dir.resolve()) if selected_output_dir else None,
        },
        "commands": commands,
        "connection_attempts": [],
        "warnings": [],
        "results": {},
        "command_results": [],
        "files": {},
    }

    for candidate in protocol_order(protocol):
        attempt_port = resolve_port(candidate, port=port, ssh_port=ssh_port, telnet_port=telnet_port)
        attempt = {"protocol": candidate, "port": attempt_port, "status": "connecting"}
        transcript_path = None
        if selected_output_dir:
            transcript_path = selected_output_dir / f"session-{candidate}.log"

        try:
            session = open_session(
                host=host,
                username=username,
                password=password,
                protocol=candidate,
                port=attempt_port,
                timeout=timeout,
                prompt_regex=prompt_regex,
                logfile_path=str(transcript_path) if transcript_path else None,
                disable_paging_on_open=False,
            )
        except Exception as exc:
            attempt.update({"status": "failed", "error": str(exc)})
            payload["connection_attempts"].append(attempt)
            continue

        attempt["status"] = "connected"
        payload["connection_attempts"].append(attempt)
        payload["metadata"]["selected_protocol"] = candidate
        payload["metadata"]["port"] = attempt_port
        if transcript_path:
            payload["files"]["transcript"] = str(transcript_path.resolve())

        paging_result = disable_paging(session, prompt_regex=prompt_regex, timeout=timeout)
        payload["paging"] = paging_result
        if not paging_result.get("success"):
            payload["warnings"].append("分页未关闭，采集可能受到 pager 影响。")

        try:
            for command in commands:
                try:
                    output = run_command(session, command, prompt_regex=prompt_regex, timeout=timeout)
                    payload["results"][command] = output
                    payload["command_results"].append({"command": command, "status": "ok", "output": output})
                except Exception as exc:
                    payload["command_results"].append({"command": command, "status": "error", "error": str(exc)})
                    payload["warnings"].append(f"命令执行失败：{command} -> {exc}")
            if selected_output_dir and payload["results"].get("display current-configuration"):
                current_cfg_path = selected_output_dir / "current.cfg"
                write_text(current_cfg_path, payload["results"]["display current-configuration"] + "\n")
                payload["files"]["current_config"] = str(current_cfg_path.resolve())
            if selected_output_dir:
                collect_path = selected_output_dir / "collect.json"
                write_json(collect_path, payload, pretty=True)
                payload["files"]["collect"] = str(collect_path.resolve())
        finally:
            session.close(force=True)

        return True, payload

    if selected_output_dir:
        collect_path = selected_output_dir / "collect.json"
        write_json(collect_path, payload, pretty=True)
        payload["files"]["collect"] = str(collect_path.resolve())
    return False, payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect non-destructive H3C switch state over SSH or Telnet.")
    parser.add_argument("--host", required=True, help="Device hostname or IP.")
    parser.add_argument("--username", required=True, help="Login username.")
    parser.add_argument("--password", help="Login password. Defaults to env H3C_PASSWORD or interactive prompt.")
    parser.add_argument("--password-env", default="H3C_PASSWORD", help="Environment variable used for password fallback.")
    parser.add_argument("--protocol", choices=["ssh", "telnet", "auto"], default="ssh", help="Connection protocol.")
    parser.add_argument("--port", type=int, help="Override destination port for single-protocol runs.")
    parser.add_argument("--ssh-port", type=int, help="Override SSH port when using protocol auto.")
    parser.add_argument("--telnet-port", type=int, help="Override Telnet port when using protocol auto.")
    parser.add_argument("--timeout", type=int, default=15, help="Per-command timeout in seconds.")
    parser.add_argument("--prompt-regex", default=DEFAULT_PROMPT_REGEX, help="Prompt detection regex.")
    parser.add_argument("--command", action="append", dest="commands", help="Extra command to collect. Can repeat.")
    parser.add_argument("--execute", action="store_true", help="Actually connect and collect. Without this flag the script prints a dry-run plan.")
    parser.add_argument("--output", help="Optional output JSON path.")
    parser.add_argument("--output-dir", help="Optional directory for collect.json, current.cfg, and session logs.")
    args = parser.parse_args()

    commands = DEFAULT_COMMANDS + (args.commands or [])
    payload = {
        "metadata": {
            "generated_at": utc_now(),
            "mode": "execute" if args.execute else "dry-run",
            "host": args.host,
            "requested_protocol": args.protocol,
            "selected_protocol": None,
            "port": args.port or (22 if args.protocol == "ssh" else 23 if args.protocol == "telnet" else None),
            "output_dir": args.output_dir,
        },
        "commands": commands,
    }

    if not args.execute:
        text = dump_json(payload, pretty=True) + "\n"
        if args.output:
            write_text(args.output, text)
        else:
            sys.stdout.write(text)
        return

    password = get_password(args.password, password_env=args.password_env)
    success, payload = collect_device_state(
        host=args.host,
        username=args.username,
        password=password,
        protocol=args.protocol,
        port=args.port,
        ssh_port=args.ssh_port,
        telnet_port=args.telnet_port,
        timeout=args.timeout,
        prompt_regex=args.prompt_regex,
        commands=commands,
        output_dir=args.output_dir,
    )

    text = dump_json(payload, pretty=True) + "\n"
    if args.output:
        write_text(args.output, text)
    else:
        sys.stdout.write(text)

    if not success:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
