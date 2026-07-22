# AI CI/CD Pipeline Generator — Enterprise Architecture Guide

## 1. System Overview & Clean Layer Boundaries

The **AI CI/CD Pipeline Generator** is an enterprise-grade PySide6 desktop automation platform designed to design, validate, optimize, and explain CI/CD pipelines, container configurations, Infrastructure as Code (IaC), Helm charts, and Ansible playbooks.

```
+-----------------------------------------------------------------------+
|                         Presentation Layer                            |
|        (PySide6 UI: MainWindow, Wizard, Editor, Simulator, Logs)      |
+-----------------------------------+-----------------------------------+
                                    |
+-----------------------------------v-----------------------------------+
|                           Service Layer                               |
|       (AIService, ExportService, TaskManager, SecurityManager)        |
+-----------------+-----------------+-----------------+-----------------+
                  |                 |                 |
+-----------------v-+      +--------v--------+      +-v-----------------+
|  Generators Engine|      | Validator Suite |      | Plugin Architecture|
| (GHA, GitLab, etc)|      | (Hadolint, etc) |      | (BasePlugin, etc) |
+-----------------+-+      +--------+--------+      +-+-----------------+
                  |                 |                 |
+-----------------v-----------------v-----------------v-----------------+
|                    Database & Data Persistence Layer                  |
|             (SQLAlchemy ORM, SQLite DB, Automated Backups)            |
+-----------------------------------------------------------------------+
```

---

## 2. Database ORM Schema (`app/database/models.py`)

- **Projects (`projects`)**: Stores metadata regarding configured application workloads (`id`, `name`, `language`, `framework`, `target`, `created_at`).
- **Pipelines (`pipelines`)**: Stores generated CI/CD configurations (`id`, `project_id`, `platform`, `yaml_content`, `created_at`).
- **Templates (`templates`)**: Stores baseline Jinja2 and custom user templates (`id`, `name`, `platform`, `language`, `framework`, `content`, `is_custom`, `version`).
- **Audit Logs (`audit_logs`)**: Records security, export, generation, and database modification actions for compliance auditing.

---

## 3. Security Threat Model & Defense Specifications

1. **Path Traversal Protection (`app/core/security.py`)**: Sanitizes file paths using `pathlib.Path.resolve()`, enforcing strict boundary checks against `allowed_base_dir` and rejecting null bytes (`\x00`).
2. **Command Injection Prevention**: Strips dangerous shell metacharacters (`;`, `&&`, `||`, `` ` ``, `$`, `\n`) from execution strings.
3. **YAML Tag Injection Blocking**: Rejects dangerous tags (e.g. `!!python/object/apply`) to prevent arbitrary code execution during parsing.
4. **Secret Masking & Redaction**: Automatically redacts API keys, Bearer tokens, AWS signatures, and private keys from logs and UI stacktraces.

---

## 4. AI Provider Abstraction & Fallback Hierarchy

```
Configured Provider (OpenAI / Ollama / Azure / Anthropic / Gemini)
                   │ (If Timeout / API Error)
                   ▼
       Offline Rule-Based Generators (Jinja2 Templates)
```

---

## 5. Third-Party Plugin Architecture

Plugins are placed in `plugins/<plugin_name>/` containing `plugin.json` and `plugin.py`.

```json
{
  "name": "CustomK8sPlugin",
  "version": "1.0.0",
  "author": "DevOps Security Team",
  "description": "Custom K8s Policy Checks",
  "plugin_type": "VALIDATOR",
  "compatible_app_versions": ["1.0.0"]
}
```
