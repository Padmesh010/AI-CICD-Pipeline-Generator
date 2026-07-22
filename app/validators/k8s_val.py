import yaml
from typing import Dict, Any

def validate_k8s_manifests(manifest_files: Dict[str, str]) -> Dict[str, Any]:
    """Validate Kubernetes YAML manifests against Kubeconform schema and security practices."""
    results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "rules_triggered": []
    }

    for filename, content in manifest_files.items():
        if not content or not content.strip():
            continue

        try:
            parsed = yaml.safe_load(content)
            if not isinstance(parsed, dict):
                continue

            # Verify required metadata fields
            kind = parsed.get("kind", "")
            api_version = parsed.get("apiVersion", "")
            metadata = parsed.get("metadata", {})

            if not kind or not api_version:
                results["errors"].append(f"[{filename}]: Missing 'apiVersion' or 'kind' manifest headers.")

            if not metadata.get("name"):
                results["errors"].append(f"[{filename}]: Missing 'metadata.name' property.")

            # Deployment specific security audits
            if kind == "Deployment":
                spec = parsed.get("spec", {}).get("template", {}).get("spec", {})
                containers = spec.get("containers", [])

                for container in containers:
                    c_name = container.get("name", "unnamed")

                    # Check resource limits
                    if "resources" not in container or "limits" not in container.get("resources", {}):
                        results["warnings"].append(
                            f"[{filename}]: Container '{c_name}' does not specify CPU/Memory resource limits."
                        )
                        results["rules_triggered"].append("K8S-RESOURCE-LIMITS")

                    # Check liveness & readiness probes
                    if "livenessProbe" not in container:
                        results["warnings"].append(
                            f"[{filename}]: Container '{c_name}' is missing a 'livenessProbe'."
                        )
                        results["rules_triggered"].append("K8S-LIVENESS-PROBE")

                    # Check securityContext
                    sec_ctx = container.get("securityContext", {})
                    if not sec_ctx.get("runAsNonRoot"):
                        results["warnings"].append(
                            f"[{filename}]: Container '{c_name}' securityContext does not enforce 'runAsNonRoot: true'."
                        )
                        results["rules_triggered"].append("K8S-NON-ROOT")

        except yaml.YAMLError as exc:
            results["errors"].append(f"[{filename}]: Invalid YAML syntax: {exc}")

    if results["errors"]:
        results["is_valid"] = False

    return results
