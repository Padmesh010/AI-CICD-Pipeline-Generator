import os
from app.core.logger import logger

class ReportGenerator:
    def __init__(self):
        pass

    def generate_markdown(self, project_data, pipeline_data, validation_data, cost_data):
        """Generate a complete summary report in Markdown format."""
        suggestions_md = "\n".join([f"- {s}" for s in cost_data.get("suggestions", [])])
        secrets_md = "\n".join([f"- {s}" for s in validation_data.get("secrets_found", [])])
        if not secrets_md:
            secrets_md = "No secrets detected."

        md = f"""# DevOps CI/CD Pipeline Summary Report

## Project Details
- **Project Name:** {project_data.get("name", "Unnamed Project")}
- **Description:** {project_data.get("description", "No description provided.")}
- **Language / Framework:** {project_data.get("language")} / {project_data.get("framework")}
- **Target Platform:** {pipeline_data.get("platform")}
- **Deployment Target:** {project_data.get("target")}

---

## Static Validation Check
- **Overall Status:** {"PASS" if validation_data.get("is_valid") else "FAIL"}
- **Syntax Errors:** {len(validation_data.get("errors", []))} found.
- **Warnings / Recommendations:** {len(validation_data.get("warnings", []))} found.

### Secrets Scanner Report
{secrets_md}

---

## Cloud Cost & Build Time Estimation
- **Target Cloud Provider:** {cost_data.get("cloud_provider")}
- **Estimated Build Duration:** {cost_data.get("build_time_display")}
- **Estimated Monthly Cost:** {cost_data.get("monthly_cost_display")}

### Breakdowns:
- **Compute (Instances):** ${cost_data.get("compute_cost", 0.0):.2f}/mo
- **Database Service:** ${cost_data.get("database_cost", 0.0):.2f}/mo
- **Load Balancer:** ${cost_data.get("load_balancer_cost", 0.0):.2f}/mo
- **Storage:** ${cost_data.get("storage_cost", 0.0):.2f}/mo

---

## AI Platform Optimization Recommendations
{suggestions_md}

---
*Report generated automatically by AI CI/CD Pipeline Generator.*
"""
        return md

    def generate_html(self, project_data, pipeline_data, validation_data, cost_data):
        """Generate a beautiful, modern, styled HTML report."""
        suggestions_li = "".join([f"<li>{s}</li>" for s in cost_data.get("suggestions", [])])
        
        warnings = validation_data.get("warnings", [])
        warnings_li = "".join([f"<li class='warning-item'>{w}</li>" for w in warnings]) if warnings else "<li>No warnings found. Good job!</li>"
        
        errors = validation_data.get("errors", [])
        errors_li = "".join([f"<li class='error-item'>{e}</li>" for e in errors]) if errors else "<li>No syntax errors detected.</li>"

        secrets = validation_data.get("secrets_found", [])
        secrets_li = "".join([f"<li class='secret-item'>{s}</li>" for s in secrets]) if secrets else "<li>No hardcoded secrets found.</li>"

        status_class = "status-pass" if validation_data.get("is_valid") else "status-fail"
        status_text = "PASS" if validation_data.get("is_valid") else "FAIL"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Pipeline Generation Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            margin: 0;
            padding: 40px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #1e293b;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            border: 1px solid #334155;
        }}
        h1, h2, h3 {{
            color: #38bdf8;
        }}
        h1 {{
            border-bottom: 2px solid #334155;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: #0f172a;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #334155;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }}
        .status-pass {{
            background-color: #059669;
            color: #ecfdf5;
        }}
        .status-fail {{
            background-color: #dc2626;
            color: #fef2f2;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        .warning-item {{
            color: #fbbf24;
        }}
        .error-item {{
            color: #f87171;
        }}
        .secret-item {{
            color: #f87171;
            font-weight: bold;
        }}
        .price {{
            font-size: 24px;
            font-weight: bold;
            color: #34d399;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>CI/CD Pipeline Generation Report</h1>
        
        <div class="grid">
            <div class="card">
                <h2>Project Configuration</h2>
                <p><strong>Name:</strong> {project_data.get("name", "Unnamed Project")}</p>
                <p><strong>Description:</strong> {project_data.get("description", "No description provided.")}</p>
                <p><strong>Language:</strong> {project_data.get("language")} ({project_data.get("framework")})</p>
                <p><strong>CI Platform:</strong> {pipeline_data.get("platform")}</p>
                <p><strong>Deploy Target:</strong> {project_data.get("target")}</p>
            </div>
            
            <div class="card">
                <h2>Pipeline Integrity Status</h2>
                <p>Validation Check: <span class="status-badge {status_class}">{status_text}</span></p>
                <h3>Syntax Validation Errors:</h3>
                <ul>{errors_li}</ul>
            </div>
        </div>

        <div class="card" style="margin-bottom: 30px;">
            <h2>DevSecOps Audit Scans</h2>
            <h3>Secrets Scanner:</h3>
            <ul>{secrets_li}</ul>
            <h3>Quality / Static Warnings:</h3>
            <ul>{warnings_li}</ul>
        </div>

        <div class="grid">
            <div class="card">
                <h2>Financial & Resource Projections</h2>
                <p><strong>Target Infrastructure:</strong> {cost_data.get("cloud_provider")}</p>
                <p><strong>Estimated Build Time:</strong> {cost_data.get("build_time_display")}</p>
                <p><strong>Estimated Deploy Charges:</strong></p>
                <p class="price">{cost_data.get("monthly_cost_display")}</p>
                <ul>
                    <li>Compute: ${cost_data.get("compute_cost", 0.0):.2f}/mo</li>
                    <li>Database: ${cost_data.get("database_cost", 0.0):.2f}/mo</li>
                    <li>Balancer: ${cost_data.get("load_balancer_cost", 0.0):.2f}/mo</li>
                    <li>Storage: ${cost_data.get("storage_cost", 0.0):.2f}/mo</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>AI Architecture Suggestions</h2>
                <ul>{suggestions_li}</ul>
            </div>
        </div>
    </div>
</body>
</html>
"""
        return html

    def generate_json(self, project_data, pipeline_data, validation_data, cost_data):
        """Generate a complete summary report in JSON format."""
        import json
        return json.dumps({
            "report_type": "DevOps CI/CD Pipeline Summary",
            "project": project_data,
            "pipeline": pipeline_data,
            "validation": validation_data,
            "cost_estimation": cost_data
        }, indent=2)

    def export_report_files(self, base_path, project_data, pipeline_data, validation_data, cost_data):
        """Export Markdown, HTML, and JSON versions of the reports to disk."""
        try:
            os.makedirs(base_path, exist_ok=True)
            
            md_content = self.generate_markdown(project_data, pipeline_data, validation_data, cost_data)
            md_file = os.path.join(base_path, "pipeline_report.md")
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(md_content)
                
            html_content = self.generate_html(project_data, pipeline_data, validation_data, cost_data)
            html_file = os.path.join(base_path, "pipeline_report.html")
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            json_content = self.generate_json(project_data, pipeline_data, validation_data, cost_data)
            json_file = os.path.join(base_path, "pipeline_report.json")
            with open(json_file, "w", encoding="utf-8") as f:
                f.write(json_content)
                
            logger.info(f"Report exported successfully to {base_path}")
            return md_file, html_file, json_file
        except Exception as e:
            logger.error(f"Failed to export reports: {e}")
            raise e

# Global report generator instance
report_generator = ReportGenerator()
