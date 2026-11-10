from __future__ import annotations

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass
from typing import Optional
from urllib.request import ProxyHandler, Request, build_opener

from .os_info import detect_os


@dataclass(frozen=True)
class TestResult:
    ok: bool
    message: str
    detail: str = ""


class ClientOps:
    """Operations for the machine that borrows a LAN gateway exit."""

    def __init__(self, gateway_host: str = "192.168.1.33", gateway_port: int = 17890) -> None:
        self.gateway_host = gateway_host
        self.gateway_port = gateway_port
        self.os = detect_os()

    @property
    def proxy_url(self) -> str:
        return f"http://{self.gateway_host}:{self.gateway_port}"

    def set_gateway(self, host: str, port: int) -> None:
        self.gateway_host = host.strip()
        self.gateway_port = int(port)

    def tcp_reachable(self, timeout: float = 3.0) -> TestResult:
        try:
            with socket.create_connection((self.gateway_host, self.gateway_port), timeout=timeout):
                return TestResult(True, f"已连通 {self.gateway_host}:{self.gateway_port}")
        except OSError as exc:
            return TestResult(False, "无法连接出站端", str(exc))

    def fetch_egress_ip(self, timeout: float = 25.0) -> TestResult:
        url = "https://ifconfig.me"
        proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url,
        }
        try:
            opener = build_opener(ProxyHandler(proxies))
            request = Request(url, headers={"User-Agent": "y-proxy-client"})
            with opener.open(request, timeout=timeout) as resp:
                body = resp.read(200).decode("utf-8", "replace").strip()
            if not body:
                return TestResult(False, "代理返回空内容")
            if body.startswith("192.168.") or body.startswith("172.20.") or body.startswith("10."):
                return TestResult(False, f"出口像是内网地址: {body}", "流量可能未经过出站端代理")
            return TestResult(True, f"出口 IP: {body}", body)
        except Exception as exc:
            # Fall back to curl if present; urllib on some Linux builds may lack SSL proxies.
            curl = shutil.which("curl")
            if not curl:
                return TestResult(False, "代理测试失败", str(exc))
            try:
                completed = subprocess.run(
                    [curl, "-sS", "-m", str(int(timeout)), "-x", self.proxy_url, url],
                    capture_output=True,
                    text=True,
                    timeout=timeout + 5,
                    check=False,
                )
            except Exception as curl_exc:
                return TestResult(False, "代理测试失败", f"{exc}; curl: {curl_exc}")
            body = (completed.stdout or "").strip()
            err = (completed.stderr or "").strip()
            if completed.returncode != 0 or not body:
                return TestResult(False, "代理测试失败", err or str(exc))
            return TestResult(True, f"出口 IP: {body}", body)

    def export_commands(self) -> str:
        url = self.proxy_url
        return "\n".join(
            [
                f"export http_proxy={url}",
                f"export https_proxy={url}",
                f"export HTTP_PROXY={url}",
                f"export HTTPS_PROXY={url}",
            ]
        )

    def agent_commands(self) -> str:
        return self.export_commands() + "\nagent"

    def unset_commands(self) -> str:
        return "unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY"

    def apply_process_env(self) -> None:
        url = self.proxy_url
        for key in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
            os.environ[key] = url

    def clear_process_env(self) -> None:
        for key in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
            os.environ.pop(key, None)

    def current_env_proxy(self) -> dict[str, str]:
        keys = ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY")
        return {k: os.environ[k] for k in keys if k in os.environ}

    def ping_gateway(self, count: int = 3) -> TestResult:
        host = self.gateway_host
        if self.os.is_windows:
            cmd = ["ping", "-n", str(count), host]
        else:
            cmd = ["ping", "-c", str(count), host]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                timeout=20,
                check=False,
            )
        except Exception as exc:
            return TestResult(False, "ping 执行失败", str(exc))
        out = (_decode(completed.stdout) + _decode(completed.stderr)).strip()
        if completed.returncode == 0:
            return TestResult(True, "ping 成功", out[-500:])
        return TestResult(
            False,
            "ping 失败（Windows 常不回应，可继续测 TCP）",
            out[-500:],
        )


def _decode(data: bytes | None) -> str:
    if not data:
        return ""
    for encoding in ("utf-8", "gbk", "cp936"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")
