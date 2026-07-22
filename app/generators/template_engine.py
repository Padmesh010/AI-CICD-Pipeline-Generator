import os
import re
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template as JinjaTemplate
from app.core.logger import logger
from app.core.exceptions import GeneratorError, ErrorHandler

class TemplateEngine:
    """Centralized Jinja2 template discovery and rendering engine."""

    def __init__(self, templates_dir: Optional[str] = None):
        if not templates_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            templates_dir = os.path.join(base_dir, "templates")

        self.templates_dir = templates_dir
        os.makedirs(self.templates_dir, exist_ok=True)

        try:
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.templates_dir),
                autoescape=False,
                trim_blocks=True,
                lstrip_blocks=True
            )
        except Exception as e:
            logger.error(f"Failed to initialize Jinja2 environment: {e}")
            self.jinja_env = None

    def list_templates(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        """Discover available templates under the templates/ directory."""
        results = []
        target_dir = os.path.join(self.templates_dir, category) if category else self.templates_dir
        if not os.path.exists(target_dir):
            return []

        for root, _, files in os.walk(target_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.templates_dir)
                category_name = os.path.dirname(rel_path) or "general"
                
                # Parse metadata header if present
                meta = self.extract_metadata(os.path.join(root, file))
                results.append({
                    "relative_path": rel_path.replace("\\", "/"),
                    "name": file,
                    "category": category_name,
                    "version": meta.get("version", "1.0.0"),
                    "platform": meta.get("platform", category_name.capitalize()),
                    "language": meta.get("language", "Generic")
                })

        return results

    def extract_metadata(self, filepath: str) -> Dict[str, str]:
        """Extract metadata tags from header comments (e.g. # Metadata: version=1.0.0, ...)."""
        meta = {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                first_lines = [f.readline() for _ in range(3)]

            for line in first_lines:
                if "Metadata:" in line:
                    match = re.search(r"Metadata:\s*(.*)", line)
                    if match:
                        pairs = match.group(1).split(",")
                        for pair in pairs:
                            if "=" in pair:
                                k, v = pair.split("=", 1)
                                meta[k.strip().lower()] = v.strip()
        except Exception:
            pass
        return meta

    def render(self, template_rel_path: str, context: Dict[str, Any]) -> str:
        """Render template with context variables using Jinja2."""
        template_rel_path = template_rel_path.replace("\\", "/")
        full_path = os.path.join(self.templates_dir, template_rel_path)

        if not os.path.exists(full_path):
            raise GeneratorError(f"Template file '{template_rel_path}' not found under '{self.templates_dir}'.")

        try:
            if self.jinja_env:
                template = self.jinja_env.get_template(template_rel_path)
                return template.render(**context)
            else:
                with open(full_path, "r", encoding="utf-8") as f:
                    raw = f.read()
                for k, v in context.items():
                    raw = raw.replace(f"{{{{ {k} }}}}", str(v))
                return raw
        except Exception as e:
            ErrorHandler.handle_exception(
                GeneratorError(f"Error rendering template '{template_rel_path}': {e}", e),
                show_dialog=False
            )
            raise e

# Global template engine instance
template_engine = TemplateEngine()
