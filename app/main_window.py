from __future__ import annotations

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from qfluentwidgets import FluentIcon, FluentWindow, NavigationItemPosition

from .client_page import ClientPage
from .config import AppSettings
from .fx import BG_DEEP, center_on_screen
from .gateway_page import GatewayPage


# Match SciFiBackdrop mid-tone so any leftover Fluent frame blends in (not #202020 black).
_FRAME = BG_DEEP
_FRAME_LINE = "rgba(45, 226, 230, 0.35)"


def _paint_fluent_chrome(window: FluentWindow) -> None:
    """Retint Fluent chrome: window fill + stack frame use theme teal instead of black."""
    window.setMicaEffectEnabled(False)
    c = QColor(_FRAME)
    window.setCustomBackgroundColor(c, c)
    # Directly poke the private fields Fluent paintEvent reads (belt + suspenders).
    window._lightBackgroundColor = QColor(_FRAME)
    window._darkBackgroundColor = QColor(_FRAME)
    window.setBackgroundColor(c)

    window.setStyleSheet(
        f"""
        FluentWindow, FluentWindowBase {{
            background-color: {_FRAME};
        }}
        NavigationInterface {{
            background-color: {_FRAME};
            border: none;
        }}
        """
    )
    window.stackedWidget.setStyleSheet(
        f"""
        StackedWidget,
        StackedWidget[isTransparent=\"false\"],
        StackedWidget[isTransparent=\"true\"] {{
            background-color: {_FRAME};
            border: 1px solid {_FRAME_LINE};
            border-right: none;
            border-bottom: none;
            border-top-left-radius: 10px;
        }}
        """
    )


class GatewayWindow(FluentWindow):
    switch_role = pyqtSignal()
    logout_requested = pyqtSignal()

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Y-Proxy · 出站端")
        self.resize(980, 700)
        self.setMinimumSize(820, 600)
        _paint_fluent_chrome(self)

        self.gatewayPage = GatewayPage(settings, self)
        self.gatewayPage.setObjectName("gatewayInterface")
        self.addSubInterface(
            self.gatewayPage, FluentIcon.WIFI, "出站端", isTransparent=True
        )
        _paint_fluent_chrome(self)
        QTimer.singleShot(0, lambda: _paint_fluent_chrome(self))

        self.navigationInterface.addItem(
            routeKey="switchRole",
            icon=FluentIcon.SYNC,
            text="切换模式",
            onClick=self.switch_role.emit,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )
        self.navigationInterface.addItem(
            routeKey="logout",
            icon=FluentIcon.POWER_BUTTON,
            text="退出登录",
            onClick=self.logout_requested.emit,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )
        center_on_screen(self)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.gatewayPage.shutdown()
        super().closeEvent(event)


class ClientWindow(FluentWindow):
    switch_role = pyqtSignal()
    logout_requested = pyqtSignal()

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Y-Proxy · 入网端")
        self.resize(980, 700)
        self.setMinimumSize(820, 600)
        _paint_fluent_chrome(self)

        self.clientPage = ClientPage(settings, self)
        self.clientPage.setObjectName("clientInterface")
        self.addSubInterface(
            self.clientPage, FluentIcon.CONNECT, "入网端", isTransparent=True
        )
        _paint_fluent_chrome(self)
        QTimer.singleShot(0, lambda: _paint_fluent_chrome(self))

        self.navigationInterface.addItem(
            routeKey="switchRole",
            icon=FluentIcon.SYNC,
            text="切换模式",
            onClick=self.switch_role.emit,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )
        self.navigationInterface.addItem(
            routeKey="logout",
            icon=FluentIcon.POWER_BUTTON,
            text="退出登录",
            onClick=self.logout_requested.emit,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )
        center_on_screen(self)
