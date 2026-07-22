from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QFormLayout, QFileDialog, QMessageBox, QSlider, QFrame
)
from PySide6.QtCore import Qt, Signal
from app.core.config import config_manager
from app.database.db import db_manager
from app.services.ai_service import ai_service
from app.ui.theme import DesignTokens
from app.ui.components.toast_notification import ToastNotification
from app.core.logger import logger

class SettingsWidget(QWidget):
    theme_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # Header Title
        header_layout = QVBoxLayout()
        header_title = QLabel("Application Preferences & AI Settings")
        header_title.setObjectName("HeaderLabel")
        header_sub = QLabel("Configure LLM model providers, API credentials, backup storage, and system themes.")
        header_sub.setObjectName("SubHeaderLabel")
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_sub)
        layout.addLayout(header_layout)

        # Settings Form Card
        card = QWidget()
        card.setObjectName("CardWidget")
        flayout = QFormLayout(card)
        flayout.setSpacing(15)

        # AI Provider Selection
        self.combo_provider = QComboBox()
        self.combo_provider.addItems([
            "Mock Mode (Offline)", "OpenAI", "Ollama (Offline)", 
            "Azure OpenAI", "Anthropic", "Google Gemini"
        ])
        curr_provider = config_manager.get("ai_provider", "Mock Mode (Offline)")
        idx = self.combo_provider.findText(curr_provider)
        if idx >= 0:
            self.combo_provider.setCurrentIndex(idx)
        flayout.addRow("AI Model Provider:", self.combo_provider)

        # API Key
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setEchoMode(QLineEdit.Password)
        self.txt_api_key.setText(config_manager.get("api_key", ""))
        self.txt_api_key.setPlaceholderText("Enter provider API Key...")
        flayout.addRow("Provider API Key:", self.txt_api_key)

        # Ollama Endpoint
        self.txt_ollama_url = QLineEdit()
        self.txt_ollama_url.setText(config_manager.get("ollama_url", "http://localhost:11434"))
        self.txt_ollama_url.setPlaceholderText("e.g. http://localhost:11434")
        flayout.addRow("Ollama Endpoint URL:", self.txt_ollama_url)

        # Temperature Slider
        temp_layout = QHBoxLayout()
        self.slider_temp = QSlider(Qt.Horizontal)
        self.slider_temp.setRange(0, 100)
        self.slider_temp.setValue(20) # 0.2
        self.lbl_temp_val = QLabel("0.20 (Focused)")
        self.slider_temp.valueChanged.connect(self._on_temp_changed)
        temp_layout.addWidget(self.slider_temp, 1)
        temp_layout.addWidget(self.lbl_temp_val)
        flayout.addRow("AI Creativity (Temp):", temp_layout)

        # Connection Test Button
        btn_test = QPushButton("⚡ Test AI Connection")
        btn_test.clicked.connect(self.test_ai_connection)
        flayout.addRow("", btn_test)

        layout.addWidget(card)

        # Database Maintenance Card
        db_card = QWidget()
        db_card.setObjectName("CardWidget")
        db_layout = QVBoxLayout(db_card)

        db_title = QLabel("Database Maintenance & Backups")
        db_title.setObjectName("CardTitle")
        db_layout.addWidget(db_title)

        db_btn_layout = QHBoxLayout()
        btn_backup = QPushButton("💾 Backup Database Now")
        btn_backup.clicked.connect(self.backup_database)
        db_btn_layout.addWidget(btn_backup)
        db_btn_layout.addStretch()
        db_layout.addLayout(db_btn_layout)

        layout.addWidget(db_card)

        # Action bar
        action_layout = QHBoxLayout()
        btn_save = QPushButton("Save Preferences")
        btn_save.setProperty("class", "primary")
        btn_save.clicked.connect(self.save_settings)
        action_layout.addWidget(btn_save)
        action_layout.addStretch()

        layout.addLayout(action_layout)
        layout.addStretch()

    def _on_temp_changed(self, val: int):
        float_val = val / 100.0
        self.lbl_temp_val.setText(f"{float_val:.2f}")

    def test_ai_connection(self):
        try:
            res = ai_service.explain_stage("Connection Test", "test_code = True")
            ToastNotification.show_toast(self, "AI Provider Connection Successful!", "success")
        except Exception as e:
            ToastNotification.show_toast(self, f"Connection Failed: {e}", "danger")

    def backup_database(self):
        try:
            backup_path = db_manager.backup_database()
            ToastNotification.show_toast(self, f"Database backup saved: {backup_path}", "success")
        except Exception as e:
            ToastNotification.show_toast(self, f"Backup Failed: {e}", "danger")

    def save_settings(self):
        config_manager.set("ai_provider", self.combo_provider.currentText())
        config_manager.set("api_key", self.txt_api_key.text().strip())
        config_manager.set("ollama_url", self.txt_ollama_url.text().strip())
        ToastNotification.show_toast(self, "Preferences saved successfully!", "success")
