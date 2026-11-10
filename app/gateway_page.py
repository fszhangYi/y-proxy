from __future__ import annotations

import re
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import (
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SpinBox,
    TextEdit,
)

from .config import AppSettings
from .fx import APP_QSS, GlassPanel, HudHeader, SciFiBackdrop
from .services.gateway_ops import GatewayOps
from .services.relay_core import RelayServer


class RelayWorker(QThread):
    log_line = pyqtSignal(str)
    failed = pyqtSignal(str)
    started_ok = pyqtSignal()

    def __init__(
        self,
        listen_host: str,
        listen_port: int,
        target_host: str,
        target_port: int,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self._server: Optional[RelayServer] = None

    def run(self) -> None:
        self._server = RelayServer(
            listen_host=self.listen_host,
            listen_port=self.listen_port,
            target_host=self.target_host,
            target_port=self.target_port,
            log=lambda msg: self.log_line.emit(msg),
        )
        try:
            self.started_ok.emit()
            self._server.start_blocking()
        except OSError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))

    def stop_relay(self) -> None:
        if self._server is not None:
            self._server.stop()


class GatewayPage(QWidget):
    """出站端：本机已能上网，向局域网开放中转。"""

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.ops = GatewayOps(listen_port=settings.gateway_listen_port())
        self.worker: Optional[RelayWorker] = None
        self.setObjectName("gatewayPage")
        self._build_ui()
        self.refresh_status()

    def _build_ui(self) -> None:
        self.backdrop = SciFiBackdrop(self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "ScrollArea,QScrollArea{border:none;background:transparent;}"
            "QWidget{background:transparent;}"
        )
        scroll.viewport().setStyleSheet("background: transparent;")
        outer.addWidget(scroll)

        body = QWidget()
        body.setObjectName("gatewayBody")
        body.setStyleSheet("#gatewayBody{background:transparent;border:none;}")
        scroll.setWidget(body)
        root = QVBoxLayout(body)
        root.setContentsMargins(28, 22, 28, 24)
        root.setSpacing(16)

        self.header = HudHeader(
            "出站端",
            "确认本机代理端口、放行防火墙，并启动局域网中转，供入网端接入。",
            meta=f"NODE · {self.ops.os.display.upper()} · EGRESS",
        )
        root.addWidget(self.header)

        status_panel = GlassPanel("链路状态", "自动检测本机局域网地址与代理端口。")
        self.lanLabel = QLabel("")
        self.lanLabel.setObjectName("panelHint")
        self.lanLabel.setWordWrap(True)
        self.vpnLabel = QLabel("")
        self.vpnLabel.setObjectName("panelHint")
        self.vpnLabel.setWordWrap(True)
        status_panel.body.addWidget(self.lanLabel)
        status_panel.body.addWidget(self.vpnLabel)
        root.addWidget(status_panel)

        config_panel = GlassPanel("中转配置", "监听端口对局域网开放，目标指向本机代理。")
        form = QHBoxLayout()
        form.setSpacing(14)
        left = QVBoxLayout()
        left.addWidget(self._field_label("局域网监听端口"))
        self.listenSpin = SpinBox()
        self.listenSpin.setRange(1024, 65535)
        self.listenSpin.setValue(self.settings.gateway_listen_port())
        left.addWidget(self.listenSpin)
        form.addLayout(left)
        right = QVBoxLayout()
        right.addWidget(self._field_label("本机代理目标（host:port）"))
        self.targetEdit = LineEdit()
        self.targetEdit.setText(self.settings.gateway_target())
        self.targetEdit.setPlaceholderText("127.0.0.1:9674")
        right.addWidget(self.targetEdit)
        form.addLayout(right, 1)
        config_panel.body.addLayout(form)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.refreshBtn = PushButton(FluentIcon.SYNC, "刷新检测")
        self.firewallBtn = PushButton(FluentIcon.CERTIFICATE, "放行防火墙")
        self.detectBtn = PushButton(FluentIcon.SEARCH, "探测代理端口")
        self.startBtn = PrimaryPushButton(FluentIcon.PLAY, "启动中转")
        self.stopBtn = PushButton(FluentIcon.PAUSE, "停止中转")
        self.stopBtn.setEnabled(False)
        for btn in (
            self.refreshBtn,
            self.firewallBtn,
            self.detectBtn,
            self.startBtn,
            self.stopBtn,
        ):
            buttons.addWidget(btn)
        buttons.addStretch(1)
        config_panel.body.addLayout(buttons)
        root.addWidget(config_panel)

        log_panel = GlassPanel("运行日志", "实时输出中转连接事件。")
        self.logEdit = TextEdit()
        self.logEdit.setReadOnly(True)
        self.logEdit.setMinimumHeight(240)
        log_panel.body.addWidget(self.logEdit)
        tip = QLabel(
            "启动后，把本机局域网 IP 和监听端口告诉入网端。"
            "入网端不要填 127.0.0.1，也不要填手机热点或 169.254 地址。"
            "放行防火墙通常需要管理员权限。"
        )
        tip.setObjectName("panelHint")
        tip.setWordWrap(True)
        log_panel.body.addWidget(tip)
        root.addWidget(log_panel, 1)

        self.setStyleSheet(APP_QSS)
        self.refreshBtn.clicked.connect(self.refresh_status)
        self.firewallBtn.clicked.connect(self.add_firewall)
        self.detectBtn.clicked.connect(self.detect_target)
        self.startBtn.clicked.connect(self.start_relay)
        self.stopBtn.clicked.connect(self.stop_relay)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.backdrop.setGeometry(self.rect())
        self.backdrop.lower()

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("panelHint")
        return label

    def append_log(self, text: str) -> None:
        self.logEdit.append(text)

    def refresh_status(self) -> None:
        self.ops.listen_port = int(self.listenSpin.value())
        ips = self.ops.recommended_lan_ips()
        if ips:
            lines = [f"{name}: {ip}" for name, ip in ips]
            self.lanLabel.setText("本机局域网地址\n" + "\n".join(lines))
        else:
            self.lanLabel.setText("本机局域网地址\n未检测到，请手动确认。")

        ports = self.ops.probe_vpn_ports()
        if ports:
            self.vpnLabel.setText(
                "本机代理端口  "
                + ", ".join(f"{p.address}:{p.port}" for p in ports)
            )
        else:
            self.vpnLabel.setText(
                "本机代理端口  未检测到 9674/9675/9676。"
                "请先启动本机代理客户端，并确认代理端口已在监听。"
            )

        running = self.worker is not None and self.worker.isRunning()
        self.header.pulse.set_active(
            running,
            "RELAY ONLINE" if running else "STANDBY",
        )

    def detect_target(self) -> None:
        target = self.ops.detect_http_target()
        if target is None:
            InfoBar.warning(
                title="未找到端口",
                content="没有探测到可用的本机代理端口",
                position=InfoBarPosition.TOP,
                parent=self,
                duration=2500,
            )
            return
        value = f"{target.address}:{target.port}"
        self.targetEdit.setText(value)
        self.settings.set_gateway_target(value)
        InfoBar.success(
            title="已填入",
            content=value,
            position=InfoBarPosition.TOP,
            parent=self,
            duration=2000,
        )

    def add_firewall(self) -> None:
        self.ops.listen_port = int(self.listenSpin.value())
        ok, detail = self.ops.ensure_firewall_rule()
        self.append_log(detail)
        if ok:
            InfoBar.success(
                title="防火墙",
                content="规则已就绪",
                position=InfoBarPosition.TOP,
                parent=self,
                duration=2500,
            )
        else:
            InfoBar.error(
                title="防火墙失败",
                content="可能需要管理员权限运行本程序",
                position=InfoBarPosition.TOP,
                parent=self,
                duration=4000,
            )

    def start_relay(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return

        listen_port = int(self.listenSpin.value())
        target = self.targetEdit.text().strip()
        match = re.fullmatch(r"([^:\s]+):(\d+)", target)
        if not match:
            InfoBar.warning(
                title="目标格式错误",
                content="请使用 host:port，例如 127.0.0.1:9674",
                position=InfoBarPosition.TOP,
                parent=self,
                duration=3000,
            )
            return

        target_host, target_port = match.group(1), int(match.group(2))
        self.settings.set_gateway_listen_port(listen_port)
        self.settings.set_gateway_target(target)
        self.ops.listen_port = listen_port

        if not self.ops.probe_vpn_ports():
            InfoBar.warning(
                title="提醒",
                content="尚未检测到本机代理端口，中转仍可启动，但入网端可能连不上外网",
                position=InfoBarPosition.TOP,
                parent=self,
                duration=4000,
            )

        self.worker = RelayWorker("0.0.0.0", listen_port, target_host, target_port, self)
        self.worker.log_line.connect(self.append_log)
        self.worker.failed.connect(self._on_worker_failed)
        self.worker.started_ok.connect(self._on_worker_started)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)
        self.header.pulse.set_active(True, "BOOTING")
        self.append_log(f"starting relay 0.0.0.0:{listen_port} -> {target}")

    def stop_relay(self) -> None:
        if self.worker is None:
            return
        self.append_log("stopping…")
        self.worker.stop_relay()
        self.worker.wait(3000)
        if self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(1000)
        self._on_worker_finished()

    def _on_worker_started(self) -> None:
        self.header.pulse.set_active(True, "RELAY ONLINE")
        InfoBar.success(
            title="已启动",
            content="入网端现在可以连接本机局域网 IP",
            position=InfoBarPosition.TOP,
            parent=self,
            duration=2500,
        )

    def _on_worker_failed(self, message: str) -> None:
        self.append_log(f"error: {message}")
        InfoBar.error(
            title="启动失败",
            content=message,
            position=InfoBarPosition.TOP,
            parent=self,
            duration=4000,
        )
        self._on_worker_finished()

    def _on_worker_finished(self) -> None:
        self.worker = None
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        self.header.pulse.set_active(False, "STANDBY")

    def shutdown(self) -> None:
        self.stop_relay()
