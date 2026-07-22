import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QCheckBox, QStackedWidget, QFormLayout, 
    QProgressBar, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QThread
from app.services.ai_service import ai_service
from app.database.db import db_manager
from app.database.models import Project, Pipeline
from app.core.logger import logger
from app.modules.repo_scanner import repo_scanner
from app.modules.cost_estimator import cost_estimator
from app.ui.components.toast_notification import ToastNotification

class GenerationThread(QThread):
    # Signals to communicate results
    finished_success = Signal(int) # returns generated project_id
    finished_error = Signal(str)

    def __init__(self, proj_name, proj_desc, lang, fw, platform, target, security, quality):
        super().__init__()
        self.proj_name = proj_name
        self.proj_desc = proj_desc
        self.lang = lang
        self.fw = fw
        self.platform = platform
        self.target = target
        self.security = security
        self.quality = quality

    def run(self):
        try:
            logger.info("Generation thread started.")
            # 1. Save project in DB via ORM session
            with db_manager.get_session() as session:
                project = Project(
                    name=self.proj_name,
                    description=self.proj_desc,
                    language=self.lang,
                    framework=self.fw,
                    target=self.target
                )
                session.add(project)
                session.flush() # Populate project.id

                # 2. Call AI Service (OpenAI, Ollama, or Mock fallback)
                pipeline_content = ai_service.generate_pipeline(
                    self.lang, self.fw, self.platform, self.target, self.security, self.quality
                )
                
                # 3. Save generated pipeline via ORM session
                pipeline = Pipeline(
                    project_id=project.id,
                    platform=self.platform,
                    yaml_content=pipeline_content
                )
                session.add(pipeline)
                project_id = project.id

            db_manager.log_audit("generate_pipeline", "success", f"Generated {self.platform} for {self.proj_name}")
            self.finished_success.emit(project_id)
        except Exception as e:
            logger.error(f"Error in generation thread: {e}")
            db_manager.log_audit("generate_pipeline", "error", str(e))
            self.finished_error.emit(str(e))

class WizardWidget(QWidget):
    generation_completed = Signal(int) # Emits project_id on completion

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        self.header_title = QLabel("New Project Pipeline Wizard")
        self.header_title.setObjectName("HeaderLabel")
        self.layout.addWidget(self.header_title)
        
        self.header_sub = QLabel("Follow the steps to configure your deployment pipelines.")
        self.header_sub.setObjectName("SubHeaderLabel")
        self.layout.addWidget(self.header_sub)
        self.layout.addSpacing(20)

        # Stacked pages
        self.pages = QStackedWidget()
        
        # Page 1: General Info
        self.page1 = QWidget()
        self.setup_page1()
        self.pages.addWidget(self.page1)

        # Page 2: Language & Framework
        self.page2 = QWidget()
        self.setup_page2()
        self.pages.addWidget(self.page2)

        # Page 3: Integration Platforms
        self.page3 = QWidget()
        self.setup_page3()
        self.pages.addWidget(self.page3)

        # Page 4: Progress Indicator
        self.page4 = QWidget()
        self.setup_page4()
        self.pages.addWidget(self.page4)

        self.layout.addWidget(self.pages)

        # Navigation Buttons (at the bottom)
        self.nav_layout = QHBoxLayout()
        self.btn_back = QPushButton("← Back")
        self.btn_back.setObjectName("SecondaryButton")
        self.btn_back.clicked.connect(self._on_back_clicked)
        self.btn_back.setEnabled(False)

        self.btn_next = QPushButton("Next →")
        self.btn_next.clicked.connect(self._on_next_clicked)

        self.nav_layout.addWidget(self.btn_back)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_next)
        
        self.layout.addLayout(self.nav_layout)
        
        # Track current page index
        self.current_idx = 0

    def setup_page1(self):
        layout = QVBoxLayout(self.page1)
        card = QWidget()
        card.setObjectName("CardWidget")
        flayout = QFormLayout(card)
        flayout.setSpacing(15)

        title = QLabel("Step 1: Project Metadata")
        title.setObjectName("CardTitle")
        flayout.addRow(title)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. MyProductionApp")
        flayout.addRow("Project Name:", self.txt_name)

        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Brief description of application workloads...")
        flayout.addRow("Description:", self.txt_desc)

        btn_scan = QPushButton("📂 Auto-Detect Tech Stack from Local Folder")
        btn_scan.clicked.connect(self.scan_local_repo)
        flayout.addRow("", btn_scan)

        layout.addWidget(card)
        layout.addStretch()

    def scan_local_repo(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if not folder:
            return

        scan = repo_scanner.scan_repository(folder)
        if scan["status"] == "success":
            folder_name = os.path.basename(folder)
            self.txt_name.setText(folder_name)
            self.txt_desc.setText(f"Auto-scanned project ({scan['primary_language']})")
            
            # Select language in page 2 if found
            if scan["primary_language"] in ["Python", "Node.js", "Java", "Go", "Rust"]:
                idx = self.combo_lang.findText(scan["primary_language"])
                if idx >= 0:
                    self.combo_lang.setCurrentIndex(idx)

            ToastNotification.show_toast(
                self, 
                f"Detected Tech Stack: {scan['primary_language']} ({', '.join(scan['frameworks']) or 'Standard'})", 
                "success"
            )

    def setup_page2(self):
        layout = QVBoxLayout(self.page2)
        card = QWidget()
        card.setObjectName("CardWidget")
        flayout = QFormLayout(card)
        flayout.setSpacing(15)

        title = QLabel("Step 2: Technology Stack Selection")
        title.setObjectName("CardTitle")
        flayout.addRow(title)

        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Python", "Node.js", "Java", "Go", "Rust", "PHP"])
        self.combo_lang.currentTextChanged.connect(self._on_lang_changed)
        flayout.addRow("Language:", self.combo_lang)

        self.combo_fw = QComboBox()
        flayout.addRow("Framework:", self.combo_fw)
        self._on_lang_changed(self.combo_lang.currentText())

        layout.addWidget(card)
        layout.addStretch()

    def setup_page3(self):
        layout = QVBoxLayout(self.page3)
        
        # Tech Platforms Card
        card = QWidget()
        card.setObjectName("CardWidget")
        flayout = QFormLayout(card)
        flayout.setSpacing(15)

        title = QLabel("Step 3: CI/CD Target Platforms")
        title.setObjectName("CardTitle")
        flayout.addRow(title)

        self.combo_platform = QComboBox()
        self.combo_platform.addItems(["GitHub Actions", "GitLab CI", "Jenkins", "Azure DevOps"])
        flayout.addRow("CI/CD Platform:", self.combo_platform)

        self.combo_target = QComboBox()
        self.combo_target.addItems(["Docker", "Kubernetes", "AWS", "GCP", "Azure", "VM"])
        flayout.addRow("Deployment Target:", self.combo_target)
        
        layout.addWidget(card)
        
        # Add-ons Card
        card_addons = QWidget()
        card_addons.setObjectName("CardWidget")
        addons_layout = QVBoxLayout(card_addons)
        addons_title = QLabel("DevSecOps & Testing Add-ons")
        addons_title.setObjectName("CardTitle")
        addons_layout.addWidget(addons_title)

        self.chk_security = QCheckBox("Enable DevSecOps Security Scanning (Gitleaks, Trivy)")
        self.chk_security.setChecked(True)
        self.chk_quality = QCheckBox("Enable Code Quality / Linting checks")
        self.chk_quality.setChecked(True)

        addons_layout.addWidget(self.chk_security)
        addons_layout.addWidget(self.chk_quality)
        
        layout.addWidget(card_addons)
        layout.addStretch()

    def setup_page4(self):
        layout = QVBoxLayout(self.page4)
        card = QWidget()
        card.setObjectName("CardWidget")
        vlayout = QVBoxLayout(card)
        vlayout.setSpacing(20)
        vlayout.setAlignment(Qt.AlignCenter)

        title = QLabel("Generating Assets...")
        title.setObjectName("CardTitle")
        title.setAlignment(Qt.AlignCenter)
        vlayout.addWidget(title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate spinner
        self.progress_bar.setFixedHeight(12)
        vlayout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Consulting AI models for optimized workflow config...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        vlayout.addWidget(self.lbl_status)

        layout.addWidget(card)
        layout.addStretch()

    def reset_wizard(self):
        """Restore all parameters to defaults and restart at Page 1."""
        self.txt_name.clear()
        self.txt_desc.clear()
        self.combo_lang.setCurrentIndex(0)
        self.combo_platform.setCurrentIndex(0)
        self.combo_target.setCurrentIndex(0)
        self.chk_security.setChecked(True)
        self.chk_quality.setChecked(True)
        self.current_idx = 0
        self.pages.setCurrentIndex(0)
        self.btn_back.setEnabled(False)
        self.btn_next.setText("Next →")

    def _on_lang_changed(self, lang):
        """Update framework selection options based on the chosen language."""
        self.combo_fw.clear()
        frameworks = {
            "Python": ["Django", "Flask", "FastAPI"],
            "Node.js": ["React", "Express", "Angular", "Vue"],
            "Java": ["Spring Boot"],
            "Go": ["Gin"],
            "Rust": ["Actix Web"],
            "PHP": ["Laravel"]
        }
        self.combo_fw.addItems(frameworks.get(lang, []))

    def _on_back_clicked(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.pages.setCurrentIndex(self.current_idx)
            self.btn_next.setText("Next →")
            if self.current_idx == 0:
                self.btn_back.setEnabled(False)

    def _on_next_clicked(self):
        # Validation for page 1
        if self.current_idx == 0:
            if not self.txt_name.text().strip():
                QMessageBox.warning(self, "Validation Error", "Please provide a project name.")
                return
            self.btn_back.setEnabled(True)

        if self.current_idx < 2:
            self.current_idx += 1
            self.pages.setCurrentIndex(self.current_idx)
            if self.current_idx == 2:
                self.btn_next.setText("🚀 Generate Pipeline")
        elif self.current_idx == 2:
            # Trigger generation process
            self.current_idx += 1
            self.pages.setCurrentIndex(self.current_idx)
            self.btn_back.setEnabled(False)
            self.btn_next.setEnabled(False)
            self._trigger_generation()

    def _trigger_generation(self):
        name = self.txt_name.text().strip()
        desc = self.txt_desc.text().strip()
        lang = self.combo_lang.currentText()
        fw = self.combo_fw.currentText()
        platform = self.combo_platform.currentText()
        target = self.combo_target.currentText()
        sec = self.chk_security.isChecked()
        qual = self.chk_quality.isChecked()

        self.lbl_status.setText(f"Generating {platform} pipeline for {name}...")

        # Run thread
        self.gen_thread = GenerationThread(name, desc, lang, fw, platform, target, sec, qual)
        self.gen_thread.finished_success.connect(self._on_generation_success)
        self.gen_thread.finished_error.connect(self._on_generation_error)
        self.gen_thread.start()

    def _on_generation_success(self, project_id):
        self.btn_next.setEnabled(True)
        self.generation_completed.emit(project_id)
        # Reset wizard for next use
        self.reset_wizard()

    def _on_generation_error(self, err_msg):
        QMessageBox.critical(self, "Generation Failed", f"An error occurred: {err_msg}")
        self.reset_wizard()
        self.btn_next.setEnabled(True)
