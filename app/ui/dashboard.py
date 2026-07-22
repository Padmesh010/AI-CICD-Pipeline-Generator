import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from app.database.db import db_manager
from app.core.logger import logger

from app.database.models import Project, Pipeline, AuditLog
from app.ui.theme import DesignTokens

class DashboardWidget(QWidget):
    # Signals to communicate tab changes to MainWindow
    navigate_to_tab = Signal(str) # "wizard", "editor", "analyzer", "settings", "templates"
    open_project_in_editor = Signal(int) # project_id

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header Title
        header_layout = QVBoxLayout()
        header_title = QLabel("AI CI/CD Operations Dashboard")
        header_title.setObjectName("HeaderLabel")
        
        current_time = datetime.datetime.now().strftime("%A, %b %d, %Y")
        header_sub = QLabel(f"DevOps Automation Platform | {current_time}")
        header_sub.setObjectName("SubHeaderLabel")
        
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_sub)
        layout.addLayout(header_layout)

        # Summary Stats Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        self.stat_pipelines = self._create_stat_card("Total Pipelines", "0")
        self.stat_simulations = self._create_stat_card("Successful Runs", "0")
        self.stat_projects = self._create_stat_card("Active Projects", "0")
        self.stat_savings = self._create_stat_card("Est. Monthly Savings", "$0.00")

        stats_layout.addWidget(self.stat_pipelines)
        stats_layout.addWidget(self.stat_simulations)
        stats_layout.addWidget(self.stat_projects)
        stats_layout.addWidget(self.stat_savings)
        layout.addLayout(stats_layout)

        # Quick Actions Grid
        actions_panel = QWidget()
        actions_panel.setObjectName("CardWidget")
        actions_layout = QVBoxLayout(actions_panel)
        
        actions_title = QLabel("Quick Launcher")
        actions_title.setObjectName("CardTitle")
        actions_layout.addWidget(actions_title)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        
        btn_wizard = QPushButton("🚀 Run Project Wizard")
        btn_wizard.setProperty("class", "primary")
        btn_wizard.clicked.connect(lambda: self.navigate_to_tab.emit("wizard"))
        
        btn_analyzer = QPushButton("🔍 Scan Local Repository")
        btn_analyzer.clicked.connect(lambda: self.navigate_to_tab.emit("analyzer"))
        
        btn_templates = QPushButton("📚 Explore Template Library")
        btn_templates.clicked.connect(lambda: self.navigate_to_tab.emit("templates"))
        
        btn_settings = QPushButton("⚙️ Connection Settings")
        btn_settings.clicked.connect(lambda: self.navigate_to_tab.emit("settings"))

        grid_layout.addWidget(btn_wizard, 0, 0)
        grid_layout.addWidget(btn_analyzer, 0, 1)
        grid_layout.addWidget(btn_templates, 1, 0)
        grid_layout.addWidget(btn_settings, 1, 1)
        actions_layout.addLayout(grid_layout)
        layout.addWidget(actions_panel)

        # Split section: Recent Projects & AI Suggestions
        split_layout = QHBoxLayout()
        split_layout.setSpacing(16)

        # Recent Projects Card
        projects_card = QWidget()
        projects_card.setObjectName("CardWidget")
        projects_layout = QVBoxLayout(projects_card)
        
        projects_title = QLabel("Recent Projects")
        projects_title.setObjectName("CardTitle")
        projects_layout.addWidget(projects_title)

        self.projects_list = QListWidget()
        self.projects_list.itemDoubleClicked.connect(self._on_project_double_clicked)
        projects_layout.addWidget(self.projects_list)
        split_layout.addWidget(projects_card, 1)

        # AI Suggestions Card
        suggestions_card = QWidget()
        suggestions_card.setObjectName("CardWidget")
        suggestions_layout = QVBoxLayout(suggestions_card)
        
        suggestions_title = QLabel("DevOps Recommendations")
        suggestions_title.setObjectName("CardTitle")
        suggestions_layout.addWidget(suggestions_title)

        sug_text = QLabel(
            "💡 <b>Security Audit</b>: Avoid using raw password arguments inside Jenkinsfiles. Inject them via secrets wrappers.\n\n"
            "💡 <b>Docker Size</b>: Multi-stage python builds reduced container image sizes from 850MB to 125MB.\n\n"
            "💡 <b>Cloud Costs</b>: Enabling dependency caching saves up to 45% workflow execution time."
        )
        sug_text.setWordWrap(True)
        sug_text.setStyleSheet("line-height: 1.4;")
        suggestions_layout.addWidget(sug_text)
        suggestions_layout.addStretch()
        split_layout.addWidget(suggestions_card, 1)

        layout.addLayout(split_layout)
        layout.setStretch(3, 1)

        self.refresh_data()

    def _create_stat_card(self, title, val):
        card = QWidget()
        card.setObjectName("CardWidget")
        card.setStyleSheet(f"background-color: {DesignTokens.DARK_BG_CARD}; border: 1px solid {DesignTokens.DARK_BORDER}; border-radius: 8px;")
        clayout = QVBoxLayout(card)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 11px; color: {DesignTokens.TEXT_SECONDARY};")
        
        lbl_val = QLabel(val)
        lbl_val.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {DesignTokens.ACCENT_BLUE};")
        
        clayout.addWidget(lbl_title)
        clayout.addWidget(lbl_val)
        return card

    def refresh_data(self):
        """Reload project counters and listings via SQLAlchemy ORM."""
        try:
            with db_manager.get_session() as session:
                proj_count = session.query(Project).count()
                pipe_count = session.query(Pipeline).count()
                sim_count = session.query(AuditLog).filter(AuditLog.status == "SUCCESS").count()

                self.stat_projects.layout().itemAt(1).widget().setText(str(proj_count))
                self.stat_pipelines.layout().itemAt(1).widget().setText(str(pipe_count))
                self.stat_simulations.layout().itemAt(1).widget().setText(str(sim_count))

                savings = proj_count * 45.50
                self.stat_savings.layout().itemAt(1).widget().setText(f"${savings:.2f}")

                # Populate recent projects
                self.projects_list.clear()
                recent_projects = session.query(Project).order_by(Project.created_at.desc()).limit(10).all()
                for proj in recent_projects:
                    item = QListWidgetItem(f"📁  {proj.name} ({proj.language} / {proj.framework})")
                    item.setData(Qt.UserRole, proj.id)
                    self.projects_list.addItem(item)
        except Exception as e:
            logger.error(f"Error loading dashboard statistics: {e}")

    def _on_project_double_clicked(self, item):
        pid = item.data(Qt.UserRole)
        if pid:
            self.open_project_in_editor.emit(pid)
