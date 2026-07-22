from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QSplitter, QPlainTextEdit, 
    QInputDialog, QMessageBox, QLineEdit, QComboBox, QDialog
)
from PySide6.QtCore import Qt, Signal
from app.database.db import db_manager
from app.database.models import Template, Project, Pipeline
from app.ui.theme import DesignTokens
from app.ui.components.toast_notification import ToastNotification
from app.core.logger import logger

class TemplatePreviewModal(QDialog):
    """Modal displaying full raw source code for a selected template blueprint."""
    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Blueprint Preview: {title}")
        self.resize(650, 450)
        layout = QVBoxLayout(self)

        txt_preview = QPlainTextEdit()
        txt_preview.setReadOnly(True)
        txt_preview.setPlainText(content)
        txt_preview.setStyleSheet(f"background-color: {DesignTokens.DARK_BG_CARD}; color: {DesignTokens.TEXT_PRIMARY}; font-family: Consolas, monospace;")
        layout.addWidget(txt_preview)

        btn_close = QPushButton("Close Preview")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

class TemplatesWidget(QWidget):
    template_applied = Signal(int)

    def __init__(self):
        super().__init__()
        self.all_templates = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # Header Title
        header_layout = QVBoxLayout()
        header_title = QLabel("DevOps Template Blueprint Library")
        header_title.setObjectName("HeaderLabel")
        header_sub = QLabel("Explore enterprise-grade blueprints for CI/CD, Docker, Kubernetes, Terraform, Helm, and Ansible.")
        header_sub.setObjectName("SubHeaderLabel")
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_sub)
        layout.addLayout(header_layout)

        # Filter Bar: Search & Category Dropdown
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search blueprints by platform, language, or keyword...")
        self.search_input.textChanged.connect(self._filter_templates)
        filter_layout.addWidget(self.search_input, 1)

        self.combo_category = QComboBox()
        self.combo_category.addItems(["All Platforms", "GitHub Actions", "GitLab CI", "Jenkins", "Docker", "Kubernetes", "Terraform", "Helm", "Ansible"])
        self.combo_category.currentTextChanged.connect(self._filter_templates)
        filter_layout.addWidget(self.combo_category)

        layout.addLayout(filter_layout)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: list of templates
        list_card = QWidget()
        list_card.setObjectName("CardWidget")
        list_layout = QVBoxLayout(list_card)
        
        list_title = QLabel("Available Blueprints")
        list_title.setObjectName("CardTitle")
        list_layout.addWidget(list_title)
        
        self.templates_list = QListWidget()
        self.templates_list.currentItemChanged.connect(self._on_template_selected)
        list_layout.addWidget(self.templates_list)
        
        splitter.addWidget(list_card)

        # Right panel: template preview and launch button
        preview_card = QWidget()
        preview_card.setObjectName("CardWidget")
        preview_layout = QVBoxLayout(preview_card)

        preview_header = QHBoxLayout()
        self.lbl_preview_title = QLabel("Preview Configuration")
        self.lbl_preview_title.setObjectName("CardTitle")
        preview_header.addWidget(self.lbl_preview_title)
        preview_header.addStretch()

        self.btn_apply = QPushButton("🚀 Use Blueprint")
        self.btn_apply.setProperty("class", "primary")
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        preview_header.addWidget(self.btn_apply)

        preview_layout.addLayout(preview_header)

        self.txt_preview = QPlainTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setStyleSheet(f"font-family: Consolas, monospace; background-color: {DesignTokens.DARK_BG_CARD}; color: {DesignTokens.TEXT_PRIMARY};")
        preview_layout.addWidget(self.txt_preview)

        splitter.addWidget(preview_card)
        splitter.setSizes([350, 650])
        layout.addWidget(splitter)

        self.load_templates()

    def refresh_templates(self):
        """Alias wrapper to match MainWindow page-switch loads."""
        self.load_templates()

    def load_templates(self):
        """Fetch template records via SQLAlchemy ORM session."""
        try:
            with db_manager.get_session() as session:
                templates = session.query(Template).all()
                self.all_templates = [
                    {
                        "id": t.id,
                        "name": t.name,
                        "platform": t.platform,
                        "language": t.language,
                        "framework": t.framework,
                        "content": t.content,
                        "version": getattr(t, "version", "1.0.0")
                    } for t in templates
                ]
            self._filter_templates()
        except Exception as e:
            logger.error(f"Error loading template library: {e}")

    def _filter_templates(self):
        query = self.search_input.text().lower().strip()
        category = self.combo_category.currentText()

        self.templates_list.clear()
        for t in self.all_templates:
            match_query = (not query) or (query in t["name"].lower() or query in t["platform"].lower() or query in t["language"].lower())
            match_category = (category == "All Platforms") or (category.lower() in t["platform"].lower())

            if match_query and match_category:
                item = QListWidgetItem(f"📦  {t['name']}  v{t['version']}  ({t['platform']})")
                item.setData(Qt.UserRole, t)
                self.templates_list.addItem(item)

        if self.templates_list.count() > 0:
            self.templates_list.setCurrentRow(0)

    def _on_template_selected(self, current, previous):
        if not current:
            self.txt_preview.clear()
            self.lbl_preview_title.setText("Preview Configuration")
            self.btn_apply.setEnabled(False)
            return

        t_data = current.data(Qt.UserRole)
        if t_data:
            self.lbl_preview_title.setText(f"Blueprint: {t_data['name']} ({t_data['platform']})")
            self.txt_preview.setPlainText(t_data["content"])
            self.btn_apply.setEnabled(True)

    def _on_apply_clicked(self):
        current = self.templates_list.currentItem()
        if not current:
            return

        t_data = current.data(Qt.UserRole)
        proj_name, ok = QInputDialog.getText(self, "New Project", "Enter project name for this blueprint:", text=f"{t_data['name']}_App")
        if ok and proj_name:
            try:
                with db_manager.get_session() as session:
                    project = Project(
                        name=proj_name,
                        language=t_data["language"],
                        framework=t_data["framework"],
                        target="Docker Container"
                    )
                    session.add(project)
                    session.flush()

                    pipeline = Pipeline(
                        project_id=project.id,
                        platform=t_data["platform"],
                        yaml_content=t_data["content"]
                    )
                    session.add(pipeline)
                    pid = project.id

                ToastNotification.show_toast(self, f"Project '{proj_name}' created from template!", "success")
                self.template_applied.emit(pid)
            except Exception as e:
                ToastNotification.show_toast(self, f"Could not create project: {e}", "danger")
