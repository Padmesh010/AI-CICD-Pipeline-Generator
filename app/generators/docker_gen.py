import os
from app.core.logger import logger

def generate_docker_assets(language, framework):
    """Generate optimized Dockerfile, .dockerignore, and docker-compose.yml contents."""
    lang = language.lower()
    fw = framework.lower()
    
    dockerfile = _generate_dockerfile(lang, fw)
    dockerignore = _generate_dockerignore(lang)
    compose = _generate_compose(lang, fw)
    
    return {
        "Dockerfile": dockerfile,
        ".dockerignore": dockerignore,
        "docker-compose.yml": compose
    }

def _generate_dockerfile(lang, fw):
    if lang == "python":
        cmd_str = 'CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]' if fw == "django" else 'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]'
        return f"""# Multi-stage build for Python application
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.12-slim AS runner

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

{cmd_str}
"""
    elif lang in ["nodejs", "node.js", "javascript", "typescript"]:
        if fw == "react" or fw == "vue" or fw == "angular":
            return f"""# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production server stage
FROM nginx:1.25-alpine
COPY --from=builder /app/build /usr/share/nginx/html
# Custom default config to handle SPA routing if necessary
# COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
        else:
            return f"""# Node.js API Service
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# Final stage
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

EXPOSE 3000
CMD ["node", "index.js"]
"""
    elif lang == "java":
        return """# Gradle/Maven Multi-stage build for Spring Boot
FROM maven:3.9.6-eclipse-temurin-21-alpine AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn clean package -DskipTests

# Run stage
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
"""
    else:
        # Fallback default
        return """# Generic Dockerfile
FROM alpine:latest
WORKDIR /app
COPY . .
RUN apk add --no-cache bash
EXPOSE 8080
CMD ["echo", "Running container application..."]
"""

def _generate_dockerignore(lang):
    ignores = [
        ".git",
        ".gitignore",
        "Dockerfile",
        "docker-compose.yml",
        "README.md",
        "*.log",
        "__pycache__/",
        "*.pyc",
        "venv/",
        ".env",
        "node_modules/",
        "build/",
        "dist/",
        "target/",
        ".terraform/",
        "*.tfstate*"
    ]
    return "\n".join(ignores)

def _generate_compose(lang, fw):
    port = "8000"
    if lang in ["nodejs", "node.js"]:
        port = "3000" if fw not in ["react", "vue", "angular"] else "80"
    elif lang == "java":
        port = "8080"
        
    return f"""version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "{port}:{port}"
    environment:
      - NODE_ENV=production
      - PYTHONUNBUFFERED=1
    restart: always

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: db_user
      POSTGRES_PASSWORD: db_password
      POSTGRES_DB: main_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
"""
