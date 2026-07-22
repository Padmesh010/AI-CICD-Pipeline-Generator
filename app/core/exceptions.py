import sys
import traceback
import re
from typing import Optional
from app.core.logger import logger, error_logger

class AICICDPipelineError(Exception):
    """Base exception class for all AI CI/CD Pipeline Generator errors."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.original_exception = original_exception

class ConfigurationError(AICICDPipelineError):
    """Raised when configuration loading, saving, or parsing fails."""
    pass

class SecurityError(AICICDPipelineError):
    """Raised when security violations, secret leaks, or path traversals occur."""
    pass

class DatabaseError(AICICDPipelineError):
    """Raised when SQLite database initialization or query operations fail."""
    pass

class AIProviderError(AICICDPipelineError):
    """Raised when external AI providers (OpenAI, Ollama, Anthropic, etc.) fail."""
    pass

class ValidationError(AICICDPipelineError):
    """Raised when pipeline syntax or artifact validation fails."""
    pass

class GeneratorError(AICICDPipelineError):
    """Raised when pipeline, docker, k8s, or terraform code generation fails."""
    pass

class PluginError(AICICDPipelineError):
    """Raised when plugin discovery or compatibility execution fails."""
    pass

class ErrorHandler:
    """Centralized exception handling service."""

    @staticmethod
    def sanitize_stacktrace(tb_str: str) -> str:
        """Sanitize API keys, bearer tokens, and secrets from stack trace strings."""
        if not tb_str:
            return ""
        # Redact Bearer tokens and OpenAI keys
        sanitized = re.sub(r"sk-[a-zA-Z0-9T3BlbkFJ]{20,}", "sk-***[REDACTED]***", tb_str)
        sanitized = re.sub(r"Bearer\s+[a-zA-Z0-9_\-\.]+", "Bearer ***[REDACTED]***", sanitized)
        sanitized = re.sub(r"AKIA[0-9A-Z]{16}", "AKIA***[REDACTED]***", sanitized)
        return sanitized

    @classmethod
    def handle_exception(cls, exc: Exception, user_friendly_msg: str = "", show_dialog: bool = True) -> None:
        """Log exception safely and trigger GUI modal dialog if QApplication is active."""
        error_type = type(exc).__name__
        raw_tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        clean_tb = cls.sanitize_stacktrace(raw_tb)

        log_msg = f"{user_friendly_msg} | {error_type}: {exc}" if user_friendly_msg else f"{error_type}: {exc}"
        
        # Log to general and dedicated error loggers
        logger.error(log_msg)
        error_logger.error(f"{log_msg}\nSanitized Stacktrace:\n{clean_tb}")

        # Show GUI dialog if enabled and Qt is available
        if show_dialog:
            cls._show_gui_error_dialog(user_friendly_msg or str(exc), error_type)

    @classmethod
    def _show_gui_error_dialog(cls, message: str, title: str = "Application Error") -> None:
        """Display PySide6 QMessageBox error dialog without crashing if running headless."""
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance():
                dialog = QMessageBox()
                dialog.setIcon(QMessageBox.Critical)
                dialog.setWindowTitle(f"Error - {title}")
                dialog.setText(message)
                dialog.setInformativeText("An unexpected error occurred. Technical details have been logged to the system logs.")
                dialog.setStandardButtons(QMessageBox.Ok)
                dialog.exec()
        except Exception as gui_ex:
            logger.error(f"Failed to display error dialog: {gui_ex}")

    @classmethod
    def global_excepthook(cls, exctype, value, tb) -> None:
        """Global sys.excepthook replacement for unhandled exceptions."""
        if issubclass(exctype, KeyboardInterrupt):
            sys.__excepthook__(exctype, value, tb)
            return

        raw_tb = "".join(traceback.format_exception(exctype, value, tb))
        clean_tb = cls.sanitize_stacktrace(raw_tb)
        
        logger.critical(f"Unhandled Exception [{exctype.__name__}]: {value}")
        error_logger.critical(f"Unhandled Exception [{exctype.__name__}]: {value}\n{clean_tb}")

        cls._show_gui_error_dialog(
            f"An unexpected critical error occurred: {value}",
            title=exctype.__name__
        )

    @classmethod
    def setup_global_exception_hook(cls) -> None:
        """Install global exception hook."""
        sys.excepthook = cls.global_excepthook
        logger.info("Global exception hook registered successfully.")
