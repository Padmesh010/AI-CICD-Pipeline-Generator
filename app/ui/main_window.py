from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QLabel, QPushButton, QStackedWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor
from app.ui.style import DARK_THEME_QSS, LIGHT_THEME_QSS
from app.ui.dashboard import DashboardWidget
from app.ui.wizard import WizardWidget
from app.ui.editor import EditorWidget
from app.ui.simulator_widget import SimulatorWidget
from app.ui.settings import SettingsWidget
from app.ui.analyzer_widget import AnalyzerWidget
from app.ui.templates_widget import TemplatesWidget
from app.ui.components.status_bar import TaskStatusBar
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from app.ui.components.command_palette import CommandPaletteModal
from app.ui.components.toast_notification import ToastNotification
from app.core.config import config_manager
from app.core.logger import logger

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Windows Window Flags for custom borderless title bar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Handle dragging offset variables
        self.drag_position = QPoint()

        self.status_bar = TaskStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.init_ui()
        self.setup_shortcuts()
        self.apply_current_theme()

    def setup_shortcuts(self):
        """Register global keyboard shortcuts."""
        self.shortcut_palette = QShortcut(QKeySequence("Ctrl+K"), self)
        self.shortcut_palette.activated.connect(self.open_command_palette)

    def open_command_palette(self):
        palette = CommandPaletteModal(self)
        palette.command_selected.connect(self.execute_palette_command)
        # Center palette over main window
        p_x = self.x() + (self.width() - palette.width()) // 2
        p_y = self.y() + (self.height() - palette.height()) // 3
        palette.move(p_x, p_y)
        palette.exec()

    def execute_palette_command(self, cmd_key: str):
        if cmd_key == "nav_dashboard":
            self.switch_page(0)
        elif cmd_key == "nav_wizard":
            self.switch_page(1)
        elif cmd_key == "nav_editor":
            self.switch_page(2)
        elif cmd_key == "nav_simulator":
            self.switch_page(3)
        elif cmd_key == "nav_templates":
            self.switch_page(4)
        elif cmd_key == "nav_settings":
            self.switch_page(5)
        elif cmd_key == "action_export":
            self.switch_page(2)
            ToastNotification.show_toast(self, "Switched to Editor for asset export.", "info")
        elif cmd_key == "action_simulate":
            self.switch_page(3)
            self.simulator_widget._on_run_clicked()
        elif cmd_key == "toggle_theme":
            ToastNotification.show_toast(self, "Theme settings refreshed.", "success")

    def init_ui(self):
        self.resize(1100, 750)
        self.setMinimumSize(950, 600)

        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main Layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Custom Title Bar
        self.setup_title_bar()

        # Content Area (Sidebar + Workspace)
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # 2. Sidebar Navigation
        self.setup_sidebar()

        # 3. Pages Workspace (QStackedWidget)
        self.pages = QStackedWidget()
        self.pages.setObjectName("WorkspaceWidget")
        
        # Instantiate widgets
        self.dashboard_widget = DashboardWidget()
        self.wizard_widget = WizardWidget()
        self.editor_widget = EditorWidget()
        self.simulator_widget = SimulatorWidget()
        self.analyzer_widget = AnalyzerWidget()
        self.templates_widget = TemplatesWidget()
        self.settings_widget = SettingsWidget()

        # Add to pages stacked widget
        self.pages.addWidget(self.dashboard_widget)
        self.pages.addWidget(self.wizard_widget)
        self.pages.addWidget(self.editor_widget)
        self.pages.addWidget(self.simulator_widget)
        self.pages.addWidget(self.analyzer_widget)
        self.pages.addWidget(self.templates_widget)
        self.pages.addWidget(self.settings_widget)

        self.content_layout.addWidget(self.pages, 1)
        self.main_layout.addLayout(self.content_layout)

        # 4. Floating Notification Banner Setup
        self.setup_notification_banner()

        # Connect signals between panels
        self._connect_signals()

    def setup_title_bar(self):
        title_bar = QWidget()
        title_bar.setObjectName("TitleBarWidget")
        title_bar.setFixedHeight(40)
        
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(15, 0, 15, 0)
        tb_layout.setSpacing(10)

        lbl_icon = QLabel("🛠️")
        lbl_title = QLabel("AI CI/CD Pipeline Generator")
        lbl_title.setObjectName("TitleLabel")

        tb_layout.addWidget(lbl_icon)
        tb_layout.addWidget(lbl_title)
        tb_layout.addStretch()

        btn_min = QPushButton("—")
        btn_min.setObjectName("TitleButton")
        btn_min.clicked.connect(self.showMinimized)

        btn_max = QPushButton("🗖")
        btn_max.setObjectName("TitleButton")
        btn_max.clicked.connect(self._toggle_maximize)

        btn_close = QPushButton("✕")
        btn_close.setObjectName("TitleButton")
        btn_close.setObjectName("TitleButtonClose")
        btn_close.clicked.connect(self.close)

        tb_layout.addWidget(btn_min)
        tb_layout.addWidget(btn_max)
        tb_layout.addWidget(btn_close)

        self.main_layout.addWidget(title_bar)

        # Track movements on titlebar double click or drag
        title_bar.mousePressEvent = self._title_bar_press
        title_bar.mouseMoveEvent = self._title_bar_move
        title_bar.mouseDoubleClickEvent = self._title_bar_double_click

    def setup_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setObjectName("SidebarWidget")
        self.sidebar.setFixedWidth(200)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 15, 0, 15)
        sidebar_layout.setSpacing(4)

        # Navigation items
        self.nav_buttons = []
        
        menu_items = [
            ("📊 Dashboard", 0),
            ("🚀 Project Wizard", 1),
            ("📝 Workspace Editor", 2),
            ("⚡ Pipeline Simulator", 3),
            ("🔍 Local Repo Scan", 4),
            ("📚 Template Library", 5),
            ("⚙️ Preferences", 6)
        ]

        for text, index in menu_items:
            btn = QPushButton(text)
            btn.setObjectName("SidebarButton")
            btn.setProperty("active", False)
            btn.clicked.connect(lambda checked=False, idx=index: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()
        
        # Set active color first page
        self.nav_buttons[0].setProperty("active", True)
        self.content_layout.addWidget(self.sidebar)

    def setup_notification_banner(self):
        """Build overlay notification banner."""
        self.notification_bar = QWidget(self)
        self.notification_bar.setObjectName("CardWidget")
        self.notification_bar.setStyleSheet("""
            QWidget#CardWidget {
                background-color: #1e293b;
                border: 1px solid #38bdf8;
                border-radius: 8px;
            }
        """)
        
        nb_layout = QHBoxLayout(self.notification_bar)
        nb_layout.setContentsMargins(15, 10, 15, 10)
        
        self.lbl_notif_text = QLabel("Deployment pipeline assets generated successfully!")
        self.lbl_notif_text.setStyleSheet("font-weight: bold; color: #f8fafc;")
        nb_layout.addWidget(self.lbl_notif_text)
        
        self.notification_bar.setGeometry(300, -60, 500, 45)
        self.notification_bar.hide()
        
        # Add subtle drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        self.notification_bar.setGraphicsEffect(shadow)

    def _connect_signals(self):
        # Dashboard page navigation
        self.dashboard_widget.navigate_to_tab.connect(self._navigate_by_name)
        self.dashboard_widget.open_project_in_editor.connect(self._open_project)

        # Wizard completion
        self.wizard_widget.generation_completed.connect(self._on_wizard_completed)

        # Analyzer completion
        self.analyzer_widget.generation_completed.connect(self._on_wizard_completed)

        # Templates completion
        self.templates_widget.template_applied.connect(self._open_project)

        # Settings theme changed
        self.settings_widget.theme_changed.connect(self.switch_theme)

        # Editor simulation launch
        self.editor_widget.trigger_simulation.connect(self._on_run_simulation)

    def switch_page(self, index):
        """Change current layout index and repaint side highlight border."""
        self.pages.setCurrentIndex(index)
        
        for idx, btn in enumerate(self.nav_buttons):
            is_active = (idx == index)
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Refresh dashboard list when navigated back
        if index == 0:
            self.dashboard_widget.refresh_data()
        elif index == 5:
            self.templates_widget.refresh_templates()

    def _navigate_by_name(self, name):
        mapping = {
            "wizard": 1,
            "editor": 2,
            "simulator": 3,
            "analyzer": 4,
            "templates": 5,
            "settings": 6
        }
        idx = mapping.get(name, 0)
        self.switch_page(idx)

    def _open_project(self, project_id):
        self.editor_widget.load_project(project_id)
        self.switch_page(2) # Switch to Editor

    def _on_wizard_completed(self, project_id):
        self.show_notification("🚀 Deployment pipeline assets generated successfully!")
        self._open_project(project_id)

    def _on_run_simulation(self, platform, stages):
        self.simulator_widget.setup_timeline(platform, stages)
        self.switch_page(3) # Switch to Simulator page
        self.simulator_widget._on_run_clicked() # Auto-run

    def show_notification(self, text):
        """Slide down notification overlay."""
        self.lbl_notif_text.setText(text)
        
        # Center horizontally
        x = (self.width() - self.notification_bar.width()) // 2
        self.notification_bar.move(x, 15)
        self.notification_bar.show()
        self.notification_bar.raise_()

        # Simple timer to auto hide after 3 seconds
        from PySide6.QtCore import QTimer
        QTimer.singleShot(3500, self.notification_bar.hide)

    def apply_current_theme(self):
        theme = config_manager.get("theme", "Dark")
        self.switch_theme(theme)

    def switch_theme(self, theme):
        """Repaint application styles."""
        if theme == "Dark":
            self.setStyleSheet(DARK_THEME_QSS)
            logger.info("Applied Dark QSS template.")
        else:
            self.setStyleSheet(LIGHT_THEME_QSS)
            logger.info("Applied Light QSS template.")

    # Custom Window Controls & Dragging handlers
    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _title_bar_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def _title_bar_move(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def _title_bar_double_click(self, event):
        if event.button() == Qt.LeftButton:
            self._toggle_maximize()
            event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-center notification bar if open
        if self.notification_bar.isVisible():
            x = (self.width() - self.notification_bar.width()) // 2
            self.notification_bar.move(x, 15)
