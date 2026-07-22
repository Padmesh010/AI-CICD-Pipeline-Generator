from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFileDialog, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from app.modules.analyzer import project_analyzer
from app.ui.wizard import GenerationThread
from app.core.logger import logger

class AnalyzerWidget(QWidget):
    generation_completed = Signal(int) # Emits project_id on completion

    def __init__(self):
        super().__init__()
        self.detected_language = None
        self.detected_framework = None
        self.detected_target = "Docker" # Default fallback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # Header Title
        header_layout = QVBoxLayout()
        header_title = QLabel("Local Codebase Scanner")
        header_title.setObjectName("HeaderLabel")
        header_sub = QLabel("Scan your local git repositories to auto-detect languages, frameworks, and testing tools.")
        header_sub.setObjectName("SubHeaderLabel")
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_sub)
        layout.addLayout(header_layout)

        # Form Card
        card = QWidget()
        card.setObjectName("CardWidget")
        vlayout = QVBoxLayout(card)
        vlayout.setSpacing(15)

        label_select = QLabel("Select Local Project Directory:")
        label_select.setStyleSheet("font-weight: bold; color: #f8fafc;")
        vlayout.addWidget(label_select)

        dir_layout = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Browse to folder containing package.json, requirements.txt, etc.")
        
        btn_browse = QPushButton("Browse Folder...")
        btn_browse.setObjectName("SecondaryButton")
        btn_browse.clicked.connect(self._on_browse_clicked)
        
        dir_layout.addWidget(self.txt_path)
        dir_layout.addWidget(btn_browse)
        vlayout.addLayout(dir_layout)

        self.btn_scan = QPushButton("🔍 Analyze Repository Structure")
        self.btn_scan.clicked.connect(self._on_scan_clicked)
        vlayout.addWidget(self.btn_scan)

        layout.addWidget(card)

        # Report / Output Panel
        report_card = QWidget()
        report_card.setObjectName("CardWidget")
        report_layout = QVBoxLayout(report_card)
        
        report_title = QLabel("AI Detective Report")
        report_title.setObjectName("CardTitle")
        report_layout.addWidget(report_title)

        self.txt_report = QTextEdit()
        self.txt_report.setReadOnly(True)
        self.txt_report.setHtml("<p style='color:#94a3b8;'>Scan a project folder to populate analysis report.</p>")
        report_layout.addWidget(self.txt_report)

        # Action Trigger
        self.btn_generate = QPushButton("🚀 Generate Optimized Pipeline for this codebase")
        self.btn_generate.setEnabled(False)
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        report_layout.addWidget(self.btn_generate)

        layout.addWidget(report_card)

    def _on_browse_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Repository Directory")
        if folder:
            self.txt_path.setText(folder)

    def _on_scan_clicked(self):
        path = self.txt_path.text().strip()
        if not path:
            QMessageBox.warning(self, "Validation Error", "Please select a directory path first.")
            return

        self.txt_report.setHtml("<p style='color:#fbbf24;'>Analyzing codebase fingerprints...</p>")
        self.btn_scan.setEnabled(False)

        # Run analysis
        result = project_analyzer.analyze_directory(path)
        self.btn_scan.setEnabled(True)

        if not result["detected"]:
            self.txt_report.setHtml(
                "<h3 style='color:#ef4444;'>Detection Failed</h3>"
                "<p>We were unable to identify any recognized configuration blueprints in the root folder.</p>"
                "<h4>Logs:</h4>"
                "<ul>" + "".join([f"<li>{det}</li>" for det in result["details"]]) + "</ul>"
            )
            self.btn_generate.setEnabled(False)
            return

        self.detected_language = result["language"]
        self.detected_framework = result["framework"]
        
        self.txt_report.setHtml(result.get("html_report", ""))
        self.btn_generate.setEnabled(True)

    def _on_generate_clicked(self):
        path = self.txt_path.text().strip()
        folder_name = os.path.basename(path) or "ScannedApp"
        
        # Open a simple confirm dialog to trigger pipeline generation
        # We will use GitHub Actions + Docker deploy as the default scanned pipeline recommendation
        self.btn_generate.setEnabled(False)
        self.btn_scan.setEnabled(False)
        self.txt_report.append("\n<p style='color:#fbbf24;'>Calling AI service to generate deployment files...</p>")

        # Launch thread
        self.gen_thread = GenerationThread(
            proj_name=folder_name,
            proj_desc=f"Auto-generated workspace from scanning directory: {path}",
            lang=self.detected_language,
            fw=self.detected_framework,
            platform="GitHub Actions",
            target=self.detected_target,
            security=True,
            quality=True
        )
        
        self.gen_thread.finished_success.connect(self._on_generation_success)
        self.gen_thread.finished_error.connect(self._on_generation_error)
        self.gen_thread.start()

    def _on_generation_success(self, project_id):
        self.btn_generate.setEnabled(True)
        self.btn_scan.setEnabled(True)
        self.generation_completed.emit(project_id)

    def _on_generation_error(self, err):
        self.btn_generate.setEnabled(True)
        self.btn_scan.setEnabled(True)
        QMessageBox.critical(self, "Generation Failed", f"Failed to build configurations: {err}")
