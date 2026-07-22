import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import ConfigManager, AppConfig

class TestConfigEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_app_config_defaults(self):
        config = AppConfig()
        self.assertEqual(config.ai_provider, "Mock Mode (Offline)")
        self.assertEqual(config.theme, "Dark")

    def test_config_manager_creation(self):
        cm = ConfigManager()
        self.assertIsNotNone(cm.config)
        self.assertEqual(cm.get("ai_provider"), "Mock Mode (Offline)")

    def test_env_override_precedence(self):
        os.environ["THEME"] = "HighContrast"
        cm = ConfigManager()
        self.assertEqual(cm.get("theme"), "HighContrast")
        del os.environ["THEME"]
