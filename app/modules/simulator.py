import time
import random
from typing import Dict, List, Any, Optional
from PySide6.QtCore import QThread, Signal
from app.core.logger import logger
from app.core.task_manager import task_manager

class SimulationWorker(QThread):
    """Execution simulation engine with parallel job matrix support, stage retries, and artifact outputs."""

    stage_started = Signal(str)         # stage_name
    stage_log = Signal(str)             # log_line
    stage_completed = Signal(str, str)  # stage_name, status ("success", "failed")
    progress_updated = Signal(int)      # percentage
    finished_all = Signal(bool)         # was_successful

    def __init__(self, platform: str, stages: list, inject_failure_at: Optional[str] = None):
        super().__init__()
        self.platform = platform
        self.stages = stages
        self.inject_failure_at = inject_failure_at
        self.is_running = True
        self.is_paused = False
        self.failed_stage = None
        self.artifacts = []

        self.task_info = task_manager.create_task("Pipeline Simulation 2.0", f"Platform: {platform}")

    def run(self):
        """Execute simulation steps."""
        task_manager.start_task(self.task_info.task_id)
        logger.info(f"SimulationWorker 2.0 [{self.task_info.task_id}] running on {self.platform}.")

        total_stages = len(self.stages)
        for idx, stage in enumerate(self.stages):
            if not self.is_running:
                task_manager.cancel_task(self.task_info.task_id)
                self.finished_all.emit(False)
                return

            while self.is_paused:
                time.sleep(0.2)
                if not self.is_running:
                    return

            self.stage_started.emit(stage)
            percent = int((idx / total_stages) * 100)
            task_manager.update_progress(self.task_info.task_id, percent, f"Running {stage}")
            self.progress_updated.emit(percent)

            success = self._run_stage_details(stage)
            if not success:
                self.failed_stage = stage
                self.stage_completed.emit(stage, "failed")
                task_manager.mark_failed(self.task_info.task_id, f"Failed at stage {stage}")
                self.progress_updated.emit(100)

                if "Deploy" in stage or "Production" in stage:
                    self._run_rollback()

                self.finished_all.emit(False)
                return

            self.stage_completed.emit(stage, "success")
            time.sleep(0.3)

        self._generate_artifacts()
        task_manager.update_progress(self.task_info.task_id, 100, "Completed")
        task_manager.mark_completed(self.task_info.task_id, {"status": "success", "artifacts": len(self.artifacts)})
        self.progress_updated.emit(100)
        self.finished_all.emit(True)

    def cancel(self):
        self.is_running = False

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def _run_stage_details(self, stage: str) -> bool:
        """Stream terminal output lines for the current stage."""
        self.stage_log.emit(f"\n>>> [Stage: {stage}] Runner initialized on ubuntu-latest...")
        time.sleep(0.15)

        if stage == "Checkout":
            self.stage_log.emit("  $ git clone https://github.com/org/repo.git .")
            self.stage_log.emit("  HEAD is now at a1b2c3d4 Add CI workflow configuration.")
        elif "Security" in stage:
            self.stage_log.emit("  $ trivy fs --security-checks config,vuln .")
            self.stage_log.emit("  Result: 0 High/Critical vulnerabilities found.")
        elif "Test" in stage:
            self.stage_log.emit("  [Matrix Execution] Running parallel jobs: [py3.10, py3.11, py3.12]")
            self.stage_log.emit("  $ pytest tests/ --cov=app --cov-report=xml")
            self.stage_log.emit("  ================ 37 passed in 0.18s ================")
            self.stage_log.emit("  Coverage XML artifact generated: coverage.xml (88%)")
        elif "Build" in stage or "Docker" in stage:
            self.stage_log.emit("  $ docker build -t custom-app:latest .")
            self.stage_log.emit("  Successfully built image 9f8e7d6c5b4a.")
        elif "Deploy" in stage:
            self.stage_log.emit("  $ kubectl apply -f k8s/deployment.yaml")
            self.stage_log.emit("  deployment.apps/my-app configured")

        if self.inject_failure_at and self.inject_failure_at.lower() in stage.lower():
            self.stage_log.emit(f"  [ERROR] Execution failed at stage '{stage}': Exit Code 1 (Deployment Target Connection Timeout).")
            return False

        return True

    def _run_rollback(self):
        """Simulate automated blue/green or canary rollback."""
        self.stage_log.emit("\n>>> [AUTOMATED ROLLBACK ACTIVATED]")
        self.stage_log.emit("  $ kubectl rollout undo deployment/my-app")
        self.stage_log.emit("  Rollback to previous stable revision (v1.2.4) complete.")

    def _generate_artifacts(self):
        """Simulate generated build artifacts."""
        self.artifacts = [
            {"name": "coverage.xml", "type": "Test Coverage Report", "size": "45 KB"},
            {"name": "app-container.tar", "type": "Docker Image Layer Archive", "size": "142 MB"},
            {"name": "terraform-plan.tfplan", "type": "Terraform Execution Plan", "size": "12 KB"}
        ]
