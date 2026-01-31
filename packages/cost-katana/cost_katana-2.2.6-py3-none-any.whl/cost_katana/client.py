"""
Cost Katana HTTP Client
Handles communication with the Cost Katana backend API
"""

import json
from typing import Dict, Any, Optional, List
import httpx
from .config import Config
from .exceptions import (
    CostKatanaError,
    AuthenticationError,
    ModelNotAvailableError,
    RateLimitError,
    CostLimitExceededError,
)
from .logging import AILogger, ai_logger
from .templates import TemplateManager, template_manager

# Global client instance for the configure function
_global_client = None


def configure(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    config_file: Optional[str] = None,
    **kwargs,
):
    """
    Configure Cost Katana client globally.

    Usage and cost tracking is always on; no option to disable.

    Args:
        api_key: Your Cost Katana API key (starts with 'dak_')
        base_url: Base URL for Cost Katana API (optional)
        config_file: Path to JSON configuration file (optional)
        **kwargs: Additional configuration options

    Example:
        # Using API key
        cost_katana.configure(api_key='dak_your_key_here')

        # Using config file
        cost_katana.configure(config_file='config.json')
    """
    global _global_client
    _global_client = CostKatanaClient(
        api_key=api_key, base_url=base_url, config_file=config_file, **kwargs
    )
    return _global_client


def get_global_client():
    """Get the global client instance"""
    if _global_client is None:
        raise CostKatanaError(
            "Cost Katana not configured. Call cost_katana.configure() first."
        )
    return _global_client


class CostKatanaClient:
    """HTTP client for Cost Katana API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        config_file: Optional[str] = None,
        timeout: int = 30,
        **kwargs,
    ):
        """
        Initialize Cost Katana client.

        Args:
            api_key: Your Cost Katana API key
            base_url: Base URL for the API
            config_file: Path to JSON configuration file
            timeout: Request timeout in seconds
        """
        self.config = Config.from_file(config_file) if config_file else Config()

        # Override with provided parameters
        if api_key:
            self.config.api_key = api_key
        if base_url:
            self.config.base_url = base_url

        # Apply additional config
        for key, value in kwargs.items():
            setattr(self.config, key, value)

        # Validate configuration
        if not self.config.api_key:
            raise AuthenticationError(
                "API key is required. Get one from https://costkatana.com/integrations"
            )

        # Initialize HTTP client
        self.client = httpx.Client(
            base_url=self.config.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"cost-katana-python/2.1.0",
            },
        )

        # Initialize AI logger
        if getattr(self.config, 'enable_ai_logging', True):
            self.ai_logger = AILogger(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                enable_logging=True,
            )
        else:
            self.ai_logger = None

        # Initialize template manager
        self.template_manager = TemplateManager(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client"""
        if hasattr(self, "client"):
            self.client.close()

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate exceptions"""
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise CostKatanaError(f"Invalid JSON response: {response.text}")

        if response.status_code == 401:
            raise AuthenticationError(data.get("message", "Authentication failed"))
        elif response.status_code == 403:
            raise AuthenticationError(data.get("message", "Access forbidden"))
        elif response.status_code == 404:
            raise ModelNotAvailableError(data.get("message", "Model not found"))
        elif response.status_code == 429:
            raise RateLimitError(data.get("message", "Rate limit exceeded"))
        elif response.status_code == 400 and "cost" in data.get("message", "").lower():
            raise CostLimitExceededError(data.get("message", "Cost limit exceeded"))
        elif not response.is_success:
            raise CostKatanaError(
                data.get("message", f"API error: {response.status_code}")
            )

        return data

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        try:
            response = self.client.get("/api/chat/models")
            data = self._handle_response(response)
            return data.get("data", [])
        except Exception as e:
            if isinstance(e, CostKatanaError):
                raise
            raise CostKatanaError(f"Failed to get models: {str(e)}")

    def send_message(
        self,
        message: str,
        model_id: str,
        conversation_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        chat_mode: str = "balanced",
        use_multi_agent: bool = False,
        template_id: Optional[str] = None,
        template_variables: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Send a message to the AI model via Cost Katana.

        Args:
            message: The message to send
            model_id: ID of the model to use
            conversation_id: Optional conversation ID
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            chat_mode: Chat optimization mode ('fastest', 'cheapest', 'balanced')
            use_multi_agent: Whether to use multi-agent processing
            template_id: Optional template ID to use
            template_variables: Optional variables for template

        Returns:
            Response data from the API
        """
        # Handle template if provided
        actual_message = message
        if template_id and self.template_manager:
            resolution = self.template_manager.resolve_template(
                template_id, template_variables or {}
            )
            actual_message = resolution["prompt"]

        payload = {
            "message": actual_message,
            "modelId": model_id,
            "temperature": temperature,
            "maxTokens": max_tokens,
            "chatMode": chat_mode,
            "useMultiAgent": use_multi_agent,
            **kwargs,
        }

        if conversation_id:
            payload["conversationId"] = conversation_id
        if template_id:
            payload["templateId"] = template_id
            if template_variables:
                payload["templateVariables"] = template_variables

        try:
            response = self.client.post("/api/chat/message", json=payload)
            return self._handle_response(response)
        except Exception as e:
            if isinstance(e, CostKatanaError):
                raise
            raise CostKatanaError(f"Failed to send message: {str(e)}")

    def create_conversation(
        self, title: Optional[str] = None, model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new conversation"""
        payload = {}
        if title:
            payload["title"] = title
        if model_id:
            payload["modelId"] = model_id

        try:
            response = self.client.post("/api/chat/conversations", json=payload)
            return self._handle_response(response)
        except Exception as e:
            if isinstance(e, CostKatanaError):
                raise
            raise CostKatanaError(f"Failed to create conversation: {str(e)}")

    def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation history"""
        try:
            response = self.client.get(
                f"/api/chat/conversations/{conversation_id}/history"
            )
            return self._handle_response(response)
        except Exception as e:
            if isinstance(e, CostKatanaError):
                raise
            raise CostKatanaError(f"Failed to get conversation history: {str(e)}")

    def delete_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Delete a conversation"""
        try:
            response = self.client.delete(f"/api/chat/conversations/{conversation_id}")
            return self._handle_response(response)
        except Exception as e:
            if isinstance(e, CostKatanaError):
                raise
            raise CostKatanaError(f"Failed to delete conversation: {str(e)}")
