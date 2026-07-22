import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QTextEdit, QLabel
from app.ui.theme import DesignTokens

class LogViewerWidget(QWidget):
    """Real-time log viewer widget for monitoring application, AI, and generation log files."""

    def __init__(self, log_dir: str = "", parent=None):
        super().__init__(parent)
        if not log_dir:
            self.log_dir = os.path.join(
                os.path.expanduser("~"), ".gemini", "antigravity", "ai_cicd_pipeline_generator", "logs"
            )
        else:
            self.log_dir = log_dir

        self.layout = QVBoxLayout(self)

        # Top Controls
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Select Log Stream:"))
        self.log_selector = QComboBox()
        self.log_selector.addItems(["app.log", "error.log", "ai.log", "generation.log"])
        self.log_selector.currentTextChanged.connect(self.refresh_logs)
        top_layout.addWidget(self.log_selector)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_logs)
        top_layout.addWidget(self.btn_refresh)

        self.btn_clear = QPushButton("Clear Output")
        self.btn_clear.clicked.connect(self.clear_logs)
        top_layout.addWidget(self.btn_clear)
        top_layout.addStretch()

        self.layout.addLayout(top_layout)

        # Text Area
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.layout.addWidget(self.log_display)

        self.refresh_logs()

    def refresh_logs(self):
        log_file = self.log_selector.currentText()
        log_path = os.path.join(self.log_dir, log_file)
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.log_display.setPlainText(content[-20000:])
            except Exception as e:
                self.log_display.setPlainText(f"Error reading log file: {e}")
        else:
            self.log_display.setPlainText(f"Log file '{log_file}' does not exist yet.")

    def clear_logs(self):
        self.log_display.clear()
