import os
import re
from typing import Dict, List, Optional


def parse_ip_addrs(output: str) -> List[str]:
    addrs = []
    for line in output.splitlines():
        match = re.search(r"\sinet6?\s+([0-9a-fA-F:.]+/\d+)", line)
        if match:
            addrs.append(match.group(1))
    return addrs


def parse_flow_match_from_dump(line: str) -> str:
    line = line.strip()
    if "actions=" not in line:
        raise ValueError("flow line missing actions")
    head = line.split(" actions=", 1)[0].strip()
    parts = [p.strip() for p in head.split(",") if p.strip()]
    match_parts = []
    cookie_value = None
    table_value = None
    priority_value = None
    skip_keys = {
        "duration",
        "n_packets",
        "n_bytes",
        "idle_timeout",
        "hard_timeout",
    }
    for part in parts:
        if part.startswith("cookie="):
            cookie_value = part.split("=", 1)[1]
            continue
        if part.startswith("table="):
            table_value = part.split("=", 1)[1]
            continue
        if part.startswith("priority="):
            priority_value = part.split("=", 1)[1]
            continue
        key = part.split("=", 1)[0]
        if key in skip_keys:
            continue
        match_parts.append(part)
    if cookie_value:
        if "/" not in cookie_value:
            cookie_value = f"{cookie_value}/-1"
        match_parts.insert(0, f"cookie={cookie_value}")
    if table_value is not None:
        match_parts.insert(0, f"table={table_value}")
    if priority_value is not None:
        match_parts.insert(0, f"priority={priority_value}")
    if not match_parts:
        raise ValueError("could not build match")
    return ",".join(match_parts)


def get_interface_stats_path(interface_name: str) -> Dict[str, str]:
    base_path = os.path.join("/sys/class/net", interface_name, "statistics")
    return {
        "tx": os.path.join(base_path, "tx_bytes"),
        "rx": os.path.join(base_path, "rx_bytes"),
    }


def read_interface_counter(path: str) -> Optional[int]:
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as stream:
            return int(stream.read().strip())
    except Exception:
        return None
