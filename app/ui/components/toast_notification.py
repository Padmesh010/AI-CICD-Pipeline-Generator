from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer
from app.ui.theme import DesignTokens
from app.ui.components.animation_helper import AnimationHelper

class ToastNotification(QFrame):
    """Non-blocking popup toast notification widget."""

    def __init__(self, message: str, toast_type: str = "info", duration_ms: int = 3500, parent=None):
        super().__init__(parent)
        self.toast_type = toast_type
        self.duration_ms = duration_ms
        self.init_ui(message)

    def init_ui(self, message: str):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        # Icon prefix
        icon = "ℹ️"
        border_color = DesignTokens.ACCENT_BLUE
        if self.toast_type == "success":
            icon = "✅"
            border_color = DesignTokens.ACCENT_GREEN
        elif self.toast_type == "warning":
            icon = "⚠️"
            border_color = DesignTokens.ACCENT_AMBER
        elif self.toast_type == "danger" or self.toast_type == "error":
            icon = "❌"
            border_color = DesignTokens.ACCENT_RED

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {DesignTokens.DARK_BG_CARD};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)

        lbl_icon = QLabel(icon)
        layout.addWidget(lbl_icon)

        lbl_msg = QLabel(message)
        lbl_msg.setStyleSheet(f"color: {DesignTokens.TEXT_PRIMARY}; font-weight: 500; font-size: 12px;")
        layout.addWidget(lbl_msg, 1)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(18, 18)
        btn_close.setStyleSheet("QPushButton { border: none; background: transparent; color: #8B949E; } QPushButton:hover { color: #FFFFFF; }")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        QTimer.singleShot(self.duration_ms, self.close)

    @classmethod
    def show_toast(cls, parent_widget, message: str, toast_type: str = "info"):
        toast = cls(message, toast_type, parent=parent_widget)
        toast.adjustSize()
        x = parent_widget.width() - toast.width() - 25
        y = 25
        toast.move(x, y)
        toast.show()
        toast.raise_()
        AnimationHelper.fade_in(toast, 200)
        return toast
