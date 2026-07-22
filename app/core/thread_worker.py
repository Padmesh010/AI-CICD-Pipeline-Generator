from typing import Callable, Any, Optional, Dict
from PySide6.QtCore import QThread, Signal
from app.core.logger import logger
from app.core.exceptions import ErrorHandler
from app.core.task_manager import task_manager

class WorkerThread(QThread):
    """Generic QThread worker wrapping arbitrary functions to run off the UI thread."""
    progress = Signal(int, str)             # percentage, stage_message
    finished_result = Signal(object)        # target function return value
    error = Signal(Exception, str)          # exception, sanitized message
    canceled = Signal()                     # emitted when user cancels task

    def __init__(
        self, 
        func: Callable[..., Any], 
        *args: Any, 
        task_name: str = "Background Task", 
        task_description: str = "",
        **kwargs: Any
    ):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_canceled = False
        
        # Create corresponding task in global TaskManager
        self.task_info = task_manager.create_task(task_name, task_description)

    @property
    def task_id(self) -> str:
        return self.task_info.task_id

    def cancel(self) -> None:
        """Set cancellation flag."""
        self._is_canceled = True
        task_manager.cancel_task(self.task_id)
        self.canceled.emit()

    def is_canceled(self) -> bool:
        return self._is_canceled

    def report_progress(self, percentage: int, stage_message: str = "") -> None:
        """Helper for target functions to emit progress updates."""
        if not self._is_canceled:
            task_manager.update_progress(self.task_id, percentage, stage_message)
            self.progress.emit(percentage, stage_message)

    def run(self) -> None:
        """Execute callable target on background thread."""
        task_manager.start_task(self.task_id)
        logger.info(f"WorkerThread [{self.task_id}] running task '{self.task_info.name}'")

        try:
            # Check if progress callback parameter is accepted by the target
            if "progress_callback" in self.func.__code__.co_varnames:
                self.kwargs["progress_callback"] = self.report_progress

            if self._is_canceled:
                return

            result = self.func(*self.args, **self.kwargs)

            if not self._is_canceled:
                task_manager.mark_completed(self.task_id, result)
                self.finished_result.emit(result)

        except Exception as exc:
            if not self._is_canceled:
                user_msg = f"Task '{self.task_info.name}' failed: {exc}"
                task_manager.mark_failed(self.task_id, str(exc))
                ErrorHandler.handle_exception(exc, user_friendly_msg=user_msg, show_dialog=False)
                self.error.emit(exc, str(exc))
