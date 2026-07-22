import os
import json
import yaml
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from app.core.logger import logger
from app.core.exceptions import ConfigurationError, ErrorHandler

@dataclass
class AppConfig:
    ai_provider: str = "Mock Mode (Offline)"
    api_key: str = ""
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    theme: str = "Dark"
    default_cloud: str = "AWS"
    preferred_platform: str = "GitHub Actions"
    export_dir: str = ""
    log_level: str = "INFO"
    auto_save: bool = True

class ConfigManager:
    """Multi-format configuration engine with Fernet credential encryption and source merging."""

    def __init__(self):
        self.app_dir = os.path.join(
            os.path.expanduser("~"), ".gemini", "antigravity", "ai_cicd_pipeline_generator"
        )
        os.makedirs(self.app_dir, exist_ok=True)
        
        self.config_json_path = os.path.join(self.app_dir, "config.json")
        self.config_yaml_path = os.path.join(self.app_dir, "config.yaml")
        self.key_path = os.path.join(self.app_dir, "secret.key")
        self.env_path = os.path.join(os.getcwd(), ".env")

        self.fernet = self._init_crypto()
        self.config_data: Dict[str, Any] = {}
        self.app_config = AppConfig()
        self.config = {}
        self.config = self.load_config()

    def _init_crypto(self) -> Fernet:
        """Initialize or load the encryption key for sensitive settings."""
        try:
            if not os.path.exists(self.key_path):
                key = Fernet.generate_key()
                with open(self.key_path, "wb") as key_file:
                    key_file.write(key)
            else:
                with open(self.key_path, "rb") as key_file:
                    key = key_file.read()
            return Fernet(key)
        except Exception as e:
            ErrorHandler.handle_exception(
                ConfigurationError("Failed to initialize Fernet cryptography key.", e),
                show_dialog=False
            )
            fallback_key = b"5t_K8-K1t6Wd7k9VwQJ_X931rG-e2_V0jY7gM-hGvFk="
            return Fernet(fallback_key)

    def load_config(self) -> Dict[str, Any]:
        """Load and merge configuration settings across defaults, JSON, YAML, and .env."""
        # 1. Defaults baseline
        merged = asdict(AppConfig())

        # 2. Merge JSON configuration
        if os.path.exists(self.config_json_path):
            try:
                with open(self.config_json_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                    # Decrypt API Key if stored encrypted
                    enc_key = json_data.get("api_key", "")
                    if enc_key:
                        try:
                            json_data["api_key"] = self.fernet.decrypt(enc_key.encode()).decode()
                        except Exception:
                            json_data["api_key"] = ""
                    merged.update(json_data)
            except Exception as e:
                logger.error(f"Error reading JSON config: {e}")

        # 3. Merge YAML configuration if present
        if os.path.exists(self.config_yaml_path):
            try:
                with open(self.config_yaml_path, "r", encoding="utf-8") as f:
                    yaml_data = yaml.safe_load(f)
                    if isinstance(yaml_data, dict):
                        merged.update(yaml_data)
            except Exception as e:
                logger.error(f"Error reading YAML config: {e}")

        # 4. Overwrite from .env or environment variables
        self._load_env_overrides(merged)

        # Update dataclass instance and internal dict
        self.config_data = merged
        self.config = merged
        return merged

    def _load_env_overrides(self, target_dict: Dict[str, Any]) -> None:
        """Parse .env file and process OS environment variables."""
        if os.path.exists(self.env_path):
            try:
                with open(self.env_path, "r", encoding="utf-8") as ef:
                    for line in ef:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ[k.strip()] = v.strip().strip('"').strip("'")
            except Exception as e:
                logger.error(f"Failed to parse .env file: {e}")

        # Map environment variables to config keys
        env_mappings = {
            "OPENAI_API_KEY": "api_key",
            "AI_PROVIDER": "ai_provider",
            "OLLAMA_URL": "ollama_url",
            "OLLAMA_MODEL": "ollama_model",
            "THEME": "theme",
            "DEFAULT_CLOUD": "default_cloud",
            "PREFERRED_PLATFORM": "preferred_platform",
            "EXPORT_DIR": "export_dir"
        }

        for env_key, config_key in env_mappings.items():
            val = os.environ.get(env_key)
            if val:
                target_dict[config_key] = val

    def save_config(self, new_config: Optional[Dict[str, Any]] = None) -> None:
        """Encrypt API key and save configuration settings to JSON and YAML files."""
        if new_config is not None:
            self.config.update(new_config)

        try:
            config_copy = self.config.copy()
            api_key = config_copy.get("api_key", "")
            if api_key:
                config_copy["api_key"] = self.fernet.encrypt(api_key.encode()).decode()

            # Save JSON
            with open(self.config_json_path, "w", encoding="utf-8") as f:
                json.dump(config_copy, f, indent=4)

            # Save YAML preview (non-encrypted key omitted for security)
            yaml_copy = self.config.copy()
            if "api_key" in yaml_copy:
                yaml_copy["api_key"] = "***ENCRYPTED***"
            with open(self.config_yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(yaml_copy, f, default_flow_style=False)

            logger.info("Configuration saved successfully to JSON and YAML formats.")
        except Exception as e:
            ErrorHandler.handle_exception(
                ConfigurationError("Failed to persist configuration settings to disk.", e),
                show_dialog=False
            )

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value
        self.save_config()

# Global config manager instance
config_manager = ConfigManager()
