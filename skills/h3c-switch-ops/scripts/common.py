#!/usr/bin/env python3
from __future__ import annotations

import getpass
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import pexpect
except Exception:
    pexpect = None

DEFAULT_PROMPT_REGEX = r"(?m)(?:<[^<>\r\n]+>|\[[^\[\]\r\n]+\])\s*$"
PAGER_PATTERNS = [
    r"--\s*More\s*--",
    r"----\s*More\s*----",
    r"\bMore:\s*<",
    r"(?i)press\s+any\s+key\s+to\s+continue",
]
CONFIRM_PATTERNS = [
    r"(?i)continue\?\s*\[Y/N\]",
    r"(?i)\[Y/N\]",
    r"(?i)\(y/n\)",
]
ANSI_ESCAPE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
SAFE_PATH_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def load_json(path: str | Path) -> Any:
    return json.loads(read_text(path))


def dump_json(data: Any, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
    return json.dumps(data, ensure_ascii=False)


def write_json(path: str | Path, data: Any, pretty: bool = True) -> None:
    write_text(path, dump_json(data, pretty=pretty) + "\n")


def safe_path_component(value: str) -> str:
    cleaned = SAFE_PATH_CHARS.sub("-", value.strip())
    cleaned = cleaned.strip("-._")
    return cleaned or "device"


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def dedupe_ints(values: Iterable[int]) -> list[int]:
    return sorted({int(value) for value in values})


def expand_vlan_expression(expression: str | list[int] | None) -> list[int]:
    if expression is None:
        return []
    if isinstance(expression, list):
        return dedupe_ints(expression)

    tokens = re.split(r"[\s,]+", expression.strip())
    tokens = [token for token in tokens if token]
    result: list[int] = []
    index = 0

    while index < len(tokens):
        token = tokens[index].lower()
        if token == "to":
            index += 1
            continue

        current = parse_int(tokens[index])
        if current is None:
            index += 1
            continue

        if index + 2 < len(tokens) and tokens[index + 1].lower() == "to":
            end = parse_int(tokens[index + 2])
            if end is not None:
                start, stop = sorted((current, end))
                result.extend(range(start, stop + 1))
                index += 3
                continue

        result.append(current)
        index += 1

    return dedupe_ints(result)


def collapse_vlan_list(values: Iterable[int] | None) -> str:
    numbers = dedupe_ints(values or [])
    if not numbers:
        return ""

    ranges: list[str] = []
    start = end = numbers[0]
    for number in numbers[1:]:
        if number == end + 1:
            end = number
            continue
        ranges.append(f"{start} to {end}" if start != end else str(start))
        start = end = number
    ranges.append(f"{start} to {end}" if start != end else str(start))
    return " ".join(ranges)


def split_blocks(config_text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw_line in config_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()
        if not line:
            continue
        if line.strip() == "#":
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def detect_version_family(config_text: str) -> str:
    lowered = config_text.lower()
    if re.search(r"version\s+7(?:\.\d+)?", lowered):
        return "comware7"
    if re.search(r"version\s+5(?:\.\d+)?", lowered):
        return "comware5"
    return "unknown"


def clean_device_output(text: str, command: str | None = None) -> str:
    cleaned = ANSI_ESCAPE.sub("", text.replace("\r", ""))
    cleaned = cleaned.replace("\x08", "")
    lines = cleaned.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if command and lines and lines[0].strip() == command.strip():
        lines.pop(0)
    return "\n".join(line.rstrip() for line in lines).strip()


def get_password(explicit_password: str | None = None, password_env: str = "H3C_PASSWORD") -> str:
    if explicit_password:
        return explicit_password
    env_password = os.getenv(password_env)
    if env_password:
        return env_password
    return getpass.getpass("Device password: ")


def ensure_pexpect() -> None:
    if pexpect is None:
        raise RuntimeError("pexpect is required for device interaction scripts.")


def _build_spawn_command(protocol: str, host: str, port: int, username: str) -> tuple[str, list[str]]:
    if protocol == "ssh":
        return (
            "ssh",
            [
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "ServerAliveInterval=30",
                "-p",
                str(port),
                f"{username}@{host}",
            ],
        )
    telnet_path = shutil.which("telnet")
    if not telnet_path:
        raise RuntimeError("telnet binary not found. Install a telnet client or use SSH.")
    return telnet_path, [host, str(port)]


def open_session(
    host: str,
    username: str,
    password: str,
    protocol: str = "ssh",
    port: int | None = None,
    timeout: int = 15,
    prompt_regex: str = DEFAULT_PROMPT_REGEX,
    logfile_path: str | None = None,
    disable_paging_on_open: bool = True,
):
    ensure_pexpect()
    protocol = protocol.lower()
    port = port or (22 if protocol == "ssh" else 23)
    executable, args = _build_spawn_command(protocol, host, port, username)
    child = pexpect.spawn(executable, args, encoding="utf-8", timeout=timeout)

    if logfile_path:
        log_file = Path(logfile_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        child.logfile = log_file.open("w", encoding="utf-8")

    if protocol == "ssh":
        _login_ssh(child, password=password, prompt_regex=prompt_regex, timeout=timeout)
    else:
        _login_telnet(child, username=username, password=password, prompt_regex=prompt_regex, timeout=timeout)

    if disable_paging_on_open:
        disable_paging(child, prompt_regex=prompt_regex, timeout=timeout)

    return child


def _login_ssh(child: Any, password: str, prompt_regex: str, timeout: int) -> None:
    patterns = [
        r"(?i)are you sure you want to continue connecting",
        r"(?i)(?:password|passphrase)[:：]\s*",
        prompt_regex,
        r"(?i)permission denied",
        pexpect.TIMEOUT,
        pexpect.EOF,
    ]

    while True:
        index = child.expect(patterns, timeout=timeout)
        if index == 0:
            child.sendline("yes")
        elif index == 1:
            child.sendline(password)
        elif index == 2:
            return
        elif index == 3:
            raise RuntimeError("SSH authentication failed.")
        elif index == 4:
            raise RuntimeError("SSH login timed out.")
        raise RuntimeError("SSH login failed unexpectedly.")


def _login_telnet(child: Any, username: str, password: str, prompt_regex: str, timeout: int) -> None:
    patterns = [
        r"(?i)(?:login|username|user name)[:：]\s*",
        r"(?i)password[:：]\s*",
        prompt_regex,
        pexpect.TIMEOUT,
        pexpect.EOF,
    ]

    sent_username = False
    sent_password = False

    while True:
        index = child.expect(patterns, timeout=timeout)
        if index == 0:
            child.sendline(username)
            sent_username = True
        elif index == 1:
            child.sendline(password)
            sent_password = True
        elif index == 2:
            if sent_username and sent_password:
                return
            return
        elif index == 3:
            raise RuntimeError("Telnet login timed out.")
        else:
            raise RuntimeError("Telnet login failed unexpectedly.")


def run_command(
    child: Any,
    command: str,
    prompt_regex: str = DEFAULT_PROMPT_REGEX,
    timeout: int | None = None,
    auto_confirm: bool = False,
) -> str:
    ensure_pexpect()
    child.sendline(command)
    chunks: list[str] = []
    patterns = [prompt_regex] + PAGER_PATTERNS + CONFIRM_PATTERNS + [pexpect.TIMEOUT, pexpect.EOF]

    while True:
        index = child.expect(patterns, timeout=timeout or child.timeout)
        chunks.append(child.before)
        if index == 0:
            break
        if 1 <= index <= len(PAGER_PATTERNS):
            child.send(" ")
            continue
        if len(PAGER_PATTERNS) < index <= len(PAGER_PATTERNS) + len(CONFIRM_PATTERNS):
            if auto_confirm:
                child.sendline("Y")
                continue
            child.sendline("N")
            raise RuntimeError(f"Interactive confirmation appeared while running: {command}")
        if index == len(patterns) - 2:
            raise RuntimeError(f"Timed out while waiting for prompt after: {command}")
        raise RuntimeError(f"Device session closed while running: {command}")

    return clean_device_output("".join(chunks), command=command)


def disable_paging(child: Any, prompt_regex: str = DEFAULT_PROMPT_REGEX, timeout: int | None = None) -> dict[str, Any]:
    try:
        output = run_command(child, "screen-length disable", prompt_regex=prompt_regex, timeout=timeout, auto_confirm=False)
        return {"success": True, "output": output}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
