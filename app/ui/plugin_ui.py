from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from app.plugins.plugin_manager import plugin_manager
from app.ui.theme import DesignTokens
from app.ui.components.toast_notification import ToastNotification
from app.core.logger import logger

class PluginManagerWidget(QWidget):
    """Interactive GUI panel for listing, enabling, disabling, and auditing developer plugins."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # Header Title
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        lbl_title = QLabel("DevOps Plugin Manager")
        lbl_title.setObjectName("HeaderLabel")
        lbl_sub = QLabel("Extend application capabilities with custom generators, security checkers, and export runners.")
        lbl_sub.setObjectName("SubHeaderLabel")
        title_layout.addWidget(lbl_title)
        title_layout.addWidget(lbl_sub)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        btn_refresh = QPushButton("🔄 Refresh Plugins")
        btn_refresh.clicked.connect(self.reload_plugins_list)
        header_layout.addWidget(btn_refresh)
        layout.addLayout(header_layout)

        # Splitter: List Table and Inspector Panel
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Plugin Table Card
        table_card = QFrame()
        table_card.setObjectName("CardWidget")
        table_card.setStyleSheet(f"QFrame#CardWidget {{ background-color: {DesignTokens.DARK_BG_CARD}; border: 1px solid {DesignTokens.DARK_BORDER}; border-radius: 8px; }}")
        table_layout = QVBoxLayout(table_card)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Plugin Name", "Type", "Author", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self.inspect_selected_plugin)
        table_layout.addWidget(self.table)
        splitter.addWidget(table_card)

        # Right panel: Inspector Panel Card
        inspect_card = QFrame()
        inspect_card.setObjectName("CardWidget")
        inspect_card.setStyleSheet(f"QFrame#CardWidget {{ background-color: {DesignTokens.DARK_BG_SURFACE}; border: 1px solid {DesignTokens.DARK_BORDER}; border-radius: 8px; }}")
        inspect_layout = QVBoxLayout(inspect_card)

        lbl_inspect_title = QLabel("Plugin Details & Manifest")
        lbl_inspect_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        inspect_layout.addWidget(lbl_inspect_title)

        self.txt_inspect = QTextEdit()
        self.txt_inspect.setReadOnly(True)
        self.txt_inspect.setStyleSheet("font-family: Consolas, monospace;")
        self.txt_inspect.setHtml("<p style='color: #8B949E;'>Select a plugin from the table to view manifest details.</p>")
        inspect_layout.addWidget(self.txt_inspect)

        # Toggle Active Status button
        self.btn_toggle = QPushButton("Toggle Active Status")
        self.btn_toggle.setEnabled(False)
        self.btn_toggle.clicked.connect(self.toggle_plugin_status)
        inspect_layout.addWidget(self.btn_toggle)

        splitter.addWidget(inspect_card)
        splitter.setSizes([600, 350])
        layout.addWidget(splitter)

        self.reload_plugins_list()

    def reload_plugins_list(self):
        plugin_manager.discover_plugins()
        plugins = plugin_manager.list_plugins()

        self.table.setRowCount(0)
        for p_name, p_info in plugins.items():
            meta = p_info["metadata"]
            row = self.table.rowCount()
            self.table.insertRow(row)

            item_name = QTableWidgetItem(meta.name)
            item_name.setData(Qt.UserRole, p_name)
            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(meta.plugin_type.value))
            self.table.setItem(row, 2, QTableWidgetItem(meta.author))
            
            status_str = "ACTIVE" if p_info["active"] else "DISABLED"
            self.table.setItem(row, 3, QTableWidgetItem(status_str))

    def inspect_selected_plugin(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.txt_inspect.clear()
            self.btn_toggle.setEnabled(False)
            return

        plugin_name = selected_items[0].data(Qt.UserRole)
        plugins = plugin_manager.list_plugins()
        if plugin_name in plugins:
            p_info = plugins[plugin_name]
            meta = p_info["metadata"]

            html = f"""
                <h3>{meta.name}</h3>
                <p><b>Version:</b> {meta.version}</p>
                <p><b>Author:</b> {meta.author}</p>
                <p><b>Type:</b> {meta.plugin_type.value}</p>
                <p><b>Compatibility:</b> {', '.join(meta.compatible_versions)}</p>
                <hr>
                <p><b>Description:</b><br>{meta.description}</p>
            """
            self.txt_inspect.setHtml(html)
            self.btn_toggle.setEnabled(True)

    def toggle_plugin_status(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        plugin_name = selected_items[0].data(Qt.UserRole)
        plugins = plugin_manager.list_plugins()
        if plugin_name in plugins:
            current_status = plugins[plugin_name]["active"]
            if current_status:
                plugin_manager.disable_plugin(plugin_name)
                ToastNotification.show_toast(self, f"Disabled plugin: {plugin_name}", "warning")
            else:
                plugin_manager.enable_plugin(plugin_name)
                ToastNotification.show_toast(self, f"Enabled plugin: {plugin_name}", "success")
            self.reload_plugins_list()
            self.inspect_selected_plugin()
