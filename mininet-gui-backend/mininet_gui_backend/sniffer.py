import asyncio
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field, field_validator
import pyshark.ek_field_mapping as ek_field_mapping
from pyshark.tshark.output_parser.tshark_ek import TsharkEkJsonParser


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


class SnifferManager:
    def __init__(
        self,
        interface_provider: Callable[[], List[dict]],
        process_factory: Callable[[int, str], asyncio.subprocess.Process],
    ):
        self._interface_provider = interface_provider
        self._process_factory = process_factory
        self._active = False
        self._history: List[dict] = []
        self._processes: Dict[Tuple[str, str], asyncio.subprocess.Process] = {}
        self._tasks: Dict[Tuple[str, str], asyncio.Task] = {}
        self._subscribers: Set[asyncio.Queue] = set()
        self._stop_event = asyncio.Event()
        self._lock = asyncio.Lock()
        self._runner_task: Optional[asyncio.Task] = None
        self._history_pcap: List[Tuple[int, bytes]] = []

    @property
    def active(self) -> bool:
        return self._active

    async def start(self):
        if self._active:
            return
        self._active = True
        self._stop_event.clear()
        try:
            ek_field_mapping.MAPPING.load_mapping("3.2.3")
        except Exception:
            pass
        self._runner_task = asyncio.create_task(self._run())

    async def stop(self):
        if not self._active:
            return
        self._active = False
        self._stop_event.set()
        if self._runner_task:
            self._runner_task.cancel()
        await self._shutdown()
        async with self._lock:
            self._history = []
            self._history_pcap = []

    async def _run(self):
        while not self._stop_event.is_set():
            await self._refresh_interfaces()
            await asyncio.sleep(1.0)

    async def _refresh_interfaces(self):
        current = self._interface_provider()
        current_keys: Set[Tuple[str, str]] = set()
        for node_info in current:
            for intf_name in node_info.get("intfs", []):
                key = (node_info["id"], intf_name)
                current_keys.add(key)
                if key not in self._processes:
                    await self._start_capture(node_info, intf_name)

        stale = [key for key in self._processes.keys() if key not in current_keys]
        for key in stale:
            await self._stop_capture(key)

    async def _start_capture(self, node_info, intf_name):
        key = (node_info["id"], intf_name)
        process = await self._process_factory(node_info.get("pid", 0), intf_name)
        self._processes[key] = process
        self._tasks[key] = asyncio.create_task(self._read_and_publish(node_info, intf_name, process))

    async def _stop_capture(self, key):
        process = self._processes.pop(key, None)
        task = self._tasks.pop(key, None)
        if task:
            task.cancel()
        if process:
            process.terminate()
            try:
                await process.wait()
            except Exception:
                pass

    async def _read_and_publish(self, node_info, intf_name, process):
        parser = TsharkEkJsonParser()
        buffer = b""
        got_first = False
        try:
            while not self._stop_event.is_set():
                try:
                    packet, buffer = await parser.get_packets_from_stream(
                        process.stdout, buffer, got_first_packet=got_first
                    )
                except EOFError:
                    break
                if packet is None:
                    continue
                got_first = True
                event = parse_tshark_packet(packet, node_info, intf_name)
                if not event:
                    continue
                payload = event.model_dump(by_alias=True)
                async with self._lock:
                    self._history.append(payload)
                    try:
                        raw_bytes = packet.get_raw_packet()
                        self._history_pcap.append((event.ts or 0, raw_bytes))
                    except Exception:
                        pass
                    for queue in list(self._subscribers):
                        if queue.full():
                            continue
                        queue.put_nowait(payload)
        except Exception:
            pass

    async def _shutdown(self):
        for key in list(self._tasks.keys()):
            await self._stop_capture(key)

    async def get_history(self) -> List[dict]:
        async with self._lock:
            return list(self._history)

    async def get_pcap(self) -> bytes:
        async with self._lock:
            packets = list(self._history_pcap)
        if not packets:
            return b""
        # Build a pcap global header + records
        header = b""
        header += (0xA1B2C3D4).to_bytes(4, "little")  # magic
        header += (2).to_bytes(2, "little")  # major
        header += (4).to_bytes(2, "little")  # minor
        header += (0).to_bytes(4, "little")  # thiszone
        header += (0).to_bytes(4, "little")  # sigfigs
        header += (262144).to_bytes(4, "little")  # snaplen
        header += (1).to_bytes(4, "little")  # network (Ethernet)

        records = bytearray()
        for ts_ns, pkt in packets:
            ts_sec = int(ts_ns / 1_000_000_000)
            ts_usec = int((ts_ns % 1_000_000_000) / 1_000)
            records += ts_sec.to_bytes(4, "little")
            records += ts_usec.to_bytes(4, "little")
            records += len(pkt).to_bytes(4, "little")
            records += len(pkt).to_bytes(4, "little")
            records += pkt
        return header + records

    async def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue(maxsize=2000)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue):
        async with self._lock:
            self._subscribers.discard(queue)
