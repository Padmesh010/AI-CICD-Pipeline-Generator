import time
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from PySide6.QtCore import QObject, Signal
from app.core.logger import logger
from app.core.exceptions import ErrorHandler

class TaskState(Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

@dataclass
class TaskInfo:
    task_id: str
    name: str
    description: str
    state: TaskState = TaskState.QUEUED
    progress: int = 0
    current_stage: str = "Initializing"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    result: Any = None
    logs: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        if not self.start_time:
            return 0.0
        end = self.end_time or time.time()
        return round(end - self.start_time, 2)

class TaskManager(QObject):
    """Central registry and signal hub for application background execution tasks."""
    task_started = Signal(str, str)             # task_id, task_name
    task_progress = Signal(str, int, str)       # task_id, percentage, stage_message
    task_completed = Signal(str, object)        # task_id, result_object
    task_failed = Signal(str, str)              # task_id, error_message
    task_canceled = Signal(str)                 # task_id

    def __init__(self):
        super().__init__()
        self._tasks: Dict[str, TaskInfo] = {}

    def create_task(self, name: str, description: str = "") -> TaskInfo:
        """Create and register a new background task."""
        task_id = str(uuid.uuid4())[:8]
        task = TaskInfo(
            task_id=task_id,
            name=name,
            description=description
        )
        self._tasks[task_id] = task
        logger.info(f"Task [{task_id}] '{name}' registered.")
        return task

    def start_task(self, task_id: str) -> None:
        """Mark task as active/running."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.state = TaskState.RUNNING
            task.start_time = time.time()
            task.logs.append(f"[{time.strftime('%H:%M:%S')}] Task started.")
            self.task_started.emit(task_id, task.name)

    def update_progress(self, task_id: str, percentage: int, stage_message: str = "") -> None:
        """Update progress indicator and current stage."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.progress = min(100, max(0, percentage))
            if stage_message:
                task.current_stage = stage_message
                task.logs.append(f"[{time.strftime('%H:%M:%S')}] {stage_message}")
            self.task_progress.emit(task_id, task.progress, task.current_stage)

    def mark_completed(self, task_id: str, result: Any = None) -> None:
        """Mark task as successfully finished."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.state = TaskState.COMPLETED
            task.progress = 100
            task.end_time = time.time()
            task.result = result
            task.logs.append(f"[{time.strftime('%H:%M:%S')}] Task completed successfully in {task.duration_seconds}s.")
            logger.info(f"Task [{task_id}] completed in {task.duration_seconds}s.")
            self.task_completed.emit(task_id, result)

    def mark_failed(self, task_id: str, error_msg: str) -> None:
        """Mark task as failed with error details."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.state = TaskState.FAILED
            task.end_time = time.time()
            task.error_message = error_msg
            task.logs.append(f"[{time.strftime('%H:%M:%S')}] Task failed: {error_msg}")
            logger.error(f"Task [{task_id}] failed: {error_msg}")
            self.task_failed.emit(task_id, error_msg)

    def cancel_task(self, task_id: str) -> None:
        """Mark task as canceled by user."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.state = TaskState.CANCELED
            task.end_time = time.time()
            task.logs.append(f"[{time.strftime('%H:%M:%S')}] Task canceled by user.")
            logger.info(f"Task [{task_id}] canceled.")
            self.task_canceled.emit(task_id)

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        return self._tasks.get(task_id)

    def get_active_tasks(self) -> List[TaskInfo]:
        return [t for t in self._tasks.values() if t.state in (TaskState.QUEUED, TaskState.RUNNING)]

    def get_all_tasks(self) -> List[TaskInfo]:
        return list(self._tasks.values())

# Global TaskManager singleton instance
task_manager = TaskManager()
