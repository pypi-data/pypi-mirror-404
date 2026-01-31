"""
Configuration management for Cost Katana
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, fields
from pathlib import Path


@dataclass
class Config:
    """
    Configuration class for Cost Katana client.

    Usage and cost tracking is always on; there is no option to disable it
    (required for usage attribution and cost visibility).
    """

    api_key: Optional[str] = None
    base_url: str = "https://api.costkatana.com"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    default_model: str = "nova-lite"
    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    default_chat_mode: str = "balanced"
    enable_analytics: bool = True
    enable_optimization: bool = True
    enable_failover: bool = True
    cost_limit_per_request: Optional[float] = None
    cost_limit_per_day: Optional[float] = None
    
    # Logging configuration
    enable_ai_logging: bool = True
    ai_logging_batch_size: int = 50
    ai_logging_flush_interval: float = 5.0
    log_level: str = 'info'

    def __post_init__(self):
        """Load from environment variables if not set"""
        if not self.api_key:
            self.api_key = os.getenv("API_KEY")

        # Override with environment variables if they exist
        if os.getenv("COST_KATANA_BASE_URL"):
            self.base_url = os.getenv("COST_KATANA_BASE_URL")
        if os.getenv("COST_KATANA_DEFAULT_MODEL"):
            self.default_model = os.getenv("COST_KATANA_DEFAULT_MODEL")
        if os.getenv("COST_KATANA_TIMEOUT"):
            self.timeout = int(os.getenv("COST_KATANA_TIMEOUT"))

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to JSON configuration file

        Returns:
            Config instance

        Example config.json:
        {
            "api_key": "dak_your_key_here",
            "base_url": "https://api.costkatana.com",
            "default_model": "claude-3-sonnet",
            "default_temperature": 0.3,
            "cost_limit_per_day": 100.0,
            "providers": {
                "anthropic": {
                    "priority": 1,
                    "models": ["claude-3-sonnet", "claude-3-haiku"]
                },
                "openai": {
                    "priority": 2,
                    "models": ["gpt-4", "gpt-3.5-turbo"]
                }
            }
        }
        """
        config_path_obj = Path(config_path).expanduser()

        if not config_path_obj.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path_obj, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")

        # Extract known fields
        config_fields = {field.name for field in fields(cls)}

        config_data = {k: v for k, v in data.items() if k in config_fields}
        config = cls(**config_data)

        # Store additional data
        setattr(
            config,
            "_extra_data",
            {k: v for k, v in data.items() if k not in config_fields},
        )

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        result = asdict(self)

        # Add extra data if it exists
        if hasattr(self, "_extra_data"):
            result.update(self._extra_data)

        return result

    def save(self, config_path: str):
        """Save configuration to JSON file"""
        config_path_obj = Path(config_path).expanduser()
        config_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path_obj, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        if hasattr(self, "_extra_data") and "providers" in self._extra_data:
            return self._extra_data["providers"].get(provider, {})
        return {}

    def get_model_mapping(self, model_name: str) -> str:
        """
        Map user-friendly model names to internal model IDs.
        This allows users to use names like 'gemini-2.0-flash' while
        the backend uses the actual model IDs.
        """
        # Default mapping - can be overridden in config file
        # Based on actual models available from Cost Katana Backend
        default_mappings = {
            # Amazon Nova models (primary recommendation)
            "nova-micro": "amazon.nova-micro-v1:0",
            "nova-lite": "amazon.nova-lite-v1:0",
            "nova-pro": "amazon.nova-pro-v1:0",
            "fast": "amazon.nova-micro-v1:0",
            "balanced": "amazon.nova-lite-v1:0",
            "powerful": "amazon.nova-pro-v1:0",
            # Anthropic Claude models
            "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
            "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
            "claude-3-opus": "anthropic.claude-3-opus-20240229-v1:0",
            "claude-3.5-haiku": "anthropic.claude-3-5-haiku-20241022-v1:0",
            "claude-3.5-sonnet": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "claude": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            # Meta Llama models
            "llama-3.1-8b": "meta.llama3-1-8b-instruct-v1:0",
            "llama-3.1-70b": "meta.llama3-1-70b-instruct-v1:0",
            "llama-3.1-405b": "meta.llama3-1-405b-instruct-v1:0",
            "llama-3.2-1b": "meta.llama3-2-1b-instruct-v1:0",
            "llama-3.2-3b": "meta.llama3-2-3b-instruct-v1:0",
            # Mistral models
            "mistral-7b": "mistral.mistral-7b-instruct-v0:2",
            "mixtral-8x7b": "mistral.mixtral-8x7b-instruct-v0:1",
            "mistral-large": "mistral.mistral-large-2402-v1:0",
            # Cohere models
            "command": "cohere.command-text-v14",
            "command-light": "cohere.command-light-text-v14",
            "command-r": "cohere.command-r-v1:0",
            "command-r-plus": "cohere.command-r-plus-v1:0",
            # AI21 models
            "jamba": "ai21.jamba-instruct-v1:0",
            "j2-ultra": "ai21.j2-ultra-v1",
            "j2-mid": "ai21.j2-mid-v1",
            # Backwards compatibility aliases
            "gemini-2.0-flash": "amazon.nova-lite-v1:0",  # Map to similar performance
            "gemini-pro": "amazon.nova-pro-v1:0",
            "gpt-4": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "gpt-3.5-turbo": "anthropic.claude-3-haiku-20240307-v1:0",
        }

        # Check for custom mappings in config
        if hasattr(self, "_extra_data") and "model_mappings" in self._extra_data:
            custom_mappings = self._extra_data["model_mappings"]
            default_mappings.update(custom_mappings)

        return default_mappings.get(model_name, model_name)
