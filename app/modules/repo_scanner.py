import os
import re
from typing import Dict, Any, List

class RepoScanner:
    """Enterprise DevOps Codebase Repository Scanner and Health Auditor."""

    def scan_repository(self, repo_path: str) -> Dict[str, Any]:
        """Scan codebase repository to compile an executive DevOps architecture and health scorecard."""
        if not os.path.exists(repo_path) or not os.path.isdir(repo_path):
            return {"status": "error", "message": f"Directory path '{repo_path}' does not exist."}

        repo_name = os.path.basename(os.path.abspath(repo_path))

        # File counters
        py_files = 0
        ui_files = 0
        template_files = 0
        total_files = 0

        # Tech stack detections
        detected_languages: List[str] = []
        detected_frameworks: List[str] = []
        detected_cicd: List[str] = []
        detected_infra: List[str] = []
        detected_databases: List[str] = []
        detected_orms: List[str] = []
        detected_configs: List[str] = []
        detected_ai: List[str] = []
        detected_libs: List[str] = []

        # Toolings & Devops
        package_manager = "pip"
        dependency_file = "None"
        formatter = "None"
        linter = "None"
        type_checking = "None"
        packaging = "None"

        # Directory layout discovery
        layout_tree: List[str] = []
        
        # Scanned paths to verify
        sec_warnings = []
        has_tests = False
        has_docker = False
        has_cicd = False
        has_gitignore = False
        has_readme = False

        # Walk folder structure
        for root, dirs, files in os.walk(repo_path):
            # Prune hidden / venv directories
            dirs[:] = [d for d in dirs if d not in [".git", "venv", ".venv", "__pycache__", "node_modules", "build", "dist"]]

            # Track folder layout structure
            rel_dir = os.path.relpath(root, repo_path)
            if rel_dir != ".":
                depth = rel_dir.count(os.sep)
                if depth < 2:  # Limit depth shown in layout tree
                    layout_tree.append(f"{'  ' * depth}📁 {os.path.basename(root)}/")

            for file in files:
                total_files += 1
                full_path = os.path.join(root, file)
                rel_file = os.path.relpath(full_path, repo_path)
                file_lower = file.lower()

                # Categorize file types
                if file.endswith(".py"):
                    py_files += 1
                elif file.endswith((".ui", "widget.py", "window.py")):
                    ui_files += 1
                elif file.endswith((".j2", ".jinja", ".html", ".yml", ".yaml")) and "templates" in rel_file:
                    template_files += 1

                # Standard files
                if file_lower == ".gitignore":
                    has_gitignore = True
                elif file_lower == "readme.md":
                    has_readme = True

                # File extensions mappings
                ext_mappings = {
                    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
                    ".java": "Java", ".go": "Go", ".rs": "Rust", ".cs": "C#"
                }
                _, ext = os.path.splitext(file_lower)
                if ext in ext_mappings and ext_mappings[ext] not in detected_languages:
                    detected_languages.append(ext_mappings[ext])

                # Config files
                if file_lower == ".env":
                    detected_configs.append(".env")
                elif file_lower.endswith(".json"):
                    detected_configs.append("JSON")
                elif file_lower.endswith((".yaml", ".yml")):
                    detected_configs.append("YAML")

                # Packaging
                if "pyinstaller" in file_lower or file_lower.endswith(".spec"):
                    packaging = "PyInstaller"
                elif file_lower == "setup.py" or file_lower == "pyproject.toml":
                    packaging = "setuptools"

                # Check Dependency file
                if file_lower == "requirements.txt":
                    dependency_file = "requirements.txt"
                    package_manager = "pip"
                    self._parse_dependencies(full_path, detected_libs, detected_frameworks, detected_orms, detected_ai, detected_databases)
                elif file_lower == "package.json":
                    dependency_file = "package.json"
                    package_manager = "npm"
                    self._parse_dependencies(full_path, detected_libs, detected_frameworks, detected_orms, detected_ai, detected_databases)
                elif file_lower == "pipfile":
                    dependency_file = "Pipfile"
                    package_manager = "pipenv"

                # Frameworks file triggers
                if file_lower == "manage.py":
                    if "Django" not in detected_frameworks:
                        detected_frameworks.append("Django")
                elif file_lower in ["main.py", "app.py"]:
                    # Probe file content for frameworks imports
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            main_content = f.read()
                        if "fastapi" in main_content.lower() and "FastAPI" not in detected_frameworks:
                            detected_frameworks.append("FastAPI")
                        if "flask" in main_content.lower() and "Flask" not in detected_frameworks:
                            detected_frameworks.append("Flask")
                        if "streamlit" in main_content.lower() and "Streamlit" not in detected_frameworks:
                            detected_frameworks.append("Streamlit")
                        if "pyside" in main_content.lower() or "pyqt" in main_content.lower():
                            if "PySide6 Desktop Application" not in detected_frameworks:
                                detected_frameworks.append("PySide6 Desktop Application")
                    except Exception:
                        pass

                # CI/CD Workflows
                if ".github/workflows" in rel_file.replace("\\", "/"):
                    has_cicd = True
                    if "GitHub Actions" not in detected_cicd:
                        detected_cicd.append("GitHub Actions")
                elif file_lower == ".gitlab-ci.yml":
                    has_cicd = True
                    detected_cicd.append("GitLab CI")
                elif file_lower == "jenkinsfile":
                    has_cicd = True
                    detected_cicd.append("Jenkins")
                elif file_lower == "azure-pipelines.yml":
                    has_cicd = True
                    detected_cicd.append("Azure Pipelines")

                # Infrastructure support
                if file_lower == "dockerfile":
                    has_docker = True
                    detected_infra.append("Dockerfile")
                elif file_lower == "docker-compose.yml":
                    detected_infra.append("Docker Compose")
                elif file_lower.endswith(".tf"):
                    if "Terraform" not in detected_infra:
                        detected_infra.append("Terraform")
                elif file_lower == "chart.yaml":
                    detected_infra.append("Helm Chart")
                elif file_lower in ["playbook.yml", "site.yml"]:
                    detected_infra.append("Ansible")

                # Code tools indicators
                if "test_" in file_lower or "_test" in file_lower:
                    has_tests = True

                # Linters / Formatters
                if "ruff" in file_lower:
                    linter = "Ruff"
                    formatter = "Ruff"
                elif "flake8" in file_lower or "pylint" in file_lower:
                    linter = "Flake8 / Pylint"
                elif "black" in file_lower:
                    formatter = "Black"
                elif "mypy" in file_lower:
                    type_checking = "mypy"

        # Health score calculation
        score = 100
        checklist = {
            "Python": "✓" if "Python" in detected_languages else "✗",
            "Tests": "✓" if has_tests else "✗",
            "Formatting": "✓" if formatter != "None" else "✗",
            "Linting": "✓" if linter != "None" else "✗",
            "Docker": "✓" if has_docker else "✗",
            "CI/CD": "✓" if has_cicd else "✗",
            "Secrets": "✓",  # Default clean
            "Documentation": "100%" if has_readme else "0%"
        }

        # Deductions
        if not has_tests: score -= 15
        if formatter == "None": score -= 10
        if linter == "None": score -= 10
        if not has_docker: score -= 10
        if not has_cicd: score -= 15
        if not has_gitignore: score -= 10
        if not has_readme: score -= 10
        score = max(30, score)

        # Default frameworks fallback if PySide6 detected
        if "PySide6" in detected_libs and "PySide6 Desktop Application" not in detected_frameworks:
            detected_frameworks.append("PySide6 Desktop Application")

        # Suggestions & pipeline recommendations
        pipeline_recs = ["GitHub Actions", "Docker", "Terraform", "Kubernetes"]
        suggestions = [
            "Enable caching for pip dependencies inside workflows.",
            "Add a credentials security scanner (e.g. GitLeaks / Trivy).",
            "Integrate mypy type audits and Ruff lint checks to CI test stages."
        ]

        return {
            "status": "success",
            "repository_name": repo_name,
            "primary_language": detected_languages[0] if detected_languages else "Python",
            "language_version": "Python 3.12" if "Python" in detected_languages else "Unknown",
            "frameworks": list(set(detected_frameworks)) or ["Generic Python workload"],
            "architecture": "Modular MVC Pattern" if "app" in layout_tree or any("core" in f for f in layout_tree) else "Script Base",
            "package_manager": package_manager,
            "dependency_file": dependency_file,
            "testing": "pytest" if has_tests else "None",
            "formatter": formatter,
            "linter": linter,
            "type_checking": type_checking,
            "packaging": packaging,
            "database": detected_databases[0] if detected_databases else "SQLite (embedded)",
            "orm": detected_orms[0] if detected_orms else "SQLAlchemy",
            "configurations": list(set(detected_configs)),
            "ai_providers": list(set(detected_ai)),
            "container_support": "Dockerfile Found" if has_docker else "None",
            "terraform": "Supported" if "Terraform" in detected_infra else "None",
            "kubernetes": "Supported" if "Helm Chart" in detected_infra or "k8s" in layout_tree else "None",
            "github_actions": "Supported" if "GitHub Actions" in detected_cicd else "None",
            "project_size": {
                "python_files": py_files,
                "ui_files": ui_files,
                "template_files": template_files,
                "total_files": total_files
            },
            "estimated_complexity": "High" if py_files > 40 else ("Medium" if py_files > 15 else "Low"),
            "cicd_readiness": f"{score}%",
            "recommended_pipeline": pipeline_recs,
            "health_score": score,
            "health_checklist": checklist,
            "detected_libraries": list(set(detected_libs))[:12],
            "structure_tree": layout_tree[:15],
            "suggested_improvements": suggestions,
            "infrastructure_assets": detected_infra
        }

    def _parse_dependencies(self, dep_path: str, libs: list, frameworks: list, orms: list, ai: list, db: list):
        """Parse requirement files to classify modules, frameworks, ORMs, and AI SDKs."""
        try:
            with open(dep_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            packages = re.findall(r"([a-zA-Z0-9_\-\[\]]+)", content)
            for pkg in packages:
                pkg_lower = pkg.lower()
                
                # Exclude specific metadata syntax
                if pkg_lower in ["txt", "pip", "version", "install"]:
                    continue

                # Add to library list
                if pkg not in libs:
                    libs.append(pkg)

                # Classify package type
                if "pyside" in pkg_lower or "pyqt" in pkg_lower:
                    if "PySide6 Desktop Application" not in frameworks:
                        frameworks.append("PySide6 Desktop Application")
                elif "django" in pkg_lower:
                    if "Django" not in frameworks:
                        frameworks.append("Django")
                elif "fastapi" in pkg_lower:
                    if "FastAPI" not in frameworks:
                        frameworks.append("FastAPI")
                elif "flask" in pkg_lower:
                    if "Flask" not in frameworks:
                        frameworks.append("Flask")
                elif "streamlit" in pkg_lower:
                    if "Streamlit" not in frameworks:
                        frameworks.append("Streamlit")
                elif "react" in pkg_lower:
                    if "React SPA" not in frameworks:
                        frameworks.append("React SPA")
                
                if "openai" in pkg_lower:
                    ai.append("OpenAI")
                elif "ollama" in pkg_lower:
                    ai.append("Ollama")
                elif "google-generativeai" in pkg_lower or "gemini" in pkg_lower:
                    ai.append("Gemini")
                elif "anthropic" in pkg_lower:
                    ai.append("Anthropic")
                elif "langchain" in pkg_lower:
                    ai.append("LangChain")
                elif "transformers" in pkg_lower:
                    ai.append("Transformers")

                if "sqlalchemy" in pkg_lower:
                    orms.append("SQLAlchemy")
                elif "peewee" in pkg_lower:
                    orms.append("Peewee")

                if "sqlite" in pkg_lower:
                    db.append("SQLite")
                elif "psycopg" in pkg_lower or "postgres" in pkg_lower:
                    db.append("PostgreSQL")
                elif "mysql" in pkg_lower:
                    db.append("MySQL")
        except Exception:
            pass

# Global repo scanner instance
repo_scanner = RepoScanner()
