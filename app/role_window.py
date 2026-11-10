from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon, PrimaryPushButton

from .config import AppSettings
from .fx import APP_QSS, HudHeader, SciFiBackdrop, center_on_screen
from .services.os_info import detect_os
from .widgets import RoleCard


class RoleWindow(QWidget):
    role_chosen = pyqtSignal(str)
    logout_requested = pyqtSignal()

    def __init__(self, username: str, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.username = username
        self.settings = settings
        self.os = detect_os()
        self.setObjectName("roleWindow")
        self.setWindowTitle("Y-Proxy · 选择模式")
        self.resize(920, 620)
        self.setMinimumSize(820, 560)
        self._build_ui()
        center_on_screen(self)
        QTimer.singleShot(40, self._play_enter)

    def _build_ui(self) -> None:
        self.backdrop = SciFiBackdrop(self)
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 28)
        root.setSpacing(18)

        header_row = QHBoxLayout()
        self.header = HudHeader(
            "选择工作模式",
            f"你好，{self.username}。出站端共享本机出口，入网端通过局域网接入。",
            meta=f"SYSTEM · {self.os.display.upper()} · LINK READY",
        )
        header_row.addWidget(self.header, 1)
        logout = PrimaryPushButton(FluentIcon.POWER_BUTTON, "退出登录", self)
        logout.clicked.connect(self.logout_requested.emit)
        header_row.addWidget(logout, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header_row)

        self.tip = QLabel(
            "两台机器需在同一局域网。先启动出站端中转，再在入网端填写局域网地址。"
            "Windows 与 Linux 均可使用。"
        )
        self.tip.setObjectName("hudSubtitle")
        self.tip.setWordWrap(True)
        root.addWidget(self.tip)

        self.gatewayCard = RoleCard(
            FluentIcon.WIFI,
            "出站端",
            "本机已能上网。检测本地代理端口、放行防火墙，并向局域网开放中转。",
            "进入出站端",
            self,
        )
        self.clientCard = RoleCard(
            FluentIcon.CONNECT,
            "入网端",
            "本机需要借用局域网出口。填写出站端地址，测试连通，并配置终端代理。",
            "进入入网端",
            self,
        )
        self.gatewayCard.actionButton.clicked.connect(lambda: self._choose("gateway"))
        self.clientCard.actionButton.clicked.connect(lambda: self._choose("client"))
        root.addWidget(self.gatewayCard)
        root.addWidget(self.clientCard)
        root.addStretch(1)

        self.note = QLabel(f"上次选择 · {self._role_label(self.settings.last_role()) or '无'}")
        self.note.setObjectName("hudMeta")
        root.addWidget(self.note)

        self.setStyleSheet(APP_QSS)
        self.header.pulse.set_active(True, "ONLINE")

        # Avoid QGraphicsEffect on Fluent widgets — nested painters flood the console.
        self._reveal = [self.header, self.tip, self.gatewayCard, self.clientCard, self.note]
        for widget in self._reveal:
            widget.hide()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.backdrop.setGeometry(self.rect())
        self.backdrop.lower()

    def _play_enter(self) -> None:
        for index, widget in enumerate(self._reveal):
            QTimer.singleShot(60 + index * 70, widget.show)

    def _choose(self, role: str) -> None:
        self.settings.set_last_role(role)
        self.role_chosen.emit(role)

    @staticmethod
    def _role_label(role: str) -> str:
        return {"gateway": "出站端", "client": "入网端"}.get(role, "")
