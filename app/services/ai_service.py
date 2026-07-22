import json
import hashlib
from typing import Dict, Any, Optional
from app.core.config import config_manager
from app.core.logger import logger, ai_logger
from app.core.exceptions import AIProviderError, ErrorHandler
from app.services.ai_providers import (
    BaseAIProvider, MockProvider, OpenAIProvider, OllamaProvider, 
    AzureOpenAIProvider, AnthropicProvider, GeminiProvider
)
from app.generators.pipeline_gen import generate_ci_pipeline
from app.generators.docker_gen import generate_docker_assets
from app.generators.k8s_gen import generate_k8s_manifests
from app.generators.tf_gen import generate_terraform_assets

class AIService:
    """Orchestrator for AI provider completions, response caching, and offline fallback execution."""

    def __init__(self):
        self._cache: Dict[str, str] = {}
        self.mock_provider = MockProvider()

    def _get_provider(self) -> BaseAIProvider:
        """Instantiate configured AI provider instance based on application settings."""
        provider_name = config_manager.get("ai_provider", "Mock Mode (Offline)")
        api_key = config_manager.get("api_key", "")
        ollama_url = config_manager.get("ollama_url", "http://localhost:11434")
        ollama_model = config_manager.get("ollama_model", "llama3")

        if provider_name == "OpenAI":
            return OpenAIProvider(api_key=api_key)
        elif provider_name == "Ollama (Offline)":
            return OllamaProvider(endpoint_url=ollama_url, model_name=ollama_model)
        elif provider_name == "Azure OpenAI":
            endpoint = config_manager.get("azure_endpoint", "")
            deployment = config_manager.get("azure_deployment", "gpt-4")
            return AzureOpenAIProvider(api_key=api_key, endpoint_url=endpoint, deployment_name=deployment)
        elif provider_name == "Anthropic":
            return AnthropicProvider(api_key=api_key)
        elif provider_name == "Google Gemini":
            return GeminiProvider(api_key=api_key)
        else:
            return MockProvider()

    def _get_cache_key(self, system_prompt: str, user_prompt: str) -> str:
        """Generate MD5 hash key for caching prompt responses."""
        combined = f"{system_prompt}||{user_prompt}"
        return hashlib.md5(combined.encode("utf-8")).hexdigest()

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        return self.mock_provider.estimate_tokens(text)

    def generate_pipeline(self, language: str, framework: str, platform: str, target: str, security_enabled: bool = True, code_quality_enabled: bool = True) -> str:
        """Generate CI/CD pipeline code, using LLM if configured, else offline rules."""
        provider = self._get_provider()
        
        if isinstance(provider, MockProvider):
            return generate_ci_pipeline(language, framework, platform, target, security_enabled, code_quality_enabled)

        system_prompt = (
            "You are an expert DevOps and Platform Engineer. "
            "Generate ONLY valid code/syntax for a CI/CD configuration. "
            "Do not wrap your answer in markdown formatting like ```yaml or ```json. "
            "Output only the raw configuration content. "
            "Ensure it contains security scanning, building, testing, and deployment stages."
        )
        user_prompt = (
            f"Generate a {platform} pipeline for a {language} ({framework}) app. "
            f"Deployment Target: {target}. "
            f"Security Scanning: {'Enabled' if security_enabled else 'Disabled'}. "
            f"Linting/Code Quality: {'Enabled' if code_quality_enabled else 'Disabled'}."
        )

        cache_key = self._get_cache_key(system_prompt, user_prompt)
        if cache_key in self._cache:
            ai_logger.info("Retrieved pipeline completion from memory cache.")
            return self._cache[cache_key]

        try:
            result = provider.generate_completion(system_prompt, user_prompt)
            self._cache[cache_key] = result
            return result
        except Exception as e:
            ErrorHandler.handle_exception(
                AIProviderError(f"LLM pipeline generation failed: {e}", e), show_dialog=False
            )
            logger.warning("Falling back to offline rule-based pipeline generator.")
            return generate_ci_pipeline(language, framework, platform, target, security_enabled, code_quality_enabled)

    def generate_docker(self, language: str, framework: str) -> Dict[str, str]:
        """Generate Docker assets using LLM if configured, else offline rules."""
        provider = self._get_provider()

        if isinstance(provider, MockProvider):
            return generate_docker_assets(language, framework)

        system_prompt = (
            "You are an expert Cloud Engineer. Generate an optimized Dockerfile and docker-compose.yml. "
            "Format the response as a JSON object with keys 'Dockerfile', '.dockerignore', and 'docker-compose.yml'. "
            "Output ONLY valid JSON. Do not include markdown codeblocks or explanations."
        )
        user_prompt = f"Generate Docker configuration for a {language} application built with {framework}."

        try:
            raw_json = provider.generate_completion(system_prompt, user_prompt)
            raw_json = self._clean_json_response(raw_json)
            return json.loads(raw_json)
        except Exception as e:
            logger.warning(f"LLM Docker generation failed: {e}. Falling back to offline templates.")
            return generate_docker_assets(language, framework)

    def generate_k8s(self, app_name: str, namespace: str, replicas: int, port: int, ingress_host: str) -> Dict[str, str]:
        """Generate K8s manifests using LLM if configured, else offline rules."""
        provider = self._get_provider()

        if isinstance(provider, MockProvider):
            return generate_k8s_manifests(app_name, namespace, replicas, port, ingress_host)

        system_prompt = (
            "You are a Kubernetes administrator. Generate Deployment, Service, Ingress, HPA, and NetworkPolicy manifests. "
            "Format the response as a JSON object where keys are filenames (e.g. 'deployment.yaml') and values are the file contents. "
            "Output ONLY valid JSON. Do not include markdown codeblocks or explanations."
        )
        user_prompt = (
            f"Generate Kubernetes manifests for: Name: {app_name}, Namespace: {namespace}, "
            f"Replicas: {replicas}, Target Container Port: {port}, Ingress Host: {ingress_host}."
        )

        try:
            raw_json = provider.generate_completion(system_prompt, user_prompt)
            raw_json = self._clean_json_response(raw_json)
            return json.loads(raw_json)
        except Exception as e:
            logger.warning(f"LLM K8s generation failed: {e}. Falling back to offline manifests.")
            return generate_k8s_manifests(app_name, namespace, replicas, port, ingress_host)

    def generate_terraform(self, cloud_provider: str, region: str, environment: str) -> Dict[str, str]:
        """Generate Terraform assets using LLM if configured, else offline rules."""
        provider = self._get_provider()

        if isinstance(provider, MockProvider):
            return generate_terraform_assets(cloud_provider, region, environment)

        system_prompt = (
            "You are a Terraform developer. Generate providers.tf, variables.tf, main.tf, and outputs.tf. "
            "Format the response as a JSON object where keys are filenames (e.g. 'main.tf') and values are file contents. "
            "Output ONLY valid JSON. Do not include markdown codeblocks or explanations."
        )
        user_prompt = f"Generate {cloud_provider} Terraform scripts for region: {region}, environment: {environment}."

        try:
            raw_json = provider.generate_completion(system_prompt, user_prompt)
            raw_json = self._clean_json_response(raw_json)
            return json.loads(raw_json)
        except Exception as e:
            logger.warning(f"LLM Terraform generation failed: {e}. Falling back to offline configuration.")
            return generate_terraform_assets(cloud_provider, region, environment)

    def explain_stage(self, stage_name: str, code_snippet: str) -> str:
        """Provide detailed educational explanations for a pipeline stage."""
        provider = self._get_provider()

        if isinstance(provider, MockProvider):
            return (
                f"### Stage: {stage_name}\n\n"
                f"**Purpose:**\nExecutes automation tasks corresponding to {stage_name}.\n\n"
                f"**Key Commands Used:**\n```bash\n{code_snippet[:150]}...\n```\n\n"
                f"**Industry Best Practices:**\n"
                f"1. Pin actions and images to SHA digests or major/minor tags.\n"
                f"2. Keep the runner environment clean; run linting before expensive testing stages.\n"
                f"3. Secure secrets by injecting them strictly as environment variables, never hardcoding them."
            )

        system_prompt = (
            "You are a Senior DevOps mentor. Explain the given pipeline stage or code snippet. "
            "Use Markdown formatting. Include: 1) Purpose, 2) Step-by-step breakdown of commands, "
            "3) Industry best practices, and 4) Educational tips for beginners."
        )
        user_prompt = f"Explain the following stage: {stage_name}\nCode snippet:\n{code_snippet}"

        try:
            return provider.generate_completion(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"LLM Explanation failed: {e}")
            return f"Failed to load explanation from AI provider: {e}"

    def _clean_json_response(self, text: str) -> str:
        """Remove markdown JSON code fence structures if present."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

# Global AI service instance
ai_service = AIService()
