from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SnifferEvent(BaseModel):
    ts: Optional[int] = Field(default=None, description="Epoch timestamp in nanoseconds")
    proto: str = Field(default="UNKNOWN")
    src: Optional[str] = None
    dst: Optional[str] = None
    length: Optional[int] = Field(default=None, alias="len")
    info: Optional[str] = None
    node: str
    intf: str
    type: str

    model_config = {"populate_by_name": True}

    @field_validator("src", "dst", mode="before")
    @classmethod
    def coerce_address(cls, value):
        if value is None:
            return None
        if hasattr(value, "value") and value.value is not None:
            return str(value.value)
        if hasattr(value, "get_default_value"):
            return str(value.get_default_value())
        return str(value)


def parse_tshark_packet(packet, node_info, intf_name) -> Optional[SnifferEvent]:
    proto = "UNKNOWN"
    src = None
    dst = None
    info = None

    if "ip" in packet:
        proto = "IP"
        src = packet.ip.get_field("src")
        dst = packet.ip.get_field("dst")
    elif "ipv6" in packet:
        proto = "IP6"
        src = packet.ipv6.get_field("src")
        dst = packet.ipv6.get_field("dst")
    elif "arp" in packet:
        proto = "ARP"
        src = packet.arp.get_field("src_proto_ipv4")
        dst = packet.arp.get_field("dst_proto_ipv4")

    if "tcp" in packet:
        proto = "TCP"
        src_port = packet.tcp.get_field("srcport")
        dst_port = packet.tcp.get_field("dstport")
        flags = packet.tcp.get_field("flags_str")
        info = f"{src_port} -> {dst_port}"
        if flags:
            info += f" [{flags}]"
    elif "udp" in packet:
        proto = "UDP"
        src_port = packet.udp.get_field("srcport")
        dst_port = packet.udp.get_field("dstport")
        info = f"{src_port} -> {dst_port}"
    elif "icmp" in packet:
        proto = "ICMP"
        icmp_type = packet.icmp.get_field("type")
        icmp_code = packet.icmp.get_field("code")
        info = f"type={icmp_type} code={icmp_code}"
    elif "icmpv6" in packet:
        proto = "ICMP6"
        icmp_type = packet.icmpv6.get_field("type")
        icmp_code = packet.icmpv6.get_field("code")
        info = f"type={icmp_type} code={icmp_code}"

    ts_value = None
    if packet.sniff_timestamp:
        try:
            ts_float = float(packet.sniff_timestamp)
            ts_value = int(ts_float * 1_000_000_000)
        except Exception:
            ts_value = None

    return SnifferEvent(
        ts=ts_value,
        proto=proto,
        src=src,
        dst=dst,
        len=int(packet.length) if packet.length else None,
        info=info,
        node=node_info["id"],
        intf=intf_name,
        type=node_info["type"],
    )
