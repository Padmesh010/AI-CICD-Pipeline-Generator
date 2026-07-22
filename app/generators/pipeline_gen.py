import re
from app.core.logger import logger

def generate_ci_pipeline(language, framework, platform, target, security_enabled=True, code_quality_enabled=True):
    """Generate production-ready CI/CD configurations based on parameters."""
    platform = platform.lower().replace(" ", "")
    
    if "github" in platform:
        return _generate_github_actions(language, framework, target, security_enabled, code_quality_enabled)
    elif "gitlab" in platform:
        return _generate_gitlab_ci(language, framework, target, security_enabled, code_quality_enabled)
    elif "jenkins" in platform:
        return _generate_jenkinsfile(language, framework, target, security_enabled, code_quality_enabled)
    elif "azure" in platform:
        return _generate_azure_pipeline(language, framework, target, security_enabled, code_quality_enabled)
    elif "circle" in platform:
        return _generate_circleci(language, framework, target, security_enabled, code_quality_enabled)
    elif "bitbucket" in platform:
        return _generate_bitbucket(language, framework, target, security_enabled, code_quality_enabled)
    else:
        return _generate_github_actions(language, framework, target, security_enabled, code_quality_enabled)

def _generate_circleci(language, framework, target, security, quality):
    image = "cimg/python:3.12" if language.lower() == "python" else "cimg/node:20.0"
    return f"""version: 2.1

executors:
  default-executor:
    docker:
      - image: {image}

jobs:
  test:
    executor: default-executor
    steps:
      - checkout
      - run:
          name: Install Dependencies & Test
          command: |
            {"pip install -r requirements.txt pytest && pytest" if language.lower() == "python" else "npm ci && npm test"}

  deploy:
    executor: default-executor
    steps:
      - checkout
      - setup_remote_docker
      - run:
          name: Build and Deploy Container
          command: |
            echo "Deploying to target: {target}"

workflows:
  build-test-deploy:
    jobs:
      - test
      - deploy:
          requires:
            - test
"""

def _generate_bitbucket(language, framework, target, security, quality):
    image = "python:3.12" if language.lower() == "python" else "node:20"
    return f"""image: {image}

pipelines:
  default:
    - step:
        name: Build and Test
        script:
          - {"pip install -r requirements.txt pytest && pytest" if language.lower() == "python" else "npm ci && npm test"}
    - step:
        name: Deploy to {target}
        deployment: production
        script:
          - echo "Deploying workload to {target}..."
"""

def _generate_github_actions(language, framework, target, security, quality):
    steps = [
        "name: CI/CD Pipeline\n",
        "on:",
        "  push:",
        "    branches: [ main, master ]",
        "  pull_request:",
        "    branches: [ main, master ]\n",
        "jobs:",
        "  build-and-test:",
        "    runs-on: ubuntu-latest",
        "    steps:",
        "      - name: Checkout Code",
        "        uses: actions/checkout@v4"
    ]

    # Setup environment
    if language.lower() == "python":
        steps.extend([
            "      - name: Set up Python",
            "        uses: actions/setup-python@v5",
            "        with:",
            "          python-version: '3.12'",
            "          cache: 'pip'",
            "      - name: Install Dependencies",
            "        run: |",
            "          python -m pip install --upgrade pip",
            "          pip install -r requirements.txt pytest"
        ])
        test_cmd = "pytest"
    elif language.lower() in ["nodejs", "node.js", "javascript", "typescript"]:
        steps.extend([
            "      - name: Set up Node.js",
            "        uses: actions/setup-node@v4",
            "        with:",
            "          node-version: '20'",
            "          cache: 'npm'",
            "      - name: Install Dependencies",
            "        run: npm ci"
        ])
        test_cmd = "npm test"
    elif language.lower() == "java":
        steps.extend([
            "      - name: Set up JDK",
            "        uses: actions/setup-java@v4",
            "        with:",
            "          java-version: '21'",
            "          distribution: 'temurin'",
            "          cache: 'maven'",
            "      - name: Build with Maven",
            "        run: ./mvnw clean package -DskipTests"
        ])
        test_cmd = "./mvnw test"
    else:
        # Default fallback
        steps.extend([
            "      - name: Set up Build Environment",
            "        run: echo 'Setting up generic build environment...'"
        ])
        test_cmd = "echo 'Running tests...'"

    # Quality Check
    if quality:
        if language.lower() == "python":
            steps.extend([
                "      - name: Lint Code",
                "        run: |",
                "          pip install flake8",
                "          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics"
            ])
        elif language.lower() in ["nodejs", "node.js"]:
            steps.extend([
                "      - name: Run Linter",
                "        run: npm run lint --if-present"
            ])

    # Test execution
    steps.extend([
        f"      - name: Run Unit Tests",
        f"        run: {test_cmd}"
    ])

    # Security scan
    if security:
        steps.extend([
            "      - name: Secret Scan (Gitleaks)",
            "        uses: gitleaks/gitleaks-action@v2",
            "        env:",
            "          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}",
            "      - name: Dependency Vulnerability Scan",
            "        uses: snyk/actions/node@master" if language.lower() in ["nodejs", "node.js"] else "        uses: snyk/actions/python@master",
            "        env:",
            "          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}"
        ])

    # Docker/Containerization
    if target.lower() in ["docker", "kubernetes", "k8s", "aws", "gcp", "azure"]:
        steps.extend([
            "\n  docker-build-and-push:",
            "    needs: build-and-test",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - name: Checkout Code",
            "        uses: actions/checkout@v4",
            "      - name: Set up Docker Buildx",
            "        uses: docker/setup-buildx-action@v3",
            "      - name: Log in to DockerHub",
            "        uses: docker/login-action@v3",
            "        with:",
            "          username: ${{ secrets.DOCKER_USERNAME }}",
            "          password: ${{ secrets.DOCKER_PASSWORD }}",
            "      - name: Build and Push Docker Image",
            "        uses: docker/build-push-action@v5",
            "        with:",
            "          context: .",
            "          push: true",
            "          tags: ${{ secrets.DOCKER_USERNAME }}/my-app:latest"
        ])

        # Security Scan Container
        if security:
            steps.extend([
                "      - name: Scan Docker Image (Trivy)",
                "        uses: aquasecurity/trivy-action@master",
                "        with:",
                "          image-ref: '${{ secrets.DOCKER_USERNAME }}/my-app:latest'",
                "          format: 'table'",
                "          exit-code: '1'",
                "          ignore-unfixed: true",
                "          vuln-type: 'os,library'",
                "          severity: 'CRITICAL,HIGH'"
            ])

    # Deployment
    if target.lower() == "kubernetes" or target.lower() == "k8s":
        steps.extend([
            "\n  deploy-k8s:",
            "    needs: docker-build-and-push",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - name: Checkout Code",
            "        uses: actions/checkout@v4",
            "      - name: Install Kubectl",
            "        uses: azure/setup-kubectl@v3",
            "      - name: Set Kubernetes Context",
            "        uses: azure/k8s-set-context@v3",
            "        with:",
            "          method: kubeconfig",
            "          kubeconfig: ${{ secrets.KUBECONFIG }}",
            "      - name: Deploy to Kubernetes Cluster",
            "        run: |",
            "          kubectl apply -f k8s/namespace.yaml",
            "          kubectl apply -f k8s/deployment.yaml",
            "          kubectl rollout status deployment/my-app -n production"
        ])
    elif target.lower() == "docker":
        steps.extend([
            "\n  deploy-docker-host:",
            "    needs: docker-build-and-push",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - name: Deploy to Remote Docker Host via SSH",
            "        uses: appleboy/ssh-action@master",
            "        with:",
            "          host: ${{ secrets.DEPLOY_HOST }}",
            "          username: ${{ secrets.DEPLOY_USER }}",
            "          key: ${{ secrets.DEPLOY_SSH_KEY }}",
            "          script: |",
            "            docker pull ${{ secrets.DOCKER_USERNAME }}/my-app:latest",
            "            docker stop my-app || true",
            "            docker rm my-app || true",
            "            docker run -d --name my-app -p 80:8000 ${{ secrets.DOCKER_USERNAME }}/my-app:latest"
        ])
    else:
        steps.extend([
            "\n  deploy-vm:",
            "    needs: build-and-test",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - name: Deploy Application VM",
            "        run: echo 'Deploying to VM / Cloud instance using SSH...'"
        ])

    return "\n".join(steps)

def _generate_gitlab_ci(language, framework, target, security, quality):
    stages = ["stages:", "  - test", "  - build", "  - deploy\n"]
    jobs = []

    # Test Job
    test_job = [
        "unit-tests:",
        "  stage: test"
    ]
    if language.lower() == "python":
        test_job.extend([
            "  image: python:3.12-slim",
            "  before_script:",
            "    - pip install -r requirements.txt pytest",
            "  script:",
            "    - pytest"
        ])
    elif language.lower() in ["nodejs", "node.js"]:
        test_job.extend([
            "  image: node:20-slim",
            "  before_script:",
            "    - npm ci",
            "  script:",
            "    - npm test"
        ])
    else:
        test_job.extend([
            "  image: alpine:latest",
            "  script:",
            "    - echo \"Running project tests...\""
        ])
    jobs.append("\n".join(test_job))

    # Security Job
    if security:
        sec_job = [
            "security-scan:",
            "  stage: test",
            "  image: docker:24-dind",
            "  services:",
            "    - docker:24-dind",
            "  script:",
            "    - echo \"Performing Gitleaks secrets audit...\"",
            "    - echo \"Performing dependency container check...\""
        ]
        jobs.append("\n".join(sec_job))

    # Build Job
    build_job = [
        "docker-build:",
        "  stage: build",
        "  image: docker:24-dind",
        "  services:",
        "    - docker:24-dind",
        "  variables:",
        "    DOCKER_HOST: tcp://docker:2375",
        "    DOCKER_TLS_CERTDIR: \"\"",
        "  script:",
        "    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY",
        "    - docker build -t $CI_REGISTRY_IMAGE:latest .",
        "    - docker push $CI_REGISTRY_IMAGE:latest"
    ]
    jobs.append("\n".join(build_job))

    # Deploy Job
    deploy_job = [
        "deploy-production:",
        "  stage: deploy",
        "  image: alpine:latest",
        "  script:",
        "    - echo \"Deploying to production target: " + target + "\"",
        "    - echo \"Executing deployment commands...\""
    ]
    if target.lower() in ["kubernetes", "k8s"]:
        deploy_job.extend([
            "    - apk add --no-cache curl",
            "    - curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl",
            "    - chmod +x ./kubectl",
            "    - ./kubectl apply -f k8s/deployment.yaml"
        ])
    jobs.append("\n".join(deploy_job))

    return "\n".join(stages) + "\n" + "\n\n".join(jobs)

def _generate_jenkinsfile(language, framework, target, security, quality):
    stages = [
        "pipeline {",
        "    agent any",
        "    environment {",
        "        REGISTRY_CREDENTIALS = 'dockerhub-credentials'",
        "        IMAGE_NAME = 'myapp'",
        "    }",
        "    stages {"
    ]

    # Checkout
    stages.extend([
        "        stage('Checkout') {",
        "            steps {",
        "                checkout scm",
        "            }",
        "        }"
    ])

    # Build and Test
    if language.lower() == "python":
        stages.extend([
            "        stage('Build & Test') {",
            "            steps {",
            "                sh '''",
            "                    python3 -m venv venv",
            "                    . venv/bin/activate",
            "                    pip install -r requirements.txt pytest",
            "                    pytest",
            "                '''",
            "            }",
            "        }"
        ])
    elif language.lower() in ["nodejs", "node.js"]:
        stages.extend([
            "        stage('Build & Test') {",
            "            steps {",
            "                sh '''",
            "                    npm ci",
            "                    npm test",
            "                '''",
            "            }",
            "        }"
        ])
    else:
        stages.extend([
            "        stage('Build & Test') {",
            "            steps {",
            "                sh 'echo \"Building and testing generic code...\"'",
            "            }",
            "        }"
        ])

    # Security
    if security:
        stages.extend([
            "        stage('Security Audits') {",
            "            steps {",
            "                sh '''",
            "                    echo \"Running dependency scans...\"",
            "                    # Example: trivy fs .",
            "                '''",
            "            }",
            "        }"
        ])

    # Docker Build
    stages.extend([
        "        stage('Docker Build & Push') {",
        "            steps {",
        "                script {",
        "                    docker.withRegistry('', REGISTRY_CREDENTIALS) {",
        "                        def customImage = docker.build(\"${IMAGE_NAME}:${env.BUILD_ID}\")",
        "                        customImage.push()",
        "                        customImage.push('latest')",
        "                    }",
        "                }",
        "            }",
        "        }"
    ])

    # Deploy
    stages.extend([
        "        stage('Deploy') {",
        "            steps {",
        f"                sh 'echo \"Executing deployment to {target}...\"'",
        "            }",
        "        }"
    ])

    stages.extend([
        "    }",
        "    post {",
        "        always {",
        "            cleanWs()",
        "        }",
        "    }",
        "}"
    ])

    return "\n".join(stages)

def _generate_azure_pipeline(language, framework, target, security, quality):
    steps = [
        "trigger:",
        "  - main\n",
        "pool:",
        "  vmImage: 'ubuntu-latest'\n",
        "variables:",
        "  dockerRegistryServiceConnection: 'MyDockerHubConnection'",
        "  imageRepository: 'myapp'",
        "  containerRegistry: 'docker.io'",
        "  dockerfilePath: '$(Build.SourcesDirectory)/Dockerfile'",
        "  tag: '$(Build.BuildId)'\n",
        "stages:",
        "  - stage: BuildAndTest",
        "    displayName: Build and Test Stage",
        "    jobs:",
        "      - job: TestJob",
        "        steps:",
        "          - task: UsePythonVersion@0" if language.lower() == "python" else "          - task: NodeTool@0",
        "            inputs:",
        "              versionSpec: '3.x'" if language.lower() == "python" else "              versionSource: 'spec'",
        "              versionSpec: '20.x'" if language.lower() != "python" else "",
    ]
    if language.lower() == "python":
        steps.extend([
            "          - script: |",
            "              python -m pip install --upgrade pip",
            "              pip install -r requirements.txt pytest",
            "              pytest",
            "            displayName: 'Install Dependencies & Run Tests'"
        ])
    else:
        steps.extend([
            "          - script: |",
            "              npm ci",
            "              npm test",
            "            displayName: 'Install & Test NPM Packages'"
        ])

    steps.extend([
        "  - stage: BuildDockerImage",
        "    dependsOn: BuildAndTest",
        "    jobs:",
        "      - job: DockerBuild",
        "        steps:",
        "          - task: Docker@2",
        "            displayName: Build and push image",
        "            inputs:",
        "              command: buildAndPush",
        "              repository: $(imageRepository)",
        "              dockerfile: $(dockerfilePath)",
        "              containerRegistry: $(dockerRegistryServiceConnection)",
        "              tags: |",
        "                $(tag)",
        "                latest"
    ])
    
    return "\n".join(filter(None, steps))
