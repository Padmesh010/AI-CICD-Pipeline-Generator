import re
import yaml
from typing import Dict, Any
from app.core.logger import logger
from app.validators.docker_val import validate_dockerfile
from app.validators.k8s_val import validate_k8s_manifests
from app.validators.tf_val import validate_terraform_code

class PipelineValidator:
    def __init__(self):
        # Common secret patterns
        self.secret_patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "AWS Secret Key": r"([^A-Za-z0-9+/]|^)[A-Za-z0-9+/]{40}([^A-Za-z0-9+/]|$)",
            "GitHub Personal Access Token": r"ghp_[a-zA-Z0-9]{36}",
            "Slack Webhook": r"https://hooks\.slack\.com/services/T[A-Z0-9_]+/B[A-Z0-9_]+/[A-Za-z0-9_]+",
            "Generic Private Key": r"-----BEGIN [A-Z]+ PRIVATE KEY-----",
            "Generic API Key": r"api[_-]?key\s*=\s*['\"][a-zA-Z0-9]{16,64}['\"]"
        }

    def validate_workspace_assets(self, assets: Dict[str, Any]) -> Dict[str, Any]:
        """Unified validation check for pipeline, Docker, Kubernetes, and Terraform assets."""
        overall_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "secrets_found": []
        }

        # 1. Pipeline validation
        if "pipeline" in assets and "platform" in assets:
            p_res = self.validate(assets["platform"], assets["pipeline"])
            overall_results["errors"].extend(p_res.get("errors", []))
            overall_results["warnings"].extend(p_res.get("warnings", []))
            overall_results["secrets_found"].extend(p_res.get("secrets_found", []))

        # 2. Dockerfile validation
        if "Dockerfile" in assets:
            d_res = validate_dockerfile(assets["Dockerfile"])
            overall_results["errors"].extend(d_res.get("errors", []))
            overall_results["warnings"].extend(d_res.get("warnings", []))

        # 3. K8s validation
        if "k8s_manifests" in assets and isinstance(assets["k8s_manifests"], dict):
            k_res = validate_k8s_manifests(assets["k8s_manifests"])
            overall_results["errors"].extend(k_res.get("errors", []))
            overall_results["warnings"].extend(k_res.get("warnings", []))

        # 4. Terraform validation
        if "terraform" in assets and isinstance(assets["terraform"], dict):
            t_res = validate_terraform_code(assets["terraform"])
            overall_results["errors"].extend(t_res.get("errors", []))
            overall_results["warnings"].extend(t_res.get("warnings", []))

        if overall_results["errors"]:
            overall_results["is_valid"] = False

        return overall_results

    def validate(self, platform, content):
        """Validate pipeline content against syntax, secrets, and logical standards."""
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "secrets_found": []
        }

        if not content or not content.strip():
            results["is_valid"] = False
            results["errors"].append("Pipeline content is empty.")
            return results

        # 1. Scan for secrets (applies to all formats)
        self._scan_secrets(content, results)

        # 2. Syntax Validation based on platform
        platform_lower = platform.lower()
        if "github" in platform_lower or "gitlab" in platform_lower or "azure" in platform_lower:
            self._validate_yaml(content, results)
        elif "jenkins" in platform_lower:
            self._validate_jenkinsfile_structure(content, results)

        # 3. Logics & Best practices
        self._check_best_practices(platform_lower, content, results)

        if results["errors"]:
            results["is_valid"] = False

        return results

    def _scan_secrets(self, content, results):
        """Scan each line for hardcoded API keys, secrets, or certificates."""
        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            # Skip comments
            if line.strip().startswith("#") or line.strip().startswith("//"):
                continue
            for name, pattern in self.secret_patterns.items():
                if re.search(pattern, line):
                    match_info = f"Possible {name} detected on line {idx}."
                    results["secrets_found"].append(match_info)
                    results["warnings"].append(f"Security Alert: {match_info} Use environment variables or credentials vaults.")

    def _validate_yaml(self, content, results):
        """Parse with PyYAML to confirm correct format."""
        try:
            parsed = yaml.safe_load(content)
            if not isinstance(parsed, dict):
                results["errors"].append("Invalid YAML structure. Top level must be a mapping dictionary.")
                return
            
            # Simple logical structure validation
            if "on" in parsed or "jobs" in parsed: # GitHub Actions
                if "jobs" in parsed:
                    jobs = parsed["jobs"]
                    if not isinstance(jobs, dict):
                        results["errors"].append("GitHub Actions: 'jobs' section must be a dictionary mapping job IDs to definitions.")
                    else:
                        # Check dependency loops
                        job_ids = list(jobs.keys())
                        for job_id, job_def in jobs.items():
                            if not isinstance(job_def, dict):
                                results["errors"].append(f"Job '{job_id}' has an invalid structure or indentation.")
                                continue
                            needs = job_def.get("needs", [])
                            if isinstance(needs, str):
                                needs = [needs]
                            for dep in needs:
                                if dep not in job_ids:
                                    results["errors"].append(f"Job '{job_id}' depends on non-existent job '{dep}'.")
        except yaml.YAMLError as exc:
            err_msg = f"YAML Syntax Error: {exc}"
            results["errors"].append(err_msg)

    def _validate_jenkinsfile_structure(self, content, results):
        """Verify basic structure of Jenkins declarative pipelines."""
        stripped = content.replace(" ", "").replace("\n", "")
        
        # Check basic block matchings
        if "pipeline{" not in stripped:
            results["errors"].append("Jenkinsfile: Missing top-level 'pipeline' block for declarative syntax.")
        if "agentany" not in stripped and "agent{" not in stripped:
            results["warnings"].append("Jenkinsfile: Declarative pipeline should define a global 'agent'.")
        if "stages{" not in stripped:
            results["errors"].append("Jenkinsfile: Missing 'stages' container block.")

    def _check_best_practices(self, platform, content, results):
        """Assess configuration files against general design/security rules."""
        # Check for unpinned image versions
        if ":latest" in content:
            results["warnings"].append("Best Practice: Avoid utilizing ':latest' tags for docker images. Pin specific minor versions (e.g. node:20-alpine) for reproducible builds.")

        # Check for checkout step
        if "actions/checkout" not in content and "checkout scm" not in content and "git clone" not in content:
            results["warnings"].append("Potential Bug: The pipeline does not appear to checkout the source repository code.")

        # Check for secret usage
        if "password" in content.lower() or "token" in content.lower():
            if "${{" not in content and "$" not in content:
                results["warnings"].append("Security: Hardcoded strings containing the words 'password' or 'token' found. Use secrets manager references.")

# Global validator instance
pipeline_validator = PipelineValidator()
