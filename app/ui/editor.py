import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QPlainTextEdit, QSplitter, QTextEdit, QMessageBox, QFileDialog
)
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt, QRegularExpression, Signal, QThread
from app.services.ai_service import ai_service
from app.services.export_service import export_service
from app.validators.pipeline_val import pipeline_validator
from app.modules.cost_estimator import cost_estimator
from app.reports.report_gen import report_generator
from app.database.db import db_manager
from app.database.models import Project, Pipeline
from app.core.logger import logger
from app.ui.components.code_editor import CodeEditor
from app.ui.components.toast_notification import ToastNotification
import zipfile

class DevOpsHighlighter(QSyntaxHighlighter):
    """Custom syntax highlighting for pipeline code configurations (YAML, Docker, Terraform)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []

        # Keywords format (keys, instructions)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#38bdf8")) # Light blue
        keyword_format.setFontWeight(QFont.Bold)
        
        # Strings format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#34d399")) # Light green
        
        # Comments format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#64748b")) # Gray/Slate
        comment_format.setFontItalic(True)

        # Variables format e.g. ${{ secrets.FOO }} or $VAR
        var_format = QTextCharFormat()
        var_format.setForeground(QColor("#fbbf24")) # Amber/Orange

        # Rules definitions
        # 1. Keys ending in colon (YAML)
        self.rules.append((QRegularExpression(r"\b\w+(?=\s*:)"), keyword_format))
        # 2. Dockerfile commands
        docker_cmds = r"\b(FROM|RUN|COPY|ADD|CMD|ENTRYPOINT|ENV|EXPOSE|WORKDIR|USER|ARG|STOPSIGNAL|HEALTHCHECK|SHELL)\b"
        self.rules.append((QRegularExpression(docker_cmds), keyword_format))
        # 3. Double-quoted strings
        self.rules.append((QRegularExpression(r"\"[^\"]*\""), string_format))
        # 4. Single-quoted strings
        self.rules.append((QRegularExpression(r"'[^']*'"), string_format))
        # 5. Comments
        self.rules.append((QRegularExpression(r"(#|//).*"), comment_format))
        # 6. Actions expressions
        self.rules.append((QRegularExpression(r"\$\{\{[^\}]+\}\}"), var_format))
        # 7. Shell variables
        self.rules.append((QRegularExpression(r"\$[a-zA-Z_][a-zA-Z0-9_]*"), var_format))

    def highlightBlock(self, text):
        for pattern, char_format in self.rules:
            expression = QRegularExpression(pattern)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), char_format)

class ExplanationThread(QThread):
    finished = Signal(str)

    def __init__(self, stage, code):
        super().__init__()
        self.stage = stage
        self.code = code

    def run(self):
        result = ai_service.explain_stage(self.stage, self.code)
        self.finished.emit(result)

class EditorWidget(QWidget):
    trigger_simulation = Signal(str, list) # platform, list of stage names

    def __init__(self):
        super().__init__()
        self.project_id = None
        self.project_name = ""
        self.language = ""
        self.framework = ""
        self.target = ""
        
        self.generated_assets = {} # cache of files
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(15)

        # Header Bar
        header = QHBoxLayout()
        self.lbl_title = QLabel("Workspace: No Project Loaded")
        self.lbl_title.setObjectName("HeaderLabel")
        header.addWidget(self.lbl_title)
        
        header.addStretch()
        
        self.btn_validate = QPushButton("🛡️ Validate Security & Flow")
        self.btn_validate.setObjectName("SecondaryButton")
        self.btn_validate.clicked.connect(self._on_validate_clicked)
        header.addWidget(self.btn_validate)

        self.btn_sim = QPushButton("⚡ Simulate Pipeline")
        self.btn_sim.setObjectName("SecondaryButton")
        self.btn_sim.clicked.connect(self._on_sim_clicked)
        header.addWidget(self.btn_sim)

        self.btn_export = QPushButton("💾 Export Files")
        self.btn_export.clicked.connect(self._on_export_clicked)
        header.addWidget(self.btn_export)

        main_layout.addLayout(header)

        # Split editor and AI panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel: File Tabs
        self.tabs = QTabWidget()
        
        self.txt_pipeline = QPlainTextEdit()
        self.txt_pipeline.setReadOnly(False)
        self.highlighter_pipeline = DevOpsHighlighter(self.txt_pipeline.document())
        self.tabs.addTab(self.txt_pipeline, "CI/CD Pipeline")

        self.txt_docker = QPlainTextEdit()
        self.highlighter_docker = DevOpsHighlighter(self.txt_docker.document())
        self.tabs.addTab(self.txt_docker, "Dockerfile")

        self.txt_k8s = QPlainTextEdit()
        self.highlighter_k8s = DevOpsHighlighter(self.txt_k8s.document())
        self.tabs.addTab(self.txt_k8s, "Kubernetes Manifests")

        self.txt_terraform = QPlainTextEdit()
        self.highlighter_tf = DevOpsHighlighter(self.txt_terraform.document())
        self.tabs.addTab(self.txt_terraform, "Terraform IaC")

        self.txt_readme = QPlainTextEdit()
        self.tabs.addTab(self.txt_readme, "Deployment README")

        splitter.addWidget(self.tabs)

        # Right Panel: Sidebar Assistant
        sidebar = QWidget()
        sidebar.setObjectName("CardWidget")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)

        sidebar_title = QLabel("DevOps AI Tutor")
        sidebar_title.setObjectName("CardTitle")
        sidebar_layout.addWidget(sidebar_title)

        self.btn_explain = QPushButton("📖 Explain Selected Code")
        self.btn_explain.clicked.connect(self._on_explain_clicked)
        sidebar_layout.addWidget(self.btn_explain)

        self.txt_explanation = QTextEdit()
        self.txt_explanation.setReadOnly(True)
        self.txt_explanation.setHtml("<p style='color:#94a3b8;'>Select some code blocks and click <i>Explain Code</i> to launch the interactive learning mode.</p>")
        sidebar_layout.addWidget(self.txt_explanation)

        splitter.addWidget(sidebar)
        splitter.setSizes([600, 250])
        main_layout.addWidget(splitter)

    def load_project(self, project_id):
        """Fetch project details and assets from the SQLite database."""
        try:
            self.project_id = project_id
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get project metadata
            cursor.execute("SELECT name, language, framework, target FROM projects WHERE id = ?", (project_id,))
            proj = cursor.fetchone()
            if not proj:
                conn.close()
                return
            
            self.project_name, self.language, self.framework, self.target = proj
            self.lbl_title.setText(f"Workspace: {self.project_name} ({self.language} / {self.framework})")
            
            # Get pipeline
            cursor.execute("SELECT platform, yaml_content FROM pipelines WHERE project_id = ?", (project_id,))
            pipe = cursor.fetchone()
            platform, yaml_content = pipe if pipe else ("GitHub Actions", "")
            
            self.platform = platform
            self.txt_pipeline.setPlainText(yaml_content)
            self.tabs.setTabText(0, f"{platform} Workflow")

            # Load or generate secondary assets (Dockerfile, Kubernetes, Terraform) offline
            logger.info("Loading auxiliary resources for project workspace...")
            docker_assets = ai_service.generate_docker(self.language, self.framework)
            k8s_assets = ai_service.generate_k8s(
                self.project_name.lower(), "production", 3, 8000, f"{self.project_name.lower()}.local"
            )
            tf_assets = ai_service.generate_terraform(self.target, "us-east-1", "production")

            # Cache the files
            self.generated_assets = {
                "pipeline": yaml_content,
                "Dockerfile": docker_assets.get("Dockerfile", ""),
                ".dockerignore": docker_assets.get(".dockerignore", ""),
                "docker-compose.yml": docker_assets.get("docker-compose.yml", ""),
                "k8s_manifests": k8s_assets,
                "terraform": tf_assets
            }

            # Set fields
            self.txt_docker.setPlainText(self.generated_assets["Dockerfile"])
            
            # Format combined manifestations
            k8s_combined = "\n---\n".join([f"# File: {name}\n{data}" for name, data in k8s_assets.items()])
            self.txt_k8s.setPlainText(k8s_combined)
            
            tf_combined = "\n---\n".join([f"# File: {name}\n{data}" for name, data in tf_assets.items()])
            self.txt_terraform.setPlainText(tf_combined)

            # Generate helper README markdown
            readme = f"""# Deployment Guide for {self.project_name}

Your production assets have been generated successfully by the AI Pipeline Generator.

## Contents
1. **CI/CD Configuration**: Configured for {self.platform}. Save this to your repository root under the standard configuration path.
2. **Dockerfile & Compose**: Build optimized container instances.
3. **Kubernetes manifests**: Deploys pod groups, routing rules, config-maps, and HPA auto-scalers inside namespace `production`.
4. **Terraform Scripts**: Sets up public network topologies and cloud instances.

## Next Steps
- Click the **🛡️ Validate Security & Flow** button above to check for hardcoded secrets or version issues.
- Click **⚡ Simulate Pipeline** to watch the execution stages complete in real time.
- Click **💾 Export Files** to download a unified ZIP folder of all infrastructure and deployment configurations.
"""
            self.txt_readme.setPlainText(readme)
            conn.close()

            # Set text assistant window to prompt tips
            self.txt_explanation.setHtml("<p style='color:#38bdf8;'><b>Project Workspace loaded.</b></p><p>Select code segments in the editor tabs and click <i>Explain Selected Code</i> to learn the DevOps concepts behind each stage.</p>")

        except Exception as e:
            logger.error(f"Error loading project workspace: {e}")
            QMessageBox.critical(self, "Load Error", f"Could not load workspace assets: {e}")

    def _on_validate_clicked(self):
        if not self.project_id:
            return
        
        # Validate current pipeline buffer
        content = self.txt_pipeline.toPlainText()
        val_result = pipeline_validator.validate(self.platform, content)
        
        # Display validation alert popup
        status_text = "PASSED" if val_result["is_valid"] else "FAILED"
        msg = f"<h3>Static Pipeline Validation: {status_text}</h3>"
        
        if val_result["errors"]:
            msg += "<h4 style='color:#ef4444;'>Critical Failures / Errors:</h4><ul>"
            for err in val_result["errors"]:
                msg += f"<li style='color:#f87171;'>{err}</li>"
            msg += "</ul>"
            
        if val_result["warnings"]:
            msg += "<h4 style='color:#fbbf24;'>Warnings / Security Alerts:</h4><ul>"
            for warn in val_result["warnings"]:
                msg += f"<li style='color:#fbbd23;'>{warn}</li>"
            msg += "</ul>"
            
        if not val_result["errors"] and not val_result["warnings"]:
            msg += "<p style='color:#34d399;'>Congratulations! No issues found. The configuration fits industry best practices.</p>"
            
        QMessageBox.information(self, "Security & Structure Audit", msg)

    def _on_sim_clicked(self):
        if not self.project_id:
            return
        
        # Determine stages present in the pipeline file
        content = self.txt_pipeline.toPlainText()
        stages = ["Checkout", "Build & Test"]
        
        if "lint" in content.lower() or "quality" in content.lower():
            stages.append("Code Quality")
        if "security" in content.lower() or "scan" in content.lower() or "gitleaks" in content.lower():
            stages.append("Security Scan")
        if "docker" in content.lower() or "image" in content.lower():
            stages.append("Docker Build")
            stages.append("Push Image")
        if "deploy" in content.lower():
            stages.append("Deploy")
            stages.append("Smoke Tests")

        self.trigger_simulation.emit(self.platform, stages)

    def _on_explain_clicked(self):
        current_widget = self.tabs.currentWidget()
        if not isinstance(current_widget, QPlainTextEdit):
            return
        
        cursor = current_widget.textCursor()
        selected_code = cursor.selectedText()
        
        if not selected_code.strip():
            # If no selection, explain the current block/file
            selected_code = current_widget.toPlainText()[:1000]
            stage_name = self.tabs.tabText(self.tabs.currentIndex())
        else:
            stage_name = "Selected Code block"

        self.txt_explanation.setHtml("<p style='color:#94a3b8;'>AI Assistant is analyzing the syntax and compiling instructions...</p>")
        self.btn_explain.setEnabled(False)

        # Launch background Thread
        self.expl_thread = ExplanationThread(stage_name, selected_code)
        self.expl_thread.finished.connect(self._on_explanation_finished)
        self.expl_thread.start()

    def _on_explanation_finished(self, text):
        self.btn_explain.setEnabled(True)
        # Convert markdown-like response to simple HTML formatting
        html = text.replace("\n", "<br>")
        html = html.replace("###", "<h3 style='color:#38bdf8;'>").replace("##", "<h2 style='color:#38bdf8;'>")
        html = html.replace("**", "<b>").replace("*", "<i>")
        self.txt_explanation.setHtml(f"<div style='line-height:1.4; color:#e2e8f0;'>{html}</div>")

    def _on_export_clicked(self):
        if not self.project_id:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Deployment ZIP Archive", f"{self.project_name}_cicd_assets.zip", "ZIP files (*.zip)"
        )
        if not file_path:
            return

        try:
            files_to_bundle = {}

            # 1. Write Pipeline file with appropriate filename
            pipe_filename = ".github/workflows/main.yml"
            if "gitlab" in self.platform.lower():
                pipe_filename = ".gitlab-ci.yml"
            elif "azure" in self.platform.lower():
                pipe_filename = "azure-pipelines.yml"
            elif "circle" in self.platform.lower():
                pipe_filename = ".circleci/config.yml"
            elif "bitbucket" in self.platform.lower():
                pipe_filename = ".bitbucket-pipelines.yml"
            files_to_bundle[pipe_filename] = self.txt_pipeline.toPlainText()

            # 2. Write Docker assets
            if self.generated_assets.get("Dockerfile"):
                files_to_bundle["Dockerfile"] = self.generated_assets["Dockerfile"]
            if self.generated_assets.get(".dockerignore"):
                files_to_bundle[".dockerignore"] = self.generated_assets[".dockerignore"]
            if self.generated_assets.get("docker-compose.yml"):
                files_to_bundle["docker-compose.yml"] = self.generated_assets["docker-compose.yml"]

            # 3. Write Kubernetes manifest files
            k8s = self.generated_assets.get("k8s_manifests", {})
            for name, data in k8s.items():
                files_to_bundle[f"k8s/{name}"] = data

            # 4. Write Terraform manifest files
            tf = self.generated_assets.get("terraform", {})
            for name, data in tf.items():
                files_to_bundle[f"terraform/{name}"] = data

            # 5. Write README.md
            files_to_bundle["README.md"] = self.txt_readme.toPlainText()

            # Execute export via ExportService
            result = export_service.export_zip_bundle(file_path, files_to_bundle)
            ToastNotification.show_toast(
                self, 
                f"Exported repository pack ({result['file_count']} files) | SHA256: {result['sha256'][:8]}...", 
                "success"
            )
        except Exception as e:
            logger.error(f"Error exporting bundle: {e}")
            ToastNotification.show_toast(self, f"Export failed: {e}", "danger")
            db_manager.log_audit("export_zip", "error", str(e))
