from __future__ import annotations

import socket
import subprocess
from dataclasses import dataclass
from typing import Iterable, Optional

from .os_info import detect_os, lan_ipv4_addresses


DEFAULT_VPN_PORTS = (9674, 9675, 9676)
DEFAULT_LISTEN_PORT = 17890
FIREWALL_RULE_NAME = "y-proxy-17890"


@dataclass(frozen=True)
class PortListen:
    address: str
    port: int


def _decode(data: bytes | None) -> str:
    if not data:
        return ""
    for encoding in ("utf-8", "gbk", "cp936"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


class GatewayOps:
    """Operations for the machine that already has Internet and shares it on LAN."""

    def __init__(
        self,
        vpn_ports: Iterable[int] = DEFAULT_VPN_PORTS,
        listen_port: int = DEFAULT_LISTEN_PORT,
    ) -> None:
        self.vpn_ports = tuple(vpn_ports)
        self.listen_port = listen_port
        self.os = detect_os()

    def recommended_lan_ips(self) -> list[tuple[str, str]]:
        return lan_ipv4_addresses()

    def probe_vpn_ports(self) -> list[PortListen]:
        found: list[PortListen] = []
        for port in self.vpn_ports:
            for host in ("127.0.0.1",):
                if self._can_connect(host, port, timeout=0.4):
                    found.append(PortListen(host, port))
                    break
        return found

    def detect_http_target(self) -> Optional[PortListen]:
        for item in self.probe_vpn_ports():
            if self._looks_like_http_proxy(item.address, item.port):
                return item
        ports = self.probe_vpn_ports()
        return ports[0] if ports else None

    def ensure_firewall_rule(self) -> tuple[bool, str]:
        if not self.os.is_windows:
            return True, "非 Windows，跳过防火墙规则"

        remote = "192.168.0.0/24,192.168.1.0/24"
        cmd = [
            "netsh",
            "advfirewall",
            "firewall",
            "add",
            "rule",
            f"name={FIREWALL_RULE_NAME}",
            "dir=in",
            "action=allow",
            "protocol=TCP",
            f"localport={self.listen_port}",
            f"remoteip={remote}",
        ]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                timeout=20,
                check=False,
            )
        except Exception as exc:
            return False, f"执行失败: {exc}"

        out = _decode(completed.stdout) + _decode(completed.stderr)
        text = out.strip() or f"exit={completed.returncode}"
        if completed.returncode == 0 or "已经存在" in text or "exists" in text.lower():
            return True, text
        if completed.returncode != 0:
            ok, detail = self.firewall_rule_exists()
            if ok:
                return True, f"规则已存在。{detail}"
        return completed.returncode == 0, text

    def firewall_rule_exists(self) -> tuple[bool, str]:
        if not self.os.is_windows:
            return True, "非 Windows"
        cmd = [
            "netsh",
            "advfirewall",
            "firewall",
            "show",
            "rule",
            f"name={FIREWALL_RULE_NAME}",
        ]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                timeout=20,
                check=False,
            )
        except Exception as exc:
            return False, str(exc)
        out = _decode(completed.stdout) + _decode(completed.stderr)
        ok = completed.returncode == 0 and FIREWALL_RULE_NAME in out
        return ok, out.strip() or f"exit={completed.returncode}"

    def is_listen_port_open(self) -> bool:
        return self._port_is_bound(self.listen_port)

    @staticmethod
    def _can_connect(host: str, port: int, timeout: float = 0.5) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    @staticmethod
    def _looks_like_http_proxy(host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=1.5) as sock:
                sock.settimeout(1.5)
                sock.sendall(b"CONNECT 127.0.0.1:1 HTTP/1.1\r\nHost: 127.0.0.1:1\r\n\r\n")
                data = sock.recv(120)
            return data.startswith(b"HTTP/")
        except OSError:
            return False

    @staticmethod
    def _port_is_bound(port: int) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("0.0.0.0", port))
            return False
        except OSError:
            return True
        finally:
            sock.close()
