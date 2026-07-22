from PySide6.QtWidgets import QStatusBar, QLabel, QProgressBar
from PySide6.QtCore import Qt
from app.core.task_manager import task_manager, TaskInfo
from app.ui.theme import DesignTokens

class TaskStatusBar(QStatusBar):
    """Application Status Bar connected to background task progress signals."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setVisible(False)

        self.addWidget(self.status_label, 1)
        self.addPermanentWidget(self.progress_bar)

        # Connect signals
        task_manager.task_started.connect(self._on_task_started)
        task_manager.task_progress.connect(self._on_task_progress)
        task_manager.task_completed.connect(self._on_task_completed)
        task_manager.task_failed.connect(self._on_task_failed)

    def _on_task_started(self, task_id: str, task_name: str):
        self.status_label.setText(f"Running: {task_name}...")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

    def _on_task_progress(self, task_id: str, percentage: int, stage_msg: str):
        self.progress_bar.setValue(percentage)
        if stage_msg:
            self.status_label.setText(stage_msg)

    def _on_task_completed(self, task_id: str, result: object):
        task_info = task_manager.get_task(task_id)
        name = task_info.name if task_info else "Task"
        self.status_label.setText(f"Task '{name}' completed successfully.")
        self.progress_bar.setVisible(False)

    def _on_task_failed(self, task_id: str, error_message: str):
        task_info = task_manager.get_task(task_id)
        name = task_info.name if task_info else "Task"
        self.status_label.setText(f"Task '{name}' failed: {error_message}")
        self.progress_bar.setVisible(False)
