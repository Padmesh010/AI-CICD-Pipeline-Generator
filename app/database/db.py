import os
import sqlite3
import shutil
from datetime import datetime
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from app.core.logger import logger
from app.core.exceptions import DatabaseError, ErrorHandler
from app.database.models import Base, Project, Pipeline, Template, AuditLog

class DatabaseManager:
    """Enterprise Database Manager supporting SQLAlchemy ORM and automated SQLite backups."""

    def __init__(self):
        self.app_dir = os.path.join(
            os.path.expanduser("~"), ".gemini", "antigravity", "ai_cicd_pipeline_generator"
        )
        os.makedirs(self.app_dir, exist_ok=True)
        
        self.db_path = os.path.join(self.app_dir, "app.db")
        self.backup_dir = os.path.join(self.app_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

        self.db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False}, echo=False)
        self.session_factory = sessionmaker(bind=self.engine)
        self.ScopedSession = scoped_session(self.session_factory)

        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Return raw SQLite connection for backward compatibility."""
        return sqlite3.connect(self.db_path)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Provide thread-safe transactional scope around a series of operations."""
        session = self.ScopedSession()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            ErrorHandler.handle_exception(
                DatabaseError(f"Database transaction error: {e}", e), show_dialog=False
            )
            raise e
        finally:
            session.close()
            self.ScopedSession.remove()

    def backup_database(self) -> str:
        """Create automated timestamped backup copy of SQLite database file."""
        if not os.path.exists(self.db_path):
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"app_backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backup created successfully: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return ""

    def init_db(self) -> None:
        """Initialize ORM schemas and seed baseline templates."""
        try:
            Base.metadata.create_all(self.engine)
            self._apply_migrations()
            logger.info("Database ORM tables initialized successfully via SQLAlchemy.")
            self._seed_default_templates()
        except Exception as e:
            ErrorHandler.handle_exception(
                DatabaseError(f"Error initializing database tables: {e}", e), show_dialog=False
            )

    def _apply_migrations(self) -> None:
        """Apply lightweight column migrations to existing SQLite database tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(templates)")
                columns = [col[1] for col in cursor.fetchall()]
                if "version" not in columns:
                    cursor.execute("ALTER TABLE templates ADD COLUMN version TEXT DEFAULT '1.0.0'")
                    conn.commit()
                    logger.info("Applied database migration: Added 'version' column to templates table.")
        except Exception as e:
            logger.error(f"Error applying table migration: {e}")

    def _seed_default_templates(self) -> None:
        """Seed initial pipeline templates if empty."""
        try:
            with self.get_session() as session:
                count = session.query(Template).filter(Template.is_custom == 0).count()
                if count > 0:
                    return

                default_templates = [
                    Template(
                        name="Django GHA Docker Deploy",
                        platform="GitHub Actions",
                        language="Python",
                        framework="Django",
                        content="# Django CI/CD Pipeline\nname: Django CI\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  build-and-test:\n    runs-on: ubuntu-latest\n    steps:\n    - uses: actions/checkout@v4\n    - name: Set up Python\n      uses: actions/setup-python@v5\n      with:\n        python-version: '3.12'\n    - name: Install dependencies\n      run: |\n        python -m pip install --upgrade pip\n        pip install -r requirements.txt\n    - name: Run Tests\n      run: python manage.py test\n",
                        is_custom=0
                    ),
                    Template(
                        name="React SPA S3 Deploy",
                        platform="GitHub Actions",
                        language="Node.js",
                        framework="React",
                        content="# React S3 Deploy\nname: Deploy React to S3\n\non:\n  push:\n    branches: [ main ]\n\njobs:\n  build-and-deploy:\n    runs-on: ubuntu-latest\n    steps:\n    - uses: actions/checkout@v4\n    - name: Set up Node.js\n      uses: actions/setup-node@v4\n      with:\n        node-version: '20'\n    - name: Install & Build\n      run: |\n        npm ci\n        npm run build\n    - name: Deploy to S3\n      run: echo \"aws s3 sync build/ s3://my-app-bucket\"",
                        is_custom=0
                    ),
                    Template(
                        name="FastAPI K8s GitLab CI",
                        platform="GitLab CI",
                        language="Python",
                        framework="FastAPI",
                        content="# FastAPI GitLab Pipeline\nstages:\n  - test\n  - build\n  - deploy\n\ntest_job:\n  stage: test\n  image: python:3.12-slim\n  script:\n    - pip install -r requirements.txt pytest\n    - pytest\n\nbuild_job:\n  stage: build\n  image: docker:24.0.5\n  services:\n    - docker:24.0.5-dind\n  script:\n    - docker build -t fastapi-app:latest .\n",
                        is_custom=0
                    ),
                    Template(
                        name="Spring Boot Jenkins VM",
                        platform="Jenkins",
                        language="Java",
                        framework="Spring Boot",
                        content="pipeline {\n    agent any\n    stages {\n        stage('Checkout') {\n            steps {\n                checkout scm\n            }\n        }\n        stage('Build') {\n            steps {\n                sh './gradlew clean build'\n            }\n        }\n        stage('Test') {\n            steps {\n                sh './gradlew test'\n            }\n        }\n    }\n}",
                        is_custom=0
                    )
                ]

                session.add_all(default_templates)
                logger.info("Database seeded with default templates via SQLAlchemy ORM.")
        except Exception as e:
            logger.error(f"Error seeding default templates: {e}")

    def log_audit(self, action: str, status: str, details: str = None) -> None:
        """Add entry to audit log using ORM session."""
        try:
            with self.get_session() as session:
                log_entry = AuditLog(action=action, status=status, details=details)
                session.add(log_entry)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

# Global database manager instance
db_manager = DatabaseManager()
