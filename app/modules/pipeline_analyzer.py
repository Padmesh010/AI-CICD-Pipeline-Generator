import re
import yaml
from typing import Dict, Any, List
from app.core.logger import logger

class PipelineAnalyzer:
    """Comprehensive CI/CD Pipeline Analyzer & Optimization Engine."""

    def analyze(self, yaml_content: str, platform: str = "GitHub Actions") -> Dict[str, Any]:
        """Analyze pipeline YAML content for security, speed, bottlenecks, and automated fixes."""
        results = {
            "security_score": 100,
            "estimated_duration_mins": 5,
            "bottlenecks": [],
            "recommendations": [],
            "security_issues": [],
            "optimized_yaml": ""
        }

        if not yaml_content or not yaml_content.strip():
            results["security_score"] = 0
            results["estimated_duration_mins"] = 0
            results["security_issues"].append("Pipeline content is empty.")
            return results

        lines = yaml_content.splitlines()

        # 1. Security Score Deductions
        # Check for unpinned actions e.g. @v3, @master, @latest
        unpinned_actions = [line for line in lines if "uses:" in line and "@" in line and not re.search(r"@[a-f0-9]{40}", line)]
        if unpinned_actions:
            results["security_score"] -= 15
            results["security_issues"].append("Actions are pinned to mutable tags rather than immutable commit SHA digests.")
            results["recommendations"].append("Pin all third-party GitHub Actions to specific commit SHA hashes (e.g. uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11).")

        # Check for hardcoded secret tokens
        secret_matches = re.findall(r"(?:api[_-]?key|password|token)\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", yaml_content, re.IGNORECASE)
        if secret_matches:
            results["security_score"] -= 30
            results["security_issues"].append("Hardcoded credentials or API keys detected in pipeline script.")
            results["recommendations"].append("Migrate all sensitive keys to platform secrets (e.g. ${{ secrets.API_KEY }}).")

        # Check for SAST / Security Scanner stage
        if not any(token in yaml_content.lower() for token in ["trivy", "bandit", "sonarqube", "snyk", "codeql", "semgrep"]):
            results["security_score"] -= 20
            results["security_issues"].append("Missing Static Application Security Testing (SAST) or container vulnerability scanner.")
            results["recommendations"].append("Integrate SAST scanning (e.g., Trivy or CodeQL) prior to deployment stages.")

        # 2. Performance Bottlenecks & Caching
        has_cache = any(token in yaml_content.lower() for token in ["cache", "npm ci", "pip-cache", "actions/setup-python@v5"])
        if not has_cache:
            results["bottlenecks"].append("Package manager cache is disabled (pip / npm / gradle dependencies re-downloaded every run).")
            results["recommendations"].append("Enable dependency caching in setup actions e.g. 'cache: pip' or 'cache: npm'.")
            results["estimated_duration_mins"] += 4

        # Estimate duration based on step count
        step_count = yaml_content.count("- name:") + yaml_content.count("run:")
        results["estimated_duration_mins"] += max(1, step_count * 1.2)
        results["estimated_duration_mins"] = round(results["estimated_duration_mins"], 1)

        # 3. Generate Optimized YAML Preview
        results["optimized_yaml"] = self._generate_optimized_yaml(yaml_content, has_cache)

        # Clamp security score
        results["security_score"] = max(0, min(100, results["security_score"]))

        return results

    def _generate_optimized_yaml(self, raw_yaml: str, has_cache: bool) -> str:
        """Inject caching and best practice annotations into pipeline YAML."""
        optimized = raw_yaml
        if not has_cache and "actions/setup-python" in optimized:
            optimized = optimized.replace(
                "python-version: '3.12'",
                "python-version: '3.12'\n          cache: 'pip'"
            )
        return optimized

# Global analyzer instance
pipeline_analyzer = PipelineAnalyzer()
