import re
from typing import Dict, Any, List

def validate_dockerfile(content: str) -> Dict[str, Any]:
    """Lint Dockerfile content against Hadolint and container security rules."""
    results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "rules_triggered": []
    }

    if not content or not content.strip():
        results["is_valid"] = False
        results["errors"].append("Dockerfile content is empty.")
        return results

    lines = content.splitlines()

    # Rule 1: DL3006 / DL3007 - Pin base image versions
    has_from = False
    for idx, line in enumerate(lines, 1):
        if line.strip().startswith("FROM"):
            has_from = True
            if ":latest" in line or ":" not in line.split()[1]:
                results["warnings"].append(
                    f"Line {idx} [DL3007]: Avoid using ':latest' or unpinned tags in FROM instruction '{line.strip()}'. Pin specific minor version."
                )
                results["rules_triggered"].append("DL3007")

    if not has_from:
        results["errors"].append("Missing required 'FROM' base image instruction.")

    # Rule 2: Container user check (Security)
    has_user = any(line.strip().startswith("USER") for line in lines)
    if not has_user:
        results["warnings"].append(
            "Security Warning: No 'USER' instruction found. Container may run as root."
        )
        results["rules_triggered"].append("SEC-ROOT-USER")

    # Rule 3: DL3009 - Clean apt-get cache
    for idx, line in enumerate(lines, 1):
        if "apt-get install" in line and "rm -rf /var/lib/apt/lists/*" not in content:
            results["warnings"].append(
                f"Line {idx} [DL3009]: Delete package list cache 'rm -rf /var/lib/apt/lists/*' after 'apt-get install'."
            )
            results["rules_triggered"].append("DL3009")
            break

    # Rule 4: DL3025 - Use JSON array notation for CMD / ENTRYPOINT
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("CMD") or stripped.startswith("ENTRYPOINT"):
            if "[" not in stripped or "]" not in stripped:
                results["warnings"].append(
                    f"Line {idx} [DL3025]: Use JSON array notation for {stripped.split()[0]} instruction e.g. CMD [\"executable\", \"param\"]."
                )
                results["rules_triggered"].append("DL3025")

    if results["errors"]:
        results["is_valid"] = False

    return results
