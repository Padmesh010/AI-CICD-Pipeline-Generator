import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

MAX_BYTES = 5 * 1024 * 1024  # 5 MB per log file
BACKUP_COUNT = 5             # Keep 5 historical log archives

def _get_app_log_dir() -> str:
    """Return application log directory path."""
    app_data_dir = os.path.join(os.path.expanduser("~"), ".gemini", "antigravity", "ai_cicd_pipeline_generator")
    log_dir = os.path.join(app_data_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def setup_logger(name: str = "AI-CICD-Generator", log_filename: str = "app.log", level: int = logging.DEBUG) -> logging.Logger:
    """Create or retrieve a logger equipped with rotating file handlers and console formatting."""
    log_instance = logging.getLogger(name)
    log_instance.setLevel(level)

    if log_instance.handlers:
        return log_instance

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
    )

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    log_instance.addHandler(console_handler)

    # 2. Rotating File Handler
    try:
        log_dir = _get_app_log_dir()
        log_path = os.path.join(log_dir, log_filename)
        file_handler = RotatingFileHandler(
            log_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        log_instance.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to create file logger handler for {log_filename}: {e}", file=sys.stderr)

    return log_instance

# Primary Application Loggers
logger = setup_logger("AI-CICD-Generator", "app.log")
error_logger = setup_logger("AI-CICD-Errors", "error.log", level=logging.WARNING)
ai_logger = setup_logger("AI-CICD-AI", "ai.log")
generation_logger = setup_logger("AI-CICD-Generation", "generation.log")

def get_logger(module_name: str) -> logging.Logger:
    """Return scoped logger for a specific module."""
    return logging.getLogger(f"AI-CICD-Generator.{module_name}")
