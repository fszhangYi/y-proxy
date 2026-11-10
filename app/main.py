from __future__ import annotations

import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator, Theme, setTheme

from .config import AppSettings
from .fx import apply_sci_fi_theme
from .login_window import LoginWindow
from .main_window import ClientWindow, GatewayWindow
from .role_window import RoleWindow


class AppController:
    def __init__(self) -> None:
        self.settings = AppSettings()
        self.username = ""
        self.login: Optional[LoginWindow] = None
        self.role: Optional[RoleWindow] = None
        self.main = None

    def start(self) -> None:
        self.show_login()

    def show_login(self) -> None:
        self._close_all()
        self.login = LoginWindow(self.settings)
        self.login.logged_in.connect(self._on_logged_in)
        self.login.show()

    def _on_logged_in(self, username: str) -> None:
        self.username = username
        if self.login is not None:
            self.login.close()
            self.login = None
        self.show_role()

    def show_role(self) -> None:
        if self.main is not None:
            if hasattr(self.main, "gatewayPage"):
                self.main.gatewayPage.shutdown()
            self.main.close()
            self.main = None
        self.role = RoleWindow(self.username, self.settings)
        self.role.role_chosen.connect(self._on_role_chosen)
        self.role.logout_requested.connect(self.show_login)
        self.role.show()

    def _on_role_chosen(self, role: str) -> None:
        if self.role is not None:
            self.role.close()
            self.role = None
        if role == "gateway":
            window = GatewayWindow(self.settings)
        else:
            window = ClientWindow(self.settings)
        window.switch_role.connect(self.show_role)
        window.logout_requested.connect(self.show_login)
        self.main = window
        window.show()

    def _close_all(self) -> None:
        if self.main is not None:
            if hasattr(self.main, "gatewayPage"):
                self.main.gatewayPage.shutdown()
            self.main.close()
            self.main = None
        if self.role is not None:
            self.role.close()
            self.role = None
        if self.login is not None:
            self.login.close()
            self.login = None


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Y-Proxy")
    app.setOrganizationName("y-proxy")

    translator = FluentTranslator()
    app.installTranslator(translator)
    setTheme(Theme.DARK)
    apply_sci_fi_theme()

    controller = AppController()
    controller.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
