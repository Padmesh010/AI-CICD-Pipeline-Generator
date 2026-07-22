from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QRect
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect

class AnimationHelper:
    """Utility class for smooth UI widget animations and transitions."""

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 250) -> QPropertyAnimation:
        """Fade in widget using QGraphicsOpacityEffect."""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        return anim

    @staticmethod
    def slide_down(widget: QWidget, start_y: int = -50, end_y: int = 20, duration: int = 300) -> QPropertyAnimation:
        """Slide down widget from top margin."""
        current_pos = widget.pos()
        widget.move(current_pos.x(), start_y)
        widget.show()

        anim = QPropertyAnimation(widget, b"pos", widget)
        anim.setDuration(duration)
        anim.setStartValue(QPoint(current_pos.x(), start_y))
        anim.setEndValue(QPoint(current_pos.x(), end_y))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        return anim
