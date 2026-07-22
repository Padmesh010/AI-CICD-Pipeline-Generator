# AI CI/CD Pipeline Generator — User Manual & Operational Guide

## 1. Overview & Key Capabilities

The **AI CI/CD Pipeline Generator** allows software developers and DevOps engineers to generate production-grade CI/CD pipelines, Dockerfiles, Kubernetes manifests, Terraform IaC, Helm Charts, and Ansible playbooks.

### Features
- **Multi-Platform CI/CD Generation**: GitHub Actions, GitLab CI, Jenkins, Azure Pipelines, CircleCI, Bitbucket.
- **Infrastructure as Code (IaC)**: AWS/GCP/Azure Terraform HCL, Kubernetes Manifests, Helm Charts, Ansible Playbooks.
- **Enterprise Security & Linting**: Hadolint Dockerfile checks, Kubeconform schema checks, open security group detection, and secret scanning.
- **Interactive Simulator**: Animated runner step execution with simulated failure and automated rollback logs.
- **Release Bundling**: Export as raw files, `.zip` repository structures, or `.tar.gz` archives with SHA256 checksums.

---

## 2. Quick Start Guide

### Step 1: Launch the Application
Run `main.py` using Python 3.12+ or double-click `AI-CICD-Pipeline-Generator.exe`:
```bash
python main.py
```

### Step 2: Generate a Pipeline Workflow
1. Click **+ New Pipeline** on the dashboard.
2. Select your application language (e.g. `Python`, `Node.js`, `Java`, `Go`).
3. Select your application framework (e.g. `Django`, `FastAPI`, `React`, `Spring Boot`).
4. Select your target deployment platform (e.g. `GitHub Actions`, `GitLab CI`, `Jenkins`).
5. Choose your deployment target (e.g. `Docker Container`, `Kubernetes Cluster`, `AWS S3`).
6. Click **Generate Pipeline**.

---

## 3. Configuring AI Providers

Navigate to **Settings** to select your AI model backend:

1. **Mock Mode (Offline)**: Uses built-in rule-based templates. No internet or API keys required.
2. **OpenAI**: Enter your `sk-...` API key to use `gpt-4o-mini` or `gpt-4o`.
3. **Ollama (Local LLM)**: Connect to local Ollama instance at `http://localhost:11434` running `llama3` or `codellama`.
4. **Google Gemini / Anthropic / Azure OpenAI**: Enter your endpoint credentials and keys.

---

## 4. Exporting Release Bundles

Click **Export** in the Pipeline Editor to save generated assets:
- **Raw File**: Save single configuration file (`.yml`, `.tf`, `Dockerfile`).
- **ZIP Bundle**: Packages `.github/workflows/main.yml`, `Dockerfile`, `k8s/`, `terraform/` into a ready-to-commit `.zip` archive.
- **Checksum Verification**: View SHA256 hashes for release integrity.
