from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from app.ui.theme import DesignTokens

class CommandPaletteModal(QDialog):
    """VS Code style Quick Command Palette Modal dialog triggered via Ctrl+K."""
    
    command_selected = Signal(str) # Emits command action key

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(550, 320)

        self.commands = [
            {"key": "nav_dashboard", "title": "Go to Dashboard", "category": "Navigation", "shortcut": "Alt+1"},
            {"key": "nav_wizard", "title": "Create New Pipeline (Wizard)", "category": "Navigation", "shortcut": "Alt+2"},
            {"key": "nav_editor", "title": "Open Pipeline Editor", "category": "Navigation", "shortcut": "Alt+3"},
            {"key": "nav_simulator", "title": "Open Pipeline Simulator", "category": "Navigation", "shortcut": "Alt+4"},
            {"key": "nav_templates", "title": "Browse Template Library", "category": "Navigation", "shortcut": "Alt+5"},
            {"key": "nav_settings", "title": "Open Settings", "category": "Navigation", "shortcut": "Alt+6"},
            {"key": "action_export", "title": "Export Pipeline & Infrastructure Assets", "category": "Action", "shortcut": "Ctrl+E"},
            {"key": "action_simulate", "title": "Start Pipeline Execution Simulation", "category": "Action", "shortcut": "Ctrl+R"},
            {"key": "toggle_theme", "title": "Toggle Dark / High-Contrast Theme", "category": "Theme", "shortcut": "Ctrl+T"},
        ]

        self.init_ui()

    def init_ui(self):
        container = QFrame(self)
        container.setObjectName("PaletteContainer")
        container.setStyleSheet(f"""
            QFrame#PaletteContainer {{
                background-color: {DesignTokens.DARK_BG_CARD};
                border: 1px solid {DesignTokens.ACCENT_BLUE};
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type a command or search view... (Esc to cancel)")
        self.search_input.textChanged.connect(self.filter_commands)
        layout.addWidget(self.search_input)

        # Commands List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-radius: 6px;
                color: {DesignTokens.TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {DesignTokens.DARK_BG_SURFACE};
                color: {DesignTokens.ACCENT_BLUE};
                font-weight: bold;
            }}
        """)
        self.list_widget.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self.list_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        self.populate_list(self.commands)

    def populate_list(self, items: list):
        self.list_widget.clear()
        for item in items:
            list_item = QListWidgetItem(f"[{item['category']}]  {item['title']}    ({item['shortcut']})")
            list_item.setData(Qt.UserRole, item["key"])
            self.list_widget.addItem(list_item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def filter_commands(self, text: str):
        if not text.strip():
            self.populate_list(self.commands)
            return

        query = text.lower()
        filtered = [
            c for c in self.commands 
            if query in c["title"].lower() or query in c["category"].lower() or query in c["key"].lower()
        ]
        self.populate_list(filtered)

    def _on_item_activated(self, item: QListWidgetItem):
        command_key = item.data(Qt.UserRole)
        self.command_selected.emit(command_key)
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            current_item = self.list_widget.currentItem()
            if current_item:
                self._on_item_activated(current_item)
        elif event.key() in (Qt.Key_Up, Qt.Key_Down):
            self.list_widget.keyPressEvent(event)
        else:
            super().keyPressEvent(event)
