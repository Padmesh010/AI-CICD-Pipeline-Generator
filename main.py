import sys
import os
from PySide6.QtWidgets import QApplication
from app.database.db import db_manager
from app.ui.main_window import MainWindow
from app.ui.theme import theme_manager
from app.core.logger import logger
from app.core.exceptions import ErrorHandler

def main():
    # Register global exception hook for uncaught exceptions
    ErrorHandler.setup_global_exception_hook()
    logger.info("Initializing AI CI/CD Pipeline Generator application...")
    
    # Initialize the Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("AI-CICD-Pipeline-Generator")
    app.setOrganizationName("Google Gemini Antigravity")
    app.setStyleSheet(theme_manager.get_stylesheet())
    
    # Establish DB tables & seed
    db_manager.init_db()
    db_manager.log_audit("app_launch", "success", "Application loaded successfully.")

    # Create MainWindow
    window = MainWindow()
    window.show()
    
    # Start loop
    logger.info("Application UI visible. Starting Qt exec loop.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
