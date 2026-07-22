# AI CI/CD Pipeline Generator

An enterprise-grade desktop DevOps automation platform that designs, validates, simulates, and optimizes CI/CD pipelines, Docker configs, Kubernetes manifests, and Terraform IaC using Python 3.12+ and PySide6.

## Feature Overview

1. **Dashboard Overview**: Summary stats, saved workloads, and security advice.
2. **Project Wizard**: Multi-step config mapping for programming languages and platforms.
3. **Tabbed Workspace Editor**: Text editor with customized QSyntaxHighlighter for YAML, Dockerfile, and Terraform syntax.
4. **DevOps AI Tutor**: Select code segments and trigger interactive, context-aware LLM explanations.
5. **Execution Simulator**: Multi-stage pipeline execution visualizer with console log simulator and deployment rollbacks.
6. **Repository Scanner**: Folder scan to auto-detect languages/frameworks.
7. **Infrastructure Generators**: Dockerfile, docker-compose, Kubernetes resources (Deployment, Service, Ingress, NetworkPolicies, configmaps), and Terraform IaC.
8. **Static Validator**: Syntax, circular dependency, and hardcoded secret scanning.
9. **Cost Estimator**: Projections for build duration and cloud provider charges.

---

## Directory Structure

```text
ai-cicd-pipeline-generator/
│
├── app/
│   ├── core/              # Config management, Fernet encryption, Logger
│   ├── database/          # SQLite database schema, template seeding
│   ├── generators/        # Pipeline templates, Docker, K8s, Terraform
│   ├── services/          # OpenAI and Ollama connection interfaces
│   ├── validators/        # YAML parsing, Gitleaks secrets scanner
│   ├── modules/           # Timeline simulator, Cost estimator, Code scanner
│   ├── reports/           # HTML and Markdown report exporters
│   └── ui/                # PySide6 widgets, custom QSS styling
│
├── tests/                 # Unittests suite
│
├── main.py                # App bootstrapper entry point
├── requirements.txt       # App dependencies list
└── README.md
```

---

## Installation & Setup

### Prerequisites
- Python 3.12+ installed.

### Setup Steps
1. Navigate to the project directory:
   ```powershell
   cd C:\Users\admin\.gemini\antigravity\scratch\ai-cicd-pipeline-generator
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Run unit tests to verify:
   ```powershell
   python -m unittest discover -s tests
   ```

4. Launch the application:
   ```powershell
   python main.py
   ```

---

## Configuration & Offline Capability
- The application stores preferences inside `%USERPROFILE%\.gemini\antigravity\ai_cicd_pipeline_generator\config.json`.
- Sensitive details (like OpenAI API keys) are **Fernet encrypted** before writing to disk using a machine key stored in `secret.key`.
- If no internet connection is present, the application automatically uses offline templates and rule-based compilers without freezing or crashing.
