import re
from typing import Dict, Any

def validate_terraform_code(tf_files: Dict[str, str]) -> Dict[str, Any]:
    """Lint and validate Terraform HCL code blocks for structural errors and security risks."""
    results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "rules_triggered": []
    }

    for filename, content in tf_files.items():
        if not content or not content.strip():
            continue

        # 1. Structural matching brace validation
        open_braces = content.count("{")
        close_braces = content.count("}")
        if open_braces != close_braces:
            results["errors"].append(
                f"[{filename}]: Mismatched HCL braces found ({open_braces} open '{{' vs {close_braces} close '}}')."
            )

        lines = content.splitlines()

        # 2. Open Security Group rules check
        for idx, line in enumerate(lines, 1):
            if 'cidr_blocks = ["0.0.0.0/0"]' in line or "cidr_blocks = ['0.0.0.0/0']" in line:
                results["warnings"].append(
                    f"[{filename}:L{idx}] Security Warning: Open CIDR block '0.0.0.0/0' detected in security group rule."
                )
                results["rules_triggered"].append("TF-OPEN-SECURITY-GROUP")
                break

        # 3. Unencrypted S3 bucket check
        if "aws_s3_bucket" in content and "server_side_encryption_configuration" not in content:
            results["warnings"].append(
                f"[{filename}]: S3 Bucket defined without explicit server-side encryption configuration."
            )
            results["rules_triggered"].append("TF-S3-ENCRYPTION")

    if results["errors"]:
        results["is_valid"] = False

    return results
