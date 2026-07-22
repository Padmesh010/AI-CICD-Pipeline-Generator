from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QComboBox, QSlider, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from app.services.ai_service import ai_service
from app.core.config import config_manager
from app.core.thread_worker import WorkerThread
from app.ui.theme import DesignTokens
from app.ui.components.toast_notification import ToastNotification

class AIAssistantWidget(QWidget):
    """Enterprise AI Assistant Dock panel with quick prompt actions, model switching, and chat history."""

    code_generated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header Title & Provider Selector
        header_card = QFrame()
        header_card.setObjectName("CardWidget")
        header_card.setStyleSheet(f"QFrame#CardWidget {{ background-color: {DesignTokens.DARK_BG_SURFACE}; border: 1px solid {DesignTokens.DARK_BORDER}; border-radius: 8px; padding: 6px; }}")
        h_layout = QVBoxLayout(header_card)

        lbl_title = QLabel("🤖 AI DevOps Assistant")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 13px;")
        h_layout.addWidget(lbl_title)

        p_layout = QHBoxLayout()
        p_layout.addWidget(QLabel("Provider:"))
        self.combo_provider = QComboBox()
        self.combo_provider.addItems([
            "Mock Mode (Offline)", "OpenAI", "Ollama (Offline)", 
            "Azure OpenAI", "Anthropic", "Google Gemini"
        ])
        current_provider = config_manager.get("ai_provider", "Mock Mode (Offline)")
        idx = self.combo_provider.findText(current_provider)
        if idx >= 0:
            self.combo_provider.setCurrentIndex(idx)
        self.combo_provider.currentTextChanged.connect(self._on_provider_changed)
        p_layout.addWidget(self.combo_provider, 1)
        h_layout.addLayout(p_layout)

        layout.addWidget(header_card)

        # Quick Action Buttons
        quick_layout = QHBoxLayout()
        self.btn_explain = QPushButton("🔍 Explain")
        self.btn_explain.clicked.connect(lambda: self.trigger_quick_action("explain"))
        quick_layout.addWidget(self.btn_explain)

        self.btn_optimize = QPushButton("⚡ Optimize")
        self.btn_optimize.clicked.connect(lambda: self.trigger_quick_action("optimize"))
        quick_layout.addWidget(self.btn_optimize)

        self.btn_security = QPushButton("🛡️ Audit")
        self.btn_security.clicked.connect(lambda: self.trigger_quick_action("security"))
        quick_layout.addWidget(self.btn_security)

        layout.addLayout(quick_layout)

        # Chat Stream Area
        self.txt_chat = QTextEdit()
        self.txt_chat.setReadOnly(True)
        self.txt_chat.setFont(QFont("Segoe UI", 10))
        self.txt_chat.setHtml("<p style='color: #8B949E;'><i>AI Assistant initialized. Type a prompt or use quick action buttons...</i></p>")
        layout.addWidget(self.txt_chat, 1)

        # Input Prompt Bar
        input_layout = QHBoxLayout()
        self.input_prompt = QLineEdit()
        self.input_prompt.setPlaceholderText("Ask AI to generate, refactor, or explain code...")
        self.input_prompt.returnPressed.connect(self.send_user_prompt)
        input_layout.addWidget(self.input_prompt, 1)

        self.btn_send = QPushButton("Send ↵")
        self.btn_send.setProperty("class", "primary")
        self.btn_send.clicked.connect(self.send_user_prompt)
        input_layout.addWidget(self.btn_send)

        layout.addLayout(input_layout)

    def _on_provider_changed(self, provider_name: str):
        config_manager.set("ai_provider", provider_name)
        ToastNotification.show_toast(self, f"AI Provider switched to '{provider_name}'", "info")

    def append_chat(self, sender: str, text: str):
        color = DesignTokens.ACCENT_BLUE if sender == "User" else DesignTokens.ACCENT_GREEN
        formatted = f"<p><b style='color: {color};'>{sender}:</b> {text.replace('\n', '<br>')}</p>"
        self.txt_chat.append(formatted)

    def send_user_prompt(self):
        prompt = self.input_prompt.text().strip()
        if not prompt:
            return

        self.append_chat("User", prompt)
        self.input_prompt.clear()
        self.btn_send.setEnabled(False)

        # Execute off-thread via WorkerThread
        self.worker = WorkerThread(
            ai_service.explain_stage, 
            "General Code", 
            prompt, 
            task_name="AI Completion",
            task_description=f"Prompt: {prompt[:30]}..."
        )
        self.worker.finished_result.connect(self._on_ai_success)
        self.worker.error.connect(self._on_ai_error)
        self.worker.start()

    def trigger_quick_action(self, action_type: str):
        if action_type == "explain":
            prompt = "Explain current pipeline architecture and security scanning steps."
        elif action_type == "optimize":
            prompt = "Optimize build duration and inject package manager caching."
        elif action_type == "security":
            prompt = "Audit pipeline code for unpinned tags and hardcoded secrets."
        else:
            prompt = "Generate container configuration snippet."

        self.input_prompt.setText(prompt)
        self.send_user_prompt()

    def _on_ai_success(self, response_text: str):
        self.btn_send.setEnabled(True)
        self.append_chat("AI Assistant", response_text)

    def _on_ai_error(self, exc: Exception, err_msg: str):
        self.btn_send.setEnabled(True)
        self.append_chat("AI Assistant", f"<span style='color: {DesignTokens.ACCENT_RED};'>Error: {err_msg}</span>")
