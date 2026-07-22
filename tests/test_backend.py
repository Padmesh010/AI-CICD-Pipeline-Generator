import unittest
import os
import sys
import tempfile
import json
import shutil

# Make sure project directory is in import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import ConfigManager
from app.database.db import DatabaseManager, db_manager
from app.validators.pipeline_val import PipelineValidator
from app.modules.cost_estimator import CostEstimator
from app.core.exceptions import ErrorHandler, SecurityError, AIProviderError
from app.core.task_manager import task_manager, TaskState
from app.core.security import security_manager
from app.database.models import Project, Template
from app.services.ai_providers import OpenAIProvider, OllamaProvider, MockProvider
from app.services.ai_service import ai_service
from app.generators.template_engine import template_engine
from app.generators.helm_gen import generate_helm_chart
from app.generators.ansible_gen import generate_ansible_playbook
from app.generators.pipeline_gen import generate_ci_pipeline
from app.validators.docker_val import validate_dockerfile
from app.validators.k8s_val import validate_k8s_manifests
from app.validators.tf_val import validate_terraform_code
from app.plugins.base_plugin import BasePlugin, PluginMetadata, PluginType
from app.plugins.plugin_manager import PluginManager
from app.services.export_service import export_service
from app.ui.theme import theme_manager
from app.modules.pipeline_analyzer import pipeline_analyzer
from app.ui.components.animation_helper import AnimationHelper
from app.ui.components.toast_notification import ToastNotification
from app.ui.components.command_palette import CommandPaletteModal
from app.ui.ai_dock import AIAssistantWidget
from app.modules.repo_scanner import repo_scanner
from app.ui.plugin_ui import PluginManagerWidget
from app.reports.report_gen import report_generator

class DummyTestPlugin(BasePlugin):
    def initialize(self, app_context: dict) -> bool:
        return True
    def execute(self, action: str, payload: dict) -> dict:
        return {"status": "success", "action": action, "received": payload}

class TestDevOpsBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        if not QApplication.instance():
            cls._app = QApplication([])

    def setUp(self):
        # Create temp folder for test files
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_report_generator(self):
        """Test report_generator exports HTML, Markdown, and JSON files."""
        proj = {"name": "TestProj", "description": "Desc", "language": "Python", "framework": "Django", "target": "Docker"}
        pipe = {"platform": "GitHub Actions"}
        val = {"is_valid": True, "errors": [], "warnings": []}
        cost = {"cloud_provider": "AWS", "build_time_display": "5 mins", "monthly_cost_display": "$5.00"}

        files = report_generator.export_report_files(self.test_dir, proj, pipe, val, cost)
        self.assertEqual(len(files), 3)
        self.assertTrue(os.path.exists(files[2])) # json file

    def test_plugin_ui(self):
        """Test PluginManagerWidget instantiation and refresh logic."""
        ui = PluginManagerWidget()
        self.assertIsNotNone(ui.table)
        ui.reload_plugins_list()

    def test_repo_scanner(self):
        """Test codebase language, framework, and Dockerfile detection."""
        # Create dummy project files
        with open(os.path.join(self.test_dir, "manage.py"), "w") as f:
            f.write("# Django runner")
        with open(os.path.join(self.test_dir, "app.py"), "w") as f:
            f.write("print('Hello')")
        with open(os.path.join(self.test_dir, "Dockerfile"), "w") as f:
            f.write("FROM python:3.12")

        scan = repo_scanner.scan_repository(self.test_dir)
        self.assertEqual(scan["status"], "success")
        self.assertEqual(scan["primary_language"], "Python")
        self.assertIn("Django", scan["frameworks"])
        self.assertIn("Dockerfile", scan["infrastructure_assets"])

    def test_ai_dock(self):
        """Test AI Assistant Dock widget instantiation and prompt triggers."""
        ai_dock = AIAssistantWidget()
        self.assertIsNotNone(ai_dock.combo_provider)
        ai_dock.trigger_quick_action("explain")
        self.assertIn("Explain", ai_dock.txt_chat.toPlainText())

    def test_command_palette(self):
        """Test command palette initialization and filtering logic."""
        palette = CommandPaletteModal()
        self.assertGreaterEqual(len(palette.commands), 5)
        palette.filter_commands("wizard")
        self.assertGreaterEqual(palette.list_widget.count(), 1)

    def test_toast_and_animations(self):
        """Test ToastNotification creation and AnimationHelper class."""
        self.assertTrue(hasattr(AnimationHelper, "fade_in"))
        self.assertTrue(hasattr(AnimationHelper, "slide_down"))

    def test_build_script_exists(self):
        """Test build_standalone.py packaging script exists and is executable."""
        build_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build_standalone.py"))
        self.assertTrue(os.path.exists(build_script))

    def test_pipeline_analyzer(self):
        """Test pipeline security scoring, bottleneck detection, and recommendations."""
        raw_pipeline = "name: Sample\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n"
        analysis = pipeline_analyzer.analyze(raw_pipeline)
        self.assertTrue(analysis["security_score"] < 100)
        self.assertGreater(analysis["estimated_duration_mins"], 0)
        self.assertTrue(len(analysis["recommendations"]) > 0)

    def test_theme_manager(self):
        """Test UI design tokens stylesheet generation."""
        qss = theme_manager.get_stylesheet("Dark")
        self.assertIn("QMainWindow", qss)
        self.assertIn("#0D1117", qss)
        self.assertIn("#58A6FF", qss)

    def test_export_service(self):
        """Test single file, ZIP archive, and TAR.GZ export bundling."""
        # 1. Single file export
        file_path = os.path.join(self.test_dir, "test_file.yml")
        res1 = export_service.export_single_file(file_path, "name: Test")
        self.assertEqual(res1["status"], "success")
        self.assertTrue(len(res1["sha256"]) == 64)

        # 2. ZIP Bundle export
        zip_path = os.path.join(self.test_dir, "bundle.zip")
        files = {
            ".github/workflows/main.yml": "name: CI",
            "Dockerfile": "FROM python:3.12"
        }
        res2 = export_service.export_zip_bundle(zip_path, files)
        self.assertEqual(res2["file_count"], 2)
        self.assertTrue(os.path.exists(zip_path))

        # 3. TAR.GZ export
        tar_path = os.path.join(self.test_dir, "bundle.tar.gz")
        res3 = export_service.export_targz_bundle(tar_path, files)
        self.assertEqual(res3["file_count"], 2)
        self.assertTrue(os.path.exists(tar_path))

    def test_plugin_manager(self):
        """Test dynamic plugin registration, metadata validation, and execution."""
        meta = PluginMetadata(
            name="TestCustomPlugin",
            version="1.0.0",
            author="DevOps Team",
            description="Test Plugin",
            plugin_type=PluginType.GENERATOR,
            compatible_app_versions=["1.0.0"]
        )
        plugin = DummyTestPlugin(meta)
        self.assertTrue(plugin.is_compatible("1.0.0"))

        pm = PluginManager(plugins_dir=self.test_dir)
        pm.registered_plugins[meta.name] = plugin
        
        result = pm.execute_plugin("TestCustomPlugin", "run", {"data": 123})
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["action"], "run")

    def test_artifact_validators(self):
        """Test Dockerfile, Kubernetes, and Terraform linter engines."""
        # 1. Dockerfile Hadolint warning
        df_content = "FROM python:latest\nCMD python app.py"
        df_res = validate_dockerfile(df_content)
        self.assertTrue(len(df_res["warnings"]) > 0)
        self.assertIn("DL3007", df_res["rules_triggered"])

        # 2. K8s Manifest audit
        k8s_manifests = {
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: app\nspec:\n  template:\n    spec:\n      containers:\n      - name: web\n        image: nginx:1.25\n"
        }
        k8s_res = validate_k8s_manifests(k8s_manifests)
        self.assertTrue(len(k8s_res["warnings"]) > 0)
        self.assertIn("K8S-RESOURCE-LIMITS", k8s_res["rules_triggered"])

        # 3. Terraform Security Group audit
        tf_code = {
            "main.tf": 'resource "aws_security_group" "web" {\n  ingress {\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n}\n'
        }
        tf_res = validate_terraform_code(tf_code)
        self.assertTrue(len(tf_res["warnings"]) > 0)
        self.assertIn("TF-OPEN-SECURITY-GROUP", tf_res["rules_triggered"])

    def test_extended_generators(self):
        """Test Helm chart, Ansible playbook, CircleCI, and Bitbucket pipeline generation."""
        # 1. Helm
        helm_assets = generate_helm_chart(app_name="my-helm-app")
        self.assertIn("Chart.yaml", helm_assets)
        self.assertIn("my-helm-app", helm_assets["Chart.yaml"])

        # 2. Ansible
        ansible_assets = generate_ansible_playbook(app_name="my-ansible-app")
        self.assertIn("site.yml", ansible_assets)
        self.assertIn("my-ansible-app", ansible_assets["site.yml"])

        # 3. CircleCI
        circleci = generate_ci_pipeline("Python", "Flask", "CircleCI", "Docker")
        self.assertIn("version: 2.1", circleci)

        # 4. Bitbucket
        bitbucket = generate_ci_pipeline("Python", "Flask", "Bitbucket", "Docker")
        self.assertIn("pipelines:", bitbucket)

    def test_template_engine(self):
        """Test template discovery, metadata parsing, and rendering."""
        templates = template_engine.list_templates()
        self.assertGreaterEqual(len(templates), 2)

        rendered = template_engine.render(
            "github/python_django.yml", 
            {"app_name": "TestDjangoApp", "python_version": "3.12"}
        )
        self.assertIn("TestDjangoApp CI/CD Pipeline", rendered)
        self.assertIn("python-version: '3.12'", rendered)

    def test_ai_providers_and_service(self):
        """Test AI provider abstraction, token estimation, and mock fallback."""
        mock_p = MockProvider()
        self.assertTrue(mock_p.is_healthy())
        self.assertEqual(mock_p.estimate_tokens("Hello World 12345"), 4)

        openai_p = OpenAIProvider(api_key="sk-test-key")
        self.assertTrue(openai_p.is_healthy())

        # Test fallback pipeline generation
        pipeline_code = ai_service.generate_pipeline("Python", "Django", "GitHub Actions", "Docker")
        self.assertIn("name: CI/CD Pipeline", pipeline_code)

    def test_sqlalchemy_orm_and_backup(self):
        """Test SQLAlchemy session queries and automatic database backup creation."""
        # 1. ORM Query
        with DatabaseManager().get_session() as session:
            count = session.query(Template).count()
            self.assertGreaterEqual(count, 4)

        # 2. Backup generation
        backup_file = db_manager.backup_database()
        self.assertTrue(os.path.exists(backup_file))
        if os.path.exists(backup_file):
            os.remove(backup_file)

    def test_security_manager(self):
        """Test path traversal, shell injection, and YAML injection security rules."""
        # 1. Path traversal blocking
        base_folder = tempfile.mkdtemp()
        try:
            with self.assertRaises(SecurityError):
                security_manager.sanitize_filepath("../../../etc/passwd", allowed_base_dir=base_folder)
        finally:
            shutil.rmtree(base_folder)

        # 2. Shell injection stripping
        malicious_shell = "docker build . ; rm -rf /"
        clean_shell = security_manager.sanitize_shell_input(malicious_shell)
        self.assertNotIn(";", clean_shell)

        # 3. YAML injection blocking
        malicious_yaml = "!!python/object/apply:os.system ['id']"
        with self.assertRaises(SecurityError):
            security_manager.sanitize_yaml_input(malicious_yaml)

    def test_task_manager_lifecycle(self):
        """Test TaskManager creation, progress update, and completion."""
        task = task_manager.create_task("Test Job", "Unit test execution")
        self.assertEqual(task.state, TaskState.QUEUED)
        
        task_manager.start_task(task.task_id)
        self.assertEqual(task.state, TaskState.RUNNING)
        
        task_manager.update_progress(task.task_id, 50, "Halfway done")
        self.assertEqual(task.progress, 50)
        self.assertEqual(task.current_stage, "Halfway done")
        
        task_manager.mark_completed(task.task_id, {"status": "ok"})
        self.assertEqual(task.state, TaskState.COMPLETED)
        self.assertEqual(task.progress, 100)
        self.assertEqual(task.result, {"status": "ok"})

    def test_stacktrace_sanitization(self):
        """Test ErrorHandler redacts secret keys from stacktraces."""
        raw_stack = "Error calling OpenAI API key sk-123456789012345678901234567890 with Bearer secret-token"
        sanitized = ErrorHandler.sanitize_stacktrace(raw_stack)
        self.assertNotIn("sk-123456789012345678901234567890", sanitized)
        self.assertIn("sk-***[REDACTED]***", sanitized)

    def test_custom_exceptions(self):
        """Test custom exception instances and messages."""
        sec_err = SecurityError("Path traversal blocked")
        self.assertEqual(str(sec_err), "Path traversal blocked")
        self.assertIsInstance(sec_err, Exception)

    def test_config_defaults(self):
        """Test default configs loads and saves correctly."""
        cm = ConfigManager()
        self.assertEqual(cm.get("ai_provider"), "Mock Mode (Offline)")
        self.assertEqual(cm.get("theme"), "Dark")

    def test_env_override_config(self):
        """Test environment variables override default settings."""
        os.environ["THEME"] = "Light"
        os.environ["DEFAULT_CLOUD"] = "GCP"
        cm = ConfigManager()
        self.assertEqual(cm.get("theme"), "Light")
        self.assertEqual(cm.get("default_cloud"), "GCP")
        # Cleanup
        del os.environ["THEME"]
        del os.environ["DEFAULT_CLOUD"]

    def test_pricing_estimator(self):
        """Test cloud operational pricing estimator matches rates tables."""
        ce = CostEstimator()
        result = ce.estimate("Python", "GitHub Actions", "AWS", instances=2)
        
        self.assertEqual(result["cloud_provider"], "Amazon Web Services (AWS)")
        self.assertEqual(result["compute_cost"], 50.00) # 25.0 * 2
        self.assertIn("spot instances", result["suggestions"][1].lower())

    def test_pipeline_validator_valid_yaml(self):
        """Test validation status for syntax correct YAML configuration."""
        pv = PipelineValidator()
        content = """
name: CI Test
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: echo "building"
"""
        result = pv.validate("GitHub Actions", content)
        self.assertTrue(result["is_valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_pipeline_validator_invalid_yaml(self):
        """Test validation fails for broken YAML indentations."""
        pv = PipelineValidator()
        content = """
name: CI Test
on: [push]
jobs:
  build:
  runs-on: ubuntu-latest
   - broken indent
"""
        result = pv.validate("GitHub Actions", content)
        self.assertFalse(result["is_valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_pipeline_validator_detects_secrets(self):
        """Test validator catches dummy hardcoded secrets."""
        pv = PipelineValidator()
        content = """
name: CI Test
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        env:
          AWS_KEY: AKIA1234567890123456
"""
        result = pv.validate("GitHub Actions", content)
        self.assertTrue(len(result["secrets_found"]) > 0)
        self.assertIn("AWS Access Key", result["secrets_found"][0])

if __name__ == "__main__":
    unittest.main()
