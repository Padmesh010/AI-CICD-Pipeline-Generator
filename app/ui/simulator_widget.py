from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QProgressBar, QCheckBox, QFrame, QMessageBox, QDialog, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from app.modules.simulator import SimulationWorker
from app.database.db import db_manager
from app.core.logger import logger
from app.ui.theme import DesignTokens
from app.ui.components.toast_notification import ToastNotification

class StageCard(QFrame):
    """Visual card displaying state of a pipeline stage in the timeline."""
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("CardWidget")
        self.setMinimumSize(110, 75)
        self.setMaximumSize(130, 95)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setAlignment(Qt.AlignCenter)

        self.lbl_name = QLabel(self.name)
        self.lbl_name.setWordWrap(True)
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setStyleSheet("font-weight: bold; font-size: 11px;")
        self.layout.addWidget(self.lbl_name)

        self.lbl_status = QLabel("QUEUED")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 10px; color: #64748b; font-weight: bold;")
        self.layout.addWidget(self.lbl_status)

        self.set_state("queued")

    def set_state(self, state: str):
        """Transition background colors depending on build status."""
        self.state = state
        if state == "queued":
            self.lbl_status.setText("QUEUED")
            self.setStyleSheet(f"QFrame#CardWidget {{ background-color: {DesignTokens.DARK_BG_CARD}; border: 1px solid {DesignTokens.DARK_BORDER}; }}")
        elif state == "running":
            self.lbl_status.setText("RUNNING")
            self.setStyleSheet(f"QFrame#CardWidget {{ background-color: {DesignTokens.DARK_BG_SURFACE}; border: 2px solid {DesignTokens.ACCENT_AMBER}; }}")
            self.lbl_status.setStyleSheet(f"color: {DesignTokens.ACCENT_AMBER}; font-weight: bold;")
        elif state == "success":
            self.lbl_status.setText("SUCCESS")
            self.setStyleSheet(f"QFrame#CardWidget {{ background-color: {DesignTokens.DARK_BG_SURFACE}; border: 2px solid {DesignTokens.ACCENT_GREEN}; }}")
            self.lbl_status.setStyleSheet(f"color: {DesignTokens.ACCENT_GREEN}; font-weight: bold;")
        elif state == "failed":
            self.lbl_status.setText("FAILED")
            self.setStyleSheet(f"QFrame#CardWidget {{ background-color: {DesignTokens.DARK_BG_SURFACE}; border: 2px solid {DesignTokens.ACCENT_RED}; }}")
            self.lbl_status.setStyleSheet(f"color: {DesignTokens.ACCENT_RED}; font-weight: bold;")

class ArtifactsDialog(QDialog):
    """Modal displaying generated build artifacts."""
    def __init__(self, artifacts: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Build Artifacts Inspector")
        self.resize(500, 250)
        layout = QVBoxLayout(self)

        lbl = QLabel("Generated Build Artifacts & Logs:")
        lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl)

        table = QTableWidget(len(artifacts), 3)
        table.setHorizontalHeaderLabels(["Artifact Name", "Type", "Size"])
        for idx, art in enumerate(artifacts):
            table.setItem(idx, 0, QTableWidgetItem(art["name"]))
            table.setItem(idx, 1, QTableWidgetItem(art["type"]))
            table.setItem(idx, 2, QTableWidgetItem(art["size"]))
        layout.addWidget(table)

        btn = QPushButton("Close")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class SimulatorWidget(QWidget):
    simulation_finished = Signal(bool)

    def __init__(self):
        super().__init__()
        self.platform = "GitHub Actions"
        self.stages = ["Checkout", "Security Scan", "Build & Test", "Deploy"]
        self.worker = None
        self.cards = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # Header Title & Controls
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        self.lbl_title = QLabel("Pipeline Execution Simulator 2.0")
        self.lbl_title.setObjectName("HeaderLabel")
        self.lbl_sub = QLabel("Simulate runner workloads, parallel matrix jobs, retry failed stages, and inspect build artifacts.")
        self.lbl_sub.setObjectName("SubHeaderLabel")
        title_layout.addWidget(self.lbl_title)
        title_layout.addWidget(self.lbl_sub)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        self.chk_inject_error = QCheckBox("Inject simulated failure at Deploy stage")
        self.chk_inject_error.setStyleSheet("font-weight: 500;")
        header_layout.addWidget(self.chk_inject_error)

        self.btn_run = QPushButton("⚡ Start Simulation")
        self.btn_run.setProperty("class", "primary")
        self.btn_run.clicked.connect(self._on_run_clicked)
        header_layout.addWidget(self.btn_run)

        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.clicked.connect(self._on_pause_clicked)
        header_layout.addWidget(self.btn_pause)

        self.btn_artifacts = QPushButton("📦 Inspect Artifacts")
        self.btn_artifacts.clicked.connect(self._on_inspect_artifacts)
        header_layout.addWidget(self.btn_artifacts)

        self.btn_reset = QPushButton("🔄 Reset")
        self.btn_reset.clicked.connect(self._on_reset_clicked)
        header_layout.addWidget(self.btn_reset)

        layout.addLayout(header_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Stages timeline container
        self.timeline_widget = QWidget()
        self.timeline_widget.setObjectName("CardWidget")
        self.timeline_layout = QHBoxLayout(self.timeline_widget)
        self.timeline_layout.setContentsMargins(12, 16, 12, 16)
        self.timeline_layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timeline_widget)

        # Terminal Console Output
        console_title = QLabel("Runner Console Output")
        console_title.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {DesignTokens.TEXT_SECONDARY};")
        layout.addWidget(console_title)

        self.txt_console = QTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setFont(QFont("Consolas", 10))
        layout.addWidget(self.txt_console)

        self.setup_timeline(self.platform, self.stages)

    def setup_timeline(self, platform: str, stages: list):
        """Set up timeline nodes representing stages."""
        self.platform = platform
        self.stages = stages
        self.lbl_title.setText(f"Pipeline Execution Simulator 2.0: {platform}")
        
        while self.timeline_layout.count():
            child = self.timeline_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.cards.clear()
        for stage in self.stages:
            card = StageCard(stage)
            self.timeline_layout.addWidget(card)
            self.cards[stage] = card

    def _on_run_clicked(self):
        if self.worker and self.worker.isRunning():
            return

        self.txt_console.clear()
        self.progress_bar.setValue(0)
        for card in self.cards.values():
            card.set_state("queued")

        fail_stage = "Deploy" if self.chk_inject_error.isChecked() else None
        self.worker = SimulationWorker(self.platform, self.stages, inject_failure_at=fail_stage)
        self.worker.stage_started.connect(self._on_stage_started)
        self.worker.stage_log.connect(self._on_stage_log)
        self.worker.stage_completed.connect(self._on_stage_completed)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.finished_all.connect(self._on_simulation_finished)

        self.btn_run.setEnabled(False)
        self.worker.start()

    def _on_pause_clicked(self):
        if self.worker and self.worker.isRunning():
            if self.worker.is_paused:
                self.worker.resume()
                self.btn_pause.setText("⏸ Pause")
            else:
                self.worker.pause()
                self.btn_pause.setText("▶ Resume")

    def _on_reset_clicked(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()

        self.txt_console.clear()
        self.progress_bar.setValue(0)
        for card in self.cards.values():
            card.set_state("queued")
        self.btn_run.setEnabled(True)

    def _on_inspect_artifacts(self):
        if self.worker and self.worker.artifacts:
            dlg = ArtifactsDialog(self.worker.artifacts, self)
            dlg.exec()
        else:
            ToastNotification.show_toast(self, "No build artifacts generated yet. Run simulation first.", "info")

    def _on_stage_started(self, stage: str):
        if stage in self.cards:
            self.cards[stage].set_state("running")

    def _on_stage_log(self, log_line: str):
        self.txt_console.append(log_line)

    def _on_stage_completed(self, stage: str, status: str):
        if stage in self.cards:
            self.cards[stage].set_state(status)

    def _on_simulation_finished(self, success: bool):
        self.btn_run.setEnabled(True)
        self.simulation_finished.emit(success)
        status_str = "SUCCESS" if success else "FAILED (Rollback Executed)"
        db_manager.log_audit("simulate_pipeline", status_str, f"Platform: {self.platform}")
