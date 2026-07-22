import os
import re
import tempfile
import pathlib
from typing import Optional
from app.core.exceptions import SecurityError
from app.core.logger import logger

class SecurityManager:
    """Enterprise security sanitizer and validation engine."""

    # Common secret patterns for masking
    SECRET_REGEXES = [
        (r"sk-[a-zA-Z0-9T3BlbkFJ]{20,}", "sk-***[REDACTED]***"),
        (r"AKIA[0-9A-Z]{16}", "AKIA***[REDACTED]***"),
        (r"ghp_[a-zA-Z0-9]{36}", "ghp_***[REDACTED]***"),
        (r"Bearer\s+[a-zA-Z0-9_\-\.]+", "Bearer ***[REDACTED]***"),
        (r"-----BEGIN [A-Z]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z]+ PRIVATE KEY-----", "*****BEGIN PRIVATE KEY [REDACTED]*****")
    ]

    @staticmethod
    def sanitize_filepath(filepath: str, allowed_base_dir: Optional[str] = None) -> str:
        """Sanitize and resolve file paths to prevent path traversal attacks."""
        if not filepath:
            raise SecurityError("Filepath cannot be empty.")

        # Check for null bytes
        if "\x00" in filepath:
            raise SecurityError("Path traversal attack detected: Null byte in path.")

        # Normalize path
        normalized = os.path.normpath(filepath)
        resolved_path = pathlib.Path(normalized).resolve()

        if allowed_base_dir:
            allowed_resolved = pathlib.Path(allowed_base_dir).resolve()
            try:
                resolved_path.relative_to(allowed_resolved)
            except ValueError:
                raise SecurityError(
                    f"Path traversal attack blocked: '{filepath}' attempts to access outside of '{allowed_base_dir}'."
                )

        return str(resolved_path)

    @staticmethod
    def sanitize_shell_input(cmd_input: str) -> str:
        """Sanitize input strings intended for shell execution to prevent command injection."""
        if not cmd_input:
            return ""

        # Remove dangerous shell metacharacters
        dangerous_chars = [";", "&&", "||", "`", "$", "(", ")", ">", "<", "\n", "\r", "\x00"]
        sanitized = cmd_input
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        return sanitized.strip()

    @staticmethod
    def sanitize_yaml_input(yaml_content: str) -> str:
        """Check for dangerous YAML tags that could trigger arbitrary code execution."""
        if not yaml_content:
            return ""

        # Reject python tag execution vulnerabilities e.g., !!python/object/apply
        forbidden_tags = ["!!python", "!!exec", "!!eval", "!!subprocess"]
        for tag in forbidden_tags:
            if tag in yaml_content.lower():
                raise SecurityError(f"YAML Injection blocked: Forbidden tag '{tag}' found in content.")

        return yaml_content

    @classmethod
    def mask_secrets(cls, text: str) -> str:
        """Mask API keys, private keys, and bearer tokens in text output."""
        if not text:
            return ""

        masked_text = text
        for pattern, replacement in cls.SECRET_REGEXES:
            masked_text = re.sub(pattern, replacement, masked_text)

        return masked_text

    @classmethod
    def scan_content_for_secrets(cls, text: str) -> list[str]:
        """Scan content to detect hardcoded secrets (returns list of matched patterns)."""
        if not text:
            return []
        
        findings = []
        for pattern, _ in cls.SECRET_REGEXES:
            matches = re.findall(pattern, text)
            if matches:
                # Store matched strings
                findings.extend(matches)
        return list(set(findings))

    @staticmethod
    def create_safe_temp_dir(prefix: str = "aicicd_") -> str:
        """Create a secure temporary directory inside the application sandbox."""
        sandbox_dir = os.path.join(
            os.path.expanduser("~"), ".gemini", "antigravity", "ai_cicd_pipeline_generator", "tmp"
        )
        os.makedirs(sandbox_dir, exist_ok=True)
        temp_path = tempfile.mkdtemp(prefix=prefix, dir=sandbox_dir)
        logger.info(f"Created safe temporary directory: {temp_path}")
        return temp_path

# Global security manager instance
security_manager = SecurityManager()
