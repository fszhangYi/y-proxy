from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    FluentIcon,
    IconWidget,
    PrimaryPushButton,
    PushButton,
)


class RoleCard(QFrame):
    def __init__(
        self,
        icon: FluentIcon,
        title: str,
        content: str,
        action_text: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("roleCardFrame")
        self.setFixedHeight(132)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QHBoxLayout(self)
        root.setContentsMargins(22, 16, 16, 16)
        root.setSpacing(16)

        self.iconWidget = IconWidget(icon, self)
        self.iconWidget.setFixedSize(46, 46)
        root.addWidget(self.iconWidget)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        self.titleLabel = QLabel(title)
        self.titleLabel.setStyleSheet(
            "color:#e8ffff;font-size:16px;font-weight:700;background:transparent;letter-spacing:0.6px;"
        )
        self.contentLabel = QLabel(content)
        self.contentLabel.setWordWrap(True)
        self.contentLabel.setStyleSheet(
            "color:#7ea8b0;font-size:12px;background:transparent;"
        )
        text_col.addWidget(self.titleLabel)
        text_col.addWidget(self.contentLabel)
        text_col.addStretch(1)
        root.addLayout(text_col, 1)

        self.actionButton = PrimaryPushButton(action_text, self)
        self.actionButton.setFixedWidth(128)
        self.actionButton.setFixedHeight(36)
        root.addWidget(self.actionButton, 0, Qt.AlignmentFlag.AlignVCenter)


class ActionRow(QWidget):
    def __init__(self, title: str, hint: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.titleLabel = BodyLabel(title, self)
        layout.addWidget(self.titleLabel)
        if hint:
            self.hintLabel = CaptionLabel(hint, self)
            self.hintLabel.setWordWrap(True)
            layout.addWidget(self.hintLabel)
        self.buttonRow = QHBoxLayout()
        self.buttonRow.setSpacing(10)
        layout.addLayout(self.buttonRow)

    def add_button(self, text: str, primary: bool = False) -> PushButton:
        button = PrimaryPushButton(text, self) if primary else PushButton(text, self)
        self.buttonRow.addWidget(button)
        return button
