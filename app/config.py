from __future__ import annotations

from PyQt6.QtCore import QSettings


APP_NAME = "Y-Proxy"
ORG_NAME = "y-proxy"

# Local demo account. Replace with real auth later if needed.
DEMO_USER = "admin"
DEMO_PASSWORD = "admin"


class AppSettings:
    def __init__(self) -> None:
        self._settings = QSettings(ORG_NAME, APP_NAME)

    def remember_user(self) -> bool:
        return bool(self._settings.value("auth/remember", False))

    def set_remember_user(self, value: bool) -> None:
        self._settings.setValue("auth/remember", value)

    def saved_username(self) -> str:
        return str(self._settings.value("auth/username", DEMO_USER))

    def set_saved_username(self, username: str) -> None:
        self._settings.setValue("auth/username", username)

    def last_role(self) -> str:
        return str(self._settings.value("session/role", ""))

    def set_last_role(self, role: str) -> None:
        self._settings.setValue("session/role", role)

    def gateway_listen_port(self) -> int:
        return int(self._settings.value("gateway/listen_port", 17890))

    def set_gateway_listen_port(self, port: int) -> None:
        self._settings.setValue("gateway/listen_port", int(port))

    def gateway_target(self) -> str:
        return str(self._settings.value("gateway/target", "127.0.0.1:9674"))

    def set_gateway_target(self, value: str) -> None:
        self._settings.setValue("gateway/target", value)

    def client_host(self) -> str:
        return str(self._settings.value("client/host", "192.168.1.33"))

    def set_client_host(self, value: str) -> None:
        self._settings.setValue("client/host", value)

    def client_port(self) -> int:
        return int(self._settings.value("client/port", 17890))

    def set_client_port(self, port: int) -> None:
        self._settings.setValue("client/port", int(port))

    def verify_login(self, username: str, password: str) -> bool:
        return username.strip() == DEMO_USER and password == DEMO_PASSWORD
