import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import security_manager
from app.core.exceptions import SecurityError

class TestSecurityEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_path_traversal_prevention(self):
        with self.assertRaises(SecurityError):
            security_manager.sanitize_filepath("../../../etc/passwd", allowed_base_dir=self.test_dir)

        with self.assertRaises(SecurityError):
            security_manager.sanitize_filepath("test\x00file.txt")

    def test_shell_injection_stripping(self):
        malicious = "docker build . ; rm -rf /"
        cleaned = security_manager.sanitize_shell_input(malicious)
        self.assertNotIn(";", cleaned)

    def test_yaml_injection_blocking(self):
        malicious_yaml = "!!python/object/apply:os.system ['id']"
        with self.assertRaises(SecurityError):
            security_manager.sanitize_yaml_input(malicious_yaml)

    def test_secret_masking(self):
        raw_text = "API Key: sk-123456789012345678901234567890"
        masked = security_manager.mask_secrets(raw_text)
        self.assertNotIn("sk-123456789012345678901234567890", masked)
        self.assertIn("sk-***[REDACTED]***", masked)

    def test_secret_scanning(self):
        raw_text = "API Key: sk-123456789012345678901234567890"
        findings = security_manager.scan_content_for_secrets(raw_text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0], "sk-123456789012345678901234567890")
