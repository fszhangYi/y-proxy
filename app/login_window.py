from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QTimer,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CheckBox,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PasswordLineEdit,
    PrimaryPushButton,
)

from .config import AppSettings
from .fx import SciFiBackdrop, center_on_screen
from .services.os_info import detect_os


class CapabilityTag(QFrame):
    """Pill tag styled only via QSS — no QGraphicsEffect (avoids painter conflicts)."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("capabilityTag")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        self._label = QLabel(text)
        self._label.setObjectName("capabilityTagLabel")
        layout.addWidget(self._label)
        self._apply_style(False)

    def _apply_style(self, hovered: bool = False) -> None:
        if hovered:
            self.setStyleSheet(
                """
                #capabilityTag {
                    background: rgba(45, 226, 230, 0.16);
                    border: 1px solid rgba(45, 226, 230, 0.65);
                    border-radius: 15px;
                }
                #capabilityTagLabel {
                    color: #eaffff;
                    font-size: 12px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                    background: transparent;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                #capabilityTag {
                    background: rgba(8, 24, 34, 0.55);
                    border: 1px solid rgba(45, 226, 230, 0.28);
                    border-radius: 15px;
                }
                #capabilityTagLabel {
                    color: rgba(210, 245, 248, 0.9);
                    font-size: 12px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                    background: transparent;
                }
                """
            )

    def enterEvent(self, event) -> None:  # noqa: N802
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._apply_style(False)
        super().leaveEvent(event)


class LoginWindow(QWidget):
    logged_in = pyqtSignal(str)

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.os = detect_os()
        self.setObjectName("loginWindow")
        self.setWindowTitle("Y-Proxy 登录")
        self.setFixedSize(1040, 640)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        self._animations: list[QPropertyAnimation] = []
        self._build_ui()
        self._load_remembered()
        center_on_screen(self)
        QTimer.singleShot(40, self._play_enter_animation)

    def _build_ui(self) -> None:
        self.backdrop = SciFiBackdrop(self)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        brand = QWidget(self)
        brand.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(52, 58, 28, 40)
        brand_layout.setSpacing(0)
        brand_layout.addStretch(2)

        eyebrow = QLabel("SECURE LAN EGRESS")
        eyebrow.setObjectName("eyebrow")
        brand_layout.addWidget(eyebrow)
        brand_layout.addSpacing(10)

        self.brandTitle = QLabel("Y-Proxy")
        self.brandTitle.setObjectName("heroBrand")
        font = QFont("Segoe UI Semibold", 56)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.8)
        self.brandTitle.setFont(font)
        brand_layout.addWidget(self.brandTitle)

        self.brandTagline = QLabel("把已联网机器的出口，交给同网段的入网端。")
        self.brandTagline.setObjectName("heroTagline")
        self.brandTagline.setWordWrap(True)
        brand_layout.addSpacing(12)
        brand_layout.addWidget(self.brandTagline)

        brand_layout.addSpacing(30)
        tags = QHBoxLayout()
        tags.setSpacing(10)
        self.tags: list[CapabilityTag] = []
        for text in ("出站共享", "入网代理", "跨平台", self.os.display):
            tag = CapabilityTag(text, brand)
            self.tags.append(tag)
            tags.addWidget(tag, 0, Qt.AlignmentFlag.AlignLeft)
        tags.addStretch(1)
        brand_layout.addLayout(tags)
        brand_layout.addStretch(3)

        self.osHint = QLabel(f"SYSTEM DETECTED  ·  {self.os.display.upper()}")
        self.osHint.setObjectName("osHint")
        brand_layout.addWidget(self.osHint)
        root.addWidget(brand, 5)

        form_wrap = QWidget(self)
        form_wrap.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        form_layout = QVBoxLayout(form_wrap)
        form_layout.setContentsMargins(24, 48, 48, 48)
        form_layout.addStretch(1)

        self.cardHost = QWidget(form_wrap)
        self.cardHost.setFixedWidth(400)
        host_layout = QVBoxLayout(self.cardHost)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setSpacing(0)

        # Fake soft shadow plate (no QGraphicsEffect — Fluent paint + effects spam console).
        self.shadowPlate = QFrame(self.cardHost)
        self.shadowPlate.setObjectName("shadowPlate")
        self.shadowPlate.setFixedHeight(8)

        self.loginCard = QFrame(self.cardHost)
        self.loginCard.setObjectName("loginCard")

        card = QVBoxLayout(self.loginCard)
        card.setContentsMargins(30, 28, 30, 28)
        card.setSpacing(12)

        card_title = QLabel("身份验证")
        card_title.setObjectName("cardTitle")
        card_sub = QLabel("登录后选择出站端或入网端")
        card_sub.setObjectName("cardSub")
        card.addWidget(card_title)
        card.addWidget(card_sub)
        card.addSpacing(8)

        user_label = QLabel("用户名")
        user_label.setObjectName("fieldLabel")
        card.addWidget(user_label)
        self.userEdit = LineEdit(self.loginCard)
        self.userEdit.setPlaceholderText("admin")
        self.userEdit.setClearButtonEnabled(True)
        self.userEdit.setFixedHeight(40)
        card.addWidget(self.userEdit)

        pass_label = QLabel("密码")
        pass_label.setObjectName("fieldLabel")
        card.addWidget(pass_label)
        self.passEdit = PasswordLineEdit(self.loginCard)
        self.passEdit.setPlaceholderText("••••••••")
        self.passEdit.setFixedHeight(40)
        card.addWidget(self.passEdit)

        self.rememberBox = CheckBox("记住用户名", self.loginCard)
        card.addWidget(self.rememberBox)
        card.addSpacing(4)

        self.loginButton = PrimaryPushButton(FluentIcon.ACCEPT, "进入系统", self.loginCard)
        self.loginButton.setObjectName("loginButton")
        self.loginButton.setFixedHeight(42)
        self.loginButton.clicked.connect(self._on_login)
        card.addWidget(self.loginButton)

        tip = QLabel("演示账户  admin / admin")
        tip.setObjectName("demoTip")
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.addWidget(tip)

        host_layout.addWidget(self.loginCard)
        host_layout.addWidget(self.shadowPlate)
        form_layout.addWidget(self.cardHost, 0, Qt.AlignmentFlag.AlignHCenter)
        form_layout.addStretch(2)
        root.addWidget(form_wrap, 4)

        self.setStyleSheet(
            """
            #loginWindow { background: #143044; }
            #eyebrow {
                color: rgba(45, 226, 230, 0.72);
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 2.5px;
                background: transparent;
            }
            #heroBrand {
                color: #f2ffff;
                background: transparent;
            }
            #heroTagline {
                color: rgba(190, 230, 235, 0.78);
                font-size: 15px;
                line-height: 1.45;
                background: transparent;
                max-width: 380px;
            }
            #osHint {
                color: rgba(125, 190, 200, 0.48);
                font-size: 11px;
                letter-spacing: 1.4px;
                background: transparent;
            }
            #loginCard {
                background: rgba(22, 52, 70, 0.92);
                border: 1px solid rgba(45, 226, 230, 0.32);
                border-radius: 18px;
            }
            #shadowPlate {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 0, 0, 90),
                    stop:1 rgba(0, 0, 0, 0)
                );
                border: none;
                margin: 0px 18px;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
            #cardTitle {
                color: #e8ffff;
                font-size: 22px;
                font-weight: 700;
                background: transparent;
            }
            #cardSub {
                color: rgba(150, 195, 205, 0.75);
                font-size: 12px;
                background: transparent;
            }
            #fieldLabel {
                color: rgba(160, 210, 220, 0.7);
                font-size: 11px;
                letter-spacing: 0.8px;
                background: transparent;
            }
            #demoTip {
                color: rgba(125, 170, 180, 0.55);
                font-size: 11px;
                background: transparent;
                margin-top: 4px;
            }
            LineEdit, PasswordLineEdit {
                background: rgba(5, 16, 24, 0.9);
                border: 1px solid rgba(45, 226, 230, 0.18);
                border-radius: 8px;
                color: #d7f6f8;
                padding-left: 10px;
            }
            """
        )

        self.passEdit.returnPressed.connect(self._on_login)
        self.userEdit.returnPressed.connect(self.passEdit.setFocus)

        # Staggered reveal without QGraphicsOpacityEffect (effects + Fluent = painter spam).
        self._reveal = [eyebrow, self.brandTitle, self.brandTagline, *self.tags, self.osHint]
        for widget in self._reveal:
            widget.hide()
        self.cardHost.hide()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.backdrop.setGeometry(self.rect())
        self.backdrop.lower()

    def _play_enter_animation(self) -> None:
        delay = 0
        for widget in self._reveal:
            QTimer.singleShot(delay, widget.show)
            delay += 55

        def show_card() -> None:
            self.cardHost.show()
            end = self.cardHost.pos()
            start = end + QPoint(24, 12)
            self.cardHost.move(start)
            slide = QPropertyAnimation(self.cardHost, b"pos", self)
            slide.setDuration(480)
            slide.setStartValue(start)
            slide.setEndValue(end)
            slide.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._animations.append(slide)
            slide.start()

        QTimer.singleShot(delay + 40, show_card)

    def _load_remembered(self) -> None:
        if self.settings.remember_user():
            self.rememberBox.setChecked(True)
            self.userEdit.setText(self.settings.saved_username())
            self.passEdit.setFocus()
        else:
            self.userEdit.setText(self.settings.saved_username())
            self.userEdit.setFocus()

    def _on_login(self) -> None:
        username = self.userEdit.text().strip()
        password = self.passEdit.text()
        if not username or not password:
            InfoBar.warning(
                title="请填写账户",
                content="用户名和密码不能为空",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self,
            )
            return
        if not self.settings.verify_login(username, password):
            InfoBar.error(
                title="登录失败",
                content="用户名或密码不正确",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            return
        self.settings.set_remember_user(self.rememberBox.isChecked())
        if self.rememberBox.isChecked():
            self.settings.set_saved_username(username)
        self.logged_in.emit(username)
