import os
from app.core.logger import logger
from app.modules.repo_scanner import repo_scanner

class ProjectAnalyzer:
    def __init__(self):
        pass

    def analyze_directory(self, path):
        """Analyze a local directory using the Enterprise DevOps scanner and return structured metadata and HTML report."""
        result = {
            "detected": False,
            "language": "Python",
            "framework": "Generic Python",
            "build_tool": "pip",
            "package_manager": "pip",
            "test_framework": "unittest",
            "details": [],
            "html_report": ""
        }

        if not os.path.exists(path) or not os.path.isdir(path):
            result["details"].append(f"Directory path '{path}' does not exist or is not readable.")
            return result

        try:
            # Delegate to our advanced RepoScanner
            scan_data = repo_scanner.scan_repository(path)
            if scan_data.get("status") == "error":
                result["details"].append(scan_data.get("message", "Scan failed."))
                return result

            result["detected"] = True
            result["language"] = scan_data.get("primary_language", "Python")
            result["framework"] = scan_data.get("frameworks", ["Generic Python"])[0]
            result["build_tool"] = scan_data.get("package_manager", "pip")
            result["package_manager"] = scan_data.get("package_manager", "pip")
            result["test_framework"] = scan_data.get("testing", "pytest")
            
            # Format high-end enterprise scorecard HTML
            repo_name = scan_data.get("repository_name", "Unknown-Repo")
            lang_ver = scan_data.get("language_version", "Python 3.12")
            frameworks_str = ", ".join(scan_data.get("frameworks", []))
            arch = scan_data.get("architecture", "Modular MVC")
            pkg_mgr = scan_data.get("package_manager", "pip")
            dep_file = scan_data.get("dependency_file", "requirements.txt")
            test_tool = scan_data.get("testing", "pytest")
            fmt = scan_data.get("formatter", "Black")
            lnt = scan_data.get("linter", "Ruff")
            tc = scan_data.get("type_checking", "mypy")
            pkg_tool = scan_data.get("packaging", "PyInstaller")
            db_tool = scan_data.get("database", "SQLite")
            orm_tool = scan_data.get("orm", "SQLAlchemy")
            
            configs = ", ".join(scan_data.get("configurations", [])) or "None"
            ai_list = ", ".join(scan_data.get("ai_providers", [])) or "None (Offline Mock)"
            
            docker_status = "✓ Found" if scan_data.get("container_support") != "None" else "✗ Not Found"
            tf_status = "✓ Supported" if scan_data.get("terraform") != "None" else "✗ Not Found"
            k8s_status = "✓ Supported" if scan_data.get("kubernetes") != "None" else "✗ Not Found"
            gha_status = "✓ Supported" if scan_data.get("github_actions") != "None" else "✗ Not Found"
            
            size = scan_data.get("project_size", {})
            py_cnt = size.get("python_files", 0)
            ui_cnt = size.get("ui_files", 0)
            tmpl_cnt = size.get("template_files", 0)
            total_cnt = size.get("total_files", 0)
            complexity = scan_data.get("estimated_complexity", "High")
            readiness = scan_data.get("cicd_readiness", "95%")
            pipeline_recs = " ➔ ".join(scan_data.get("recommended_pipeline", []))

            # Structure tree
            tree_html = "<br>".join([f"&nbsp;&nbsp;{node}" for node in scan_data.get("structure_tree", [])])

            # Health Checklist
            checklist = scan_data.get("health_checklist", {})
            checklist_html = ""
            for item, status in checklist.items():
                color = "#22c55e" if status == "✓" or "100%" in str(status) or "88%" in str(status) else "#ef4444"
                checklist_html += f"<tr><td>{item}</td><td style='color:{color}; font-weight:bold; text-align:right;'>{status}</td></tr>"

            # Recommendations / Improvements
            improvements_li = "".join([f"<li>{imp}</li>" for imp in scan_data.get("suggested_improvements", [])])

            # Detected libs
            libs_str = ", ".join(scan_data.get("detected_libraries", [])) or "None"

            # Construct layout HTML
            html = f"""
            <div style="font-family: 'Segoe UI', sans-serif; color: #f1f5f9; padding: 5px;">
                <h2 style="color: #38bdf8; margin-top: 0; border-bottom: 2px solid #1e293b; padding-bottom: 5px;">
                    Enterprise DevOps Audit Report: {repo_name}
                </h2>
                
                <table width="100%" cellpadding="6" style="border-collapse: collapse; margin-bottom: 15px;">
                    <tr style="background-color: #0f172a;">
                        <th align="left" style="color: #38bdf8;">Repository Analysis</th>
                        <th align="left" style="color: #38bdf8;">Specification Details</th>
                    </tr>
                    <tr><td><b>Primary Language</b></td><td style="color: #38bdf8;">{result['language']} ({lang_ver})</td></tr>
                    <tr style="background-color: #1e293b;"><td><b>Framework</b></td><td>{frameworks_str}</td></tr>
                    <tr><td><b>Architecture</b></td><td>{arch}</td></tr>
                    <tr style="background-color: #1e293b;"><td><b>Package Manager</b></td><td>{pkg_mgr} ({dep_file})</td></tr>
                    <tr><td><b>Testing Engine</b></td><td>{test_tool}</td></tr>
                    <tr style="background-color: #1e293b;"><td><b>Formatter / Linter</b></td><td>{fmt} / {lnt}</td></tr>
                    <tr><td><b>Type Check / Packaging</b></td><td>{tc} / {pkg_tool}</td></tr>
                    <tr style="background-color: #1e293b;"><td><b>Database / ORM</b></td><td>{db_tool} / {orm_tool}</td></tr>
                    <tr><td><b>Configurations</b></td><td>{configs}</td></tr>
                    <tr style="background-color: #1e293b;"><td><b>AI SDK Providers</b></td><td style="color: #a78bfa;">{ai_list}</td></tr>
                </table>

                <h3 style="color: #38bdf8; border-bottom: 1px solid #1e293b; padding-bottom: 3px;">Infrastructure Support Checklist</h3>
                <table width="100%" cellpadding="4" style="margin-bottom: 15px;">
                    <tr><td><b>Dockerfile</b></td><td style="color: #22c55e;">{docker_status}</td><td><b>Terraform IaC</b></td><td style="color: #22c55e;">{tf_status}</td></tr>
                    <tr><td><b>Kubernetes Orchestration</b></td><td style="color: #22c55e;">{k8s_status}</td><td><b>GitHub Actions Workflows</b></td><td style="color: #22c55e;">{gha_status}</td></tr>
                </table>

                <h3 style="color: #38bdf8; border-bottom: 1px solid #1e293b; padding-bottom: 3px;">Project Size & Metric Estimations</h3>
                <table width="100%" cellpadding="4" style="margin-bottom: 15px;">
                    <tr><td><b>Python Files</b></td><td>{py_cnt} files</td><td><b>UI Layout Files</b></td><td>{ui_cnt} files</td></tr>
                    <tr><td><b>Workflow Templates</b></td><td>{tmpl_cnt} files</td><td><b>Total Active Files</b></td><td>{total_cnt} files</td></tr>
                    <tr><td><b>Estimated Complexity</b></td><td style="color: #f59e0b; font-weight: bold;">{complexity}</td><td><b>CI/CD Readiness Score</b></td><td style="color: #22c55e; font-weight: bold;">{readiness}</td></tr>
                </table>

                <h3 style="color: #38bdf8; border-bottom: 1px solid #1e293b; padding-bottom: 3px;">Repository Structure Tree</h3>
                <div style="background-color: #0f172a; padding: 10px; border-radius: 6px; font-family: monospace; color: #a7f3d0; margin-bottom: 15px;">
                    {tree_html}
                </div>

                <h3 style="color: #38bdf8; border-bottom: 1px solid #1e293b; padding-bottom: 3px;">Detected Libraries & SDK Modules</h3>
                <p style="color: #cbd5e1; background-color: #1e293b; padding: 8px; border-radius: 6px; font-family: Consolas, monospace;">
                    {libs_str}
                </p>

                <table width="100%" cellpadding="6" style="margin-bottom: 15px;">
                    <tr>
                        <td width="50%" valign="top" style="background-color: #0f172a; border-radius: 6px; padding: 10px;">
                            <h4 style="color: #38bdf8; margin-top: 0; border-bottom: 1px solid #334155;">Repository Health Check Score: {scan_data.get('health_score', 92)}/100</h4>
                            <table width="100%" cellpadding="3" style="font-size: 12px; color: #cbd5e1;">
                                {checklist_html}
                            </table>
                        </td>
                        <td width="50%" valign="top" style="background-color: #0f172a; border-radius: 6px; padding: 10px;">
                            <h4 style="color: #38bdf8; margin-top: 0; border-bottom: 1px solid #334155;">DevOps Recommendations</h4>
                            <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #cbd5e1;">
                                {improvements_li}
                            </ul>
                        </td>
                    </tr>
                </table>

                <h3 style="color: #38bdf8; margin-top: 15px;">Recommended Target Pipeline</h3>
                <p style="background-color: #1e1b4b; border: 1px dashed #4f46e5; color: #818cf8; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; font-size: 14px;">
                    {pipeline_recs}
                </p>
            </div>
            """
            result["html_report"] = html

        except Exception as e:
            logger.error(f"Failed to compile enterprise scan report: {e}")
            result["details"].append(f"Report formatting failed: {e}")

        return result

# Global project analyzer instance
project_analyzer = ProjectAnalyzer()
