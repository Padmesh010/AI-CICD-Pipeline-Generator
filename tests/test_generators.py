import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.generators.pipeline_gen import generate_ci_pipeline
from app.generators.docker_gen import generate_docker_assets
from app.generators.k8s_gen import generate_k8s_manifests, sanitize_k8s_name
from app.generators.tf_gen import generate_terraform_assets
from app.generators.helm_gen import generate_helm_chart
from app.generators.ansible_gen import generate_ansible_playbook

class TestGenerators(unittest.TestCase):
    def test_k8s_name_sanitization(self):
        """Test sanitizing resource names to DNS-1123 standards."""
        raw_name = "Inventory Management System"
        clean = sanitize_k8s_name(raw_name)
        self.assertEqual(clean, "inventory-management-system")

        manifests = generate_k8s_manifests(raw_name, "prod", 3, 8000, "app.local")
        self.assertIn("name: inventory-management-system", manifests["deployment.yaml"])

    def test_github_pipeline(self):
        res = generate_ci_pipeline("Python", "Django", "GitHub Actions", "Docker")
        self.assertIn("name: CI/CD Pipeline", res)

    def test_circleci_pipeline(self):
        res = generate_ci_pipeline("Python", "Django", "CircleCI", "Docker")
        self.assertIn("version: 2.1", res)

    def test_bitbucket_pipeline(self):
        res = generate_ci_pipeline("Python", "Django", "Bitbucket", "Docker")
        self.assertIn("pipelines:", res)

    def test_docker_generator(self):
        assets = generate_docker_assets("Python", "Django")
        self.assertIn("Dockerfile", assets)
        self.assertIn("docker-compose.yml", assets)

    def test_k8s_generator(self):
        assets = generate_k8s_manifests("my-app", "prod", 3, 8000, "app.local")
        self.assertIn("deployment.yaml", assets)
        self.assertIn("service.yaml", assets)

    def test_helm_generator(self):
        assets = generate_helm_chart("helm-app")
        self.assertIn("Chart.yaml", assets)
        self.assertIn("values.yaml", assets)

    def test_ansible_generator(self):
        assets = generate_ansible_playbook("ansible-app")
        self.assertIn("site.yml", assets)
        self.assertIn("inventory.ini", assets)
