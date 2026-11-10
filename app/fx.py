from __future__ import annotations

import math
import random
from typing import Optional

from PyQt6.QtCore import QPointF, QRectF, QTimer, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import setThemeColor


ACCENT = "#2de2e6"
ACCENT_DIM = "#1a9aa0"
BG_DEEP = "#143044"
BG_PANEL = "#1a3a4e"
TEXT_MAIN = "#e6fbff"
TEXT_MUTED = "#9bc4ce"


def center_on_screen(widget: QWidget) -> None:
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return
    geo = screen.availableGeometry()
    widget.move(
        geo.x() + (geo.width() - widget.width()) // 2,
        geo.y() + (geo.height() - widget.height()) // 2,
    )


def apply_sci_fi_theme() -> None:
    setThemeColor(QColor(ACCENT))


APP_QSS = f"""
/* FluentWindow chrome — hide the default black frame behind pages */
FluentWindow, QMainWindow, QStackedWidget {{
    background: {BG_DEEP};
    border: none;
    color: {TEXT_MAIN};
}}
QWidget#roleWindow,
QWidget#gatewayPage, QWidget#gatewayInterface,
QWidget#clientPage, QWidget#clientInterface {{
    background: {BG_DEEP};
    border: none;
    color: {TEXT_MAIN};
}}
QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
    background: transparent;
    border: none;
}}
QLabel#hudTitle {{
    color: {TEXT_MAIN};
    font-size: 28px;
    font-weight: 700;
    letter-spacing: 1px;
    background: transparent;
}}
QLabel#hudSubtitle {{
    color: {TEXT_MUTED};
    font-size: 13px;
    background: transparent;
}}
QLabel#hudMeta {{
    color: rgba(125, 220, 230, 0.55);
    font-size: 11px;
    letter-spacing: 1.2px;
    background: transparent;
}}
QLabel#panelTitle {{
    color: {TEXT_MAIN};
    font-size: 14px;
    font-weight: 600;
    background: transparent;
}}
QLabel#panelHint {{
    color: {TEXT_MUTED};
    font-size: 12px;
    background: transparent;
}}
QFrame#glassPanel {{
    background: rgba(30, 72, 96, 0.82);
    border: 1px solid rgba(45, 226, 230, 0.42);
    border-radius: 14px;
}}
QFrame#roleCardFrame {{
    background: rgba(28, 66, 88, 0.9);
    border: 1px solid rgba(45, 226, 230, 0.38);
    border-radius: 16px;
}}
QFrame#roleCardFrame:hover {{
    border: 1px solid rgba(45, 226, 230, 0.7);
    background: rgba(34, 78, 102, 0.95);
}}
QTextEdit {{
    background: #163848;
    color: #b5f4f7;
    border: 1px solid rgba(45, 226, 230, 0.32);
    border-radius: 10px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
    padding: 8px;
}}
"""


class SciFiBackdrop(QWidget):
    """Animated deep-space grid with scanline and drifting nodes."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._phase = 0.0
        self._scan = 0.0
        self._nodes = [
            (random.random(), random.random(), 1.5 + random.random() * 2.5, random.random() * math.pi * 2)
            for _ in range(28)
        ]
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self) -> None:
        self._phase = (self._phase + 0.045) % (math.pi * 2)
        self._scan = (self._scan + 0.01) % 1.0
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = max(self.width(), 1), max(self.height(), 1)

        base = QLinearGradient(0, 0, w, h)
        # Keep mid-tone = BG_DEEP so Fluent chrome seams disappear.
        base.setColorAt(0.0, QColor("#1a4a60"))
        base.setColorAt(0.4, QColor(BG_DEEP))
        base.setColorAt(1.0, QColor("#12364a"))
        painter.fillRect(self.rect(), base)

        # Perspective floor.
        painter.setPen(QPen(QColor(45, 226, 230, 32), 1))
        horizon = int(h * 0.38)
        for i in range(1, 16):
            y = horizon + int((h - horizon) * (i / 16) ** 1.6)
            painter.drawLine(0, y, w, y)
        vanish = QPointF(w * 0.5, horizon)
        for i in range(-12, 13):
            x = w * 0.5 + i * w * 0.07
            painter.drawLine(vanish, QPointF(x, h))

        # Upper hex-ish sparse grid.
        painter.setPen(QPen(QColor(45, 226, 230, 22), 1))
        step = 48
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, horizon)
        for y in range(0, horizon, step):
            painter.drawLine(0, y, w, y)

        # Floating nodes + links.
        points = []
        for nx, ny, speed, seed in self._nodes:
            px = (nx * w + math.sin(self._phase * speed + seed) * 18) % w
            py = (ny * h * 0.55 + math.cos(self._phase * speed * 0.8 + seed) * 12) % max(horizon, 1)
            points.append(QPointF(px, py))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(45, 226, 230, 120))
            painter.drawEllipse(points[-1], 2.2, 2.2)

        painter.setPen(QPen(QColor(45, 226, 230, 28), 1))
        for i, p in enumerate(points):
            for q in points[i + 1 : i + 4]:
                if (p - q).manhattanLength() < 120:
                    painter.drawLine(p, q)

        # Soft cyan waves near the floor.
        for wi, (amp, y0, alpha, thick) in enumerate(
            (
                (16, h * 0.72, 55, 1.6),
                (11, h * 0.78, 36, 1.2),
                (8, h * 0.84, 24, 1.0),
            )
        ):
            path = QPainterPath()
            path.moveTo(0, y0)
            steps = 48
            for s in range(steps + 1):
                x = w * s / steps
                y = y0 + math.sin(self._phase * 1.2 + s * 0.28 + wi) * amp
                path.lineTo(x, y)
            painter.setPen(QPen(QColor(45, 226, 230, alpha), thick))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        # Scanline.
        scan_y = int(h * self._scan)
        scan = QLinearGradient(0, scan_y - 24, 0, scan_y + 24)
        scan.setColorAt(0.0, QColor(45, 226, 230, 0))
        scan.setColorAt(0.5, QColor(45, 226, 230, 40))
        scan.setColorAt(1.0, QColor(45, 226, 230, 0))
        painter.fillRect(0, scan_y - 24, w, 48, scan)

        # Soft side glow (left brand emphasis).
        side = QLinearGradient(0, 0, w * 0.55, 0)
        side.setColorAt(0.0, QColor(90, 210, 220, 28))
        side.setColorAt(0.45, QColor(45, 226, 230, 0))
        side.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), side)

        # Light center lift + mild edge falloff (less black).
        lift = QRadialGradient(w * 0.42, h * 0.38, max(w, h) * 0.7)
        lift.setColorAt(0.0, QColor(120, 210, 220, 28))
        lift.setColorAt(0.55, QColor(0, 0, 0, 0))
        lift.setColorAt(1.0, QColor(8, 24, 34, 55))
        painter.fillRect(self.rect(), lift)


class StatusPulse(QWidget):
    """Breathing status orb with label."""

    def __init__(self, text: str = "STANDBY", parent=None) -> None:
        super().__init__(parent)
        self._text = text
        self._active = False
        self._phase = 0.0
        self.setFixedHeight(28)
        self.setMinimumWidth(140)
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_active(self, active: bool, text: Optional[str] = None) -> None:
        self._active = active
        if text is not None:
            self._text = text
        self.update()

    def _tick(self) -> None:
        self._phase = (self._phase + 0.08) % (math.pi * 2)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        breath = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(self._phase))
        color = QColor(45, 226, 230) if self._active else QColor(120, 150, 160)
        alpha = int(90 + 120 * breath) if self._active else 70

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color.red(), color.green(), color.blue(), alpha // 3))
        painter.drawEllipse(QPointF(12, self.height() / 2), 8 + breath * 2, 8 + breath * 2)
        painter.setBrush(QColor(color.red(), color.green(), color.blue(), alpha))
        painter.drawEllipse(QPointF(12, self.height() / 2), 4.5, 4.5)

        painter.setPen(QColor(TEXT_MAIN if self._active else TEXT_MUTED))
        font = QFont("Segoe UI Semibold", 10)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        painter.setFont(font)
        painter.drawText(QRectF(28, 0, self.width() - 28, self.height()), Qt.AlignmentFlag.AlignVCenter, self._text)


class GlassPanel(QFrame):
    def __init__(self, title: str = "", hint: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("glassPanel")
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)
        if title:
            t = QLabel(title)
            t.setObjectName("panelTitle")
            root.addWidget(t)
        if hint:
            h = QLabel(hint)
            h.setObjectName("panelHint")
            h.setWordWrap(True)
            root.addWidget(h)
        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        root.addLayout(self.body)


class HudHeader(QWidget):
    def __init__(self, title: str, subtitle: str, meta: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        self.titleLabel = QLabel(title)
        self.titleLabel.setObjectName("hudTitle")
        self.subtitleLabel = QLabel(subtitle)
        self.subtitleLabel.setObjectName("hudSubtitle")
        self.subtitleLabel.setWordWrap(True)
        text_col.addWidget(self.titleLabel)
        text_col.addWidget(self.subtitleLabel)
        if meta:
            self.metaLabel = QLabel(meta)
            self.metaLabel.setObjectName("hudMeta")
            text_col.addWidget(self.metaLabel)
        layout.addLayout(text_col, 1)

        self.pulse = StatusPulse("STANDBY", self)
        layout.addWidget(self.pulse, 0, Qt.AlignmentFlag.AlignTop)
