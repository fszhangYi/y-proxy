from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
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
from .services.client_ops import ClientOps, TestResult


class Worker(QThread):
    finished_result = pyqtSignal(object)

    def __init__(self, fn, parent=None) -> None:
        super().__init__(parent)
        self._fn = fn

    def run(self) -> None:
        try:
            self.finished_result.emit(self._fn())
        except Exception as exc:  # noqa: BLE001
            self.finished_result.emit(TestResult(False, "执行失败", str(exc)))


class ClientPage(QWidget):
    """入网端：通过局域网出站端上网。"""

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.ops = ClientOps(settings.client_host(), settings.client_port())
        self._worker: Worker | None = None
        self.setObjectName("clientPage")
        self._build_ui()
        self._refresh_commands()

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
        body.setObjectName("clientBody")
        body.setStyleSheet("#clientBody{background:transparent;border:none;}")
        scroll.setWidget(body)
        root = QVBoxLayout(body)
        root.setContentsMargins(28, 22, 28, 24)
        root.setSpacing(16)

        self.header = HudHeader(
            "入网端",
            "填写出站端局域网地址，测试连通，再配置终端代理。",
            meta=f"NODE · {self.ops.os.display.upper()} · INGRESS",
        )
        root.addWidget(self.header)

        link_panel = GlassPanel("连接出站端", "使用出站端局域网 IP 与监听端口。")
        form = QHBoxLayout()
        host_col = QVBoxLayout()
        host_col.addWidget(self._field_label("出站端局域网 IP"))
        self.hostEdit = LineEdit()
        self.hostEdit.setText(self.settings.client_host())
        self.hostEdit.setPlaceholderText("192.168.1.33")
        host_col.addWidget(self.hostEdit)
        form.addLayout(host_col, 1)
        port_col = QVBoxLayout()
        port_col.addWidget(self._field_label("端口"))
        self.portSpin = SpinBox()
        self.portSpin.setRange(1024, 65535)
        self.portSpin.setValue(self.settings.client_port())
        port_col.addWidget(self.portSpin)
        form.addLayout(port_col)
        link_panel.body.addLayout(form)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.pingBtn = PushButton(FluentIcon.SEARCH, "Ping 出站端")
        self.tcpBtn = PushButton(FluentIcon.CONNECT, "测试 TCP")
        self.webBtn = PrimaryPushButton(FluentIcon.GLOBE, "测试上网")
        self.applyBtn = PushButton(FluentIcon.ACCEPT, "应用进程代理")
        self.clearBtn = PushButton(FluentIcon.DELETE, "清除进程代理")
        for btn in (self.pingBtn, self.tcpBtn, self.webBtn, self.applyBtn, self.clearBtn):
            buttons.addWidget(btn)
        buttons.addStretch(1)
        link_panel.body.addLayout(buttons)

        self.envLabel = QLabel("当前进程代理：无")
        self.envLabel.setObjectName("panelHint")
        self.envLabel.setWordWrap(True)
        link_panel.body.addWidget(self.envLabel)
        root.addWidget(link_panel)

        cmd_panel = GlassPanel("终端命令", "复制到需要走代理的终端执行。")
        self.cmdEdit = TextEdit()
        self.cmdEdit.setReadOnly(True)
        self.cmdEdit.setMinimumHeight(150)
        cmd_panel.body.addWidget(self.cmdEdit)
        cmd_btns = QHBoxLayout()
        self.copyExportBtn = PushButton("复制 export")
        self.copyAgentBtn = PushButton("复制带代理启动")
        self.copyUnsetBtn = PushButton("复制 unset")
        for btn in (self.copyExportBtn, self.copyAgentBtn, self.copyUnsetBtn):
            cmd_btns.addWidget(btn)
        cmd_btns.addStretch(1)
        cmd_panel.body.addLayout(cmd_btns)
        root.addWidget(cmd_panel)

        log_panel = GlassPanel("结果日志", "连通与上网测试输出。")
        self.logEdit = TextEdit()
        self.logEdit.setReadOnly(True)
        self.logEdit.setMinimumHeight(180)
        log_panel.body.addWidget(self.logEdit)
        tip = QLabel(
            "进程代理只影响本应用及其子进程，不会自动改浏览器。"
            "命令行工具需先执行 export；已运行的进程看不到新的环境变量，需重新启动。"
            "用完后执行 unset，并把浏览器代理改回关闭。"
        )
        tip.setObjectName("panelHint")
        tip.setWordWrap(True)
        log_panel.body.addWidget(tip)
        root.addWidget(log_panel, 1)

        self.setStyleSheet(APP_QSS)
        self.header.pulse.set_active(False, "STANDBY")

        self.hostEdit.textChanged.connect(self._on_endpoint_changed)
        self.portSpin.valueChanged.connect(self._on_endpoint_changed)
        self.pingBtn.clicked.connect(self._do_ping)
        self.tcpBtn.clicked.connect(self._do_tcp)
        self.webBtn.clicked.connect(self._do_web)
        self.applyBtn.clicked.connect(self._apply_env)
        self.clearBtn.clicked.connect(self._clear_env)
        self.copyExportBtn.clicked.connect(lambda: self._copy(self.ops.export_commands()))
        self.copyAgentBtn.clicked.connect(lambda: self._copy(self.ops.agent_commands()))
        self.copyUnsetBtn.clicked.connect(lambda: self._copy(self.ops.unset_commands()))

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.backdrop.setGeometry(self.rect())
        self.backdrop.lower()

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("panelHint")
        return label

    def _sync_ops(self) -> None:
        host = self.hostEdit.text().strip()
        port = int(self.portSpin.value())
        self.ops.set_gateway(host, port)
        self.settings.set_client_host(host)
        self.settings.set_client_port(port)

    def _on_endpoint_changed(self, *_args) -> None:
        self._sync_ops()
        self._refresh_commands()

    def _refresh_commands(self) -> None:
        self._sync_ops()
        text = (
            "# 设置终端代理\n"
            f"{self.ops.export_commands()}\n\n"
            "# 带代理启动命令行工具（示例：agent）\n"
            f"{self.ops.agent_commands()}\n\n"
            "# 清除终端代理\n"
            f"{self.ops.unset_commands()}\n"
        )
        self.cmdEdit.setPlainText(text)
        env = self.ops.current_env_proxy()
        if env:
            self.envLabel.setText(
                "当前进程代理\n" + "\n".join(f"{k}={v}" for k, v in env.items())
            )
            self.header.pulse.set_active(True, "PROXY SET")
        else:
            self.envLabel.setText("当前进程代理：无")
            self.header.pulse.set_active(False, "STANDBY")

    def _append(self, title: str, result: TestResult) -> None:
        self.logEdit.append(f"[{title}] {result.message}")
        if result.detail:
            self.logEdit.append(result.detail)
        self.logEdit.append("")
        if result.ok:
            self.header.pulse.set_active(True, "LINK OK")

    def _run_async(self, title: str, fn) -> None:
        if self._worker is not None and self._worker.isRunning():
            InfoBar.info(
                title="请稍候",
                content="上一个检测还在进行",
                position=InfoBarPosition.TOP,
                parent=self,
                duration=1800,
            )
            return
        self._sync_ops()
        self.header.pulse.set_active(True, "SCANNING")
        self._worker = Worker(fn, self)

        def done(result: TestResult) -> None:
            self._append(title, result)
            bar = InfoBar.success if result.ok else InfoBar.warning
            bar(
                title=title,
                content=result.message,
                position=InfoBarPosition.TOP,
                parent=self,
                duration=2800,
            )
            if not result.ok:
                self.header.pulse.set_active(False, "STANDBY")

        self._worker.finished_result.connect(done)
        self._worker.start()

    def _do_ping(self) -> None:
        self._run_async("Ping", self.ops.ping_gateway)

    def _do_tcp(self) -> None:
        self._run_async("TCP", self.ops.tcp_reachable)

    def _do_web(self) -> None:
        self._run_async("上网", self.ops.fetch_egress_ip)

    def _apply_env(self) -> None:
        self._sync_ops()
        self.ops.apply_process_env()
        self._refresh_commands()
        InfoBar.success(
            title="已应用",
            content=self.ops.proxy_url,
            position=InfoBarPosition.TOP,
            parent=self,
            duration=2000,
        )

    def _clear_env(self) -> None:
        self.ops.clear_process_env()
        self._refresh_commands()
        InfoBar.success(
            title="已清除",
            content="进程代理环境变量已删除",
            position=InfoBarPosition.TOP,
            parent=self,
            duration=2000,
        )

    def _copy(self, text: str) -> None:
        QApplication.clipboard().setText(text)
        InfoBar.success(
            title="已复制",
            content="粘贴到目标终端即可",
            position=InfoBarPosition.TOP,
            parent=self,
            duration=1800,
        )
