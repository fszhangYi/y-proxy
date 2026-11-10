from __future__ import annotations

import json
import platform
import socket
from dataclasses import dataclass


@dataclass(frozen=True)
class OsInfo:
    system: str
    is_windows: bool
    is_linux: bool
    display: str


def detect_os() -> OsInfo:
    system = platform.system().lower()
    is_windows = system == "windows"
    is_linux = system == "linux"
    if is_windows:
        display = "Windows"
    elif is_linux:
        display = "Linux"
    else:
        display = platform.system() or "Unknown"
    return OsInfo(
        system=system,
        is_windows=is_windows,
        is_linux=is_linux,
        display=display,
    )


def lan_ipv4_addresses() -> list[tuple[str, str]]:
    """Return [(iface_or_source, ipv4), ...] excluding loopback and link-local."""
    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    if detect_os().is_windows:
        try:
            import subprocess

            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    (
                        "$OutputEncoding = [Console]::OutputEncoding = "
                        "[Text.UTF8Encoding]::new($false); "
                        "Get-NetIPAddress -AddressFamily IPv4 | "
                        "Where-Object { $_.IPAddress -notlike '127.*' "
                        "-and $_.IPAddress -notlike '169.254.*' } | "
                        "Select-Object InterfaceAlias, IPAddress | "
                        "ConvertTo-Json -Compress"
                    ),
                ],
                capture_output=True,
                timeout=20,
                check=False,
            )
            raw = completed.stdout or b""
            if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
                stdout = raw.decode("utf-16")
            else:
                stdout = raw.decode("utf-8", errors="replace")
            data = json.loads(stdout) if stdout.strip() else []
            if isinstance(data, dict):
                data = [data]
            for item in data:
                name = str(item.get("InterfaceAlias") or "nic")
                ip = str(item.get("IPAddress") or "")
                if ip and ip not in seen:
                    seen.add(ip)
                    results.append((name, ip))
        except Exception:
            pass

    if not results:
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
                ip = info[4][0]
                if ip.startswith("127.") or ip.startswith("169.254."):
                    continue
                if ip not in seen:
                    seen.add(ip)
                    results.append(("local", ip))
        except Exception:
            pass

    if not results:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            sock.close()
            if not ip.startswith("127."):
                results.append(("route", ip))
        except Exception:
            pass

    return results
