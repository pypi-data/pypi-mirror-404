"""
Generative AI Models - Simple interface similar to google-generative-ai
"""

import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from .client import CostKatanaClient
from .exceptions import CostKatanaError, ModelNotAvailableError


@dataclass
class GenerationConfig:
    """Configuration for text generation"""

    temperature: float = 0.7
    max_output_tokens: int = 2000
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    candidate_count: int = 1
    stop_sequences: Optional[List[str]] = None


@dataclass
class UsageMetadata:
    """Usage metadata returned with responses"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    latency: float
    model: str
    optimizations_applied: Optional[List[str]] = None
    cache_hit: bool = False
    agent_path: Optional[List[str]] = None
    risk_level: Optional[str] = None


class GenerateContentResponse:
    """Response from generate_content method"""

    def __init__(self, response_data: Dict[str, Any]):
        self._data = response_data
        self._text = response_data.get("data", {}).get("response", "")

        # Extract usage metadata
        data = response_data.get("data", {})
        self.usage_metadata = UsageMetadata(
            prompt_tokens=data.get(
                "tokenCount", 0
            ),  # This might need adjustment based on actual response
            completion_tokens=data.get("tokenCount", 0),
            total_tokens=data.get("tokenCount", 0),
            cost=data.get("cost", 0.0),
            latency=data.get("latency", 0.0),
            model=data.get("model", ""),
            optimizations_applied=data.get("optimizationsApplied"),
            cache_hit=data.get("cacheHit", False),
            agent_path=data.get("agentPath"),
            risk_level=data.get("riskLevel"),
        )

        # Store thinking/reasoning if available
        self.thinking = data.get("thinking")

    @property
    def text(self) -> str:
        """Get the response text"""
        return self._text

    @property
    def parts(self) -> List[Dict[str, Any]]:
        """Get response parts (for compatibility)"""
        return [{"text": self._text}] if self._text else []

    def __str__(self) -> str:
        return self._text

    def __repr__(self) -> str:
        return f"GenerateContentResponse(text='{self._text[:50]}...', cost=${self.usage_metadata.cost:.4f})"


class ChatSession:
    """A chat session for maintaining conversation context"""

    def __init__(
        self,
        client: CostKatanaClient,
        model_id: str,
        generation_config: Optional[GenerationConfig] = None,
        conversation_id: Optional[str] = None,
    ):
        self.client = client
        self.model_id = model_id
        self.generation_config = generation_config or GenerationConfig()
        self.conversation_id = conversation_id
        self.history: List[Dict[str, Any]] = []

        # Create conversation if not provided
        if not self.conversation_id:
            try:
                conv_response = self.client.create_conversation(
                    title=f"Chat with {model_id}", model_id=model_id
                )
                self.conversation_id = conv_response["data"]["id"]
            except Exception as e:
                raise CostKatanaError(f"Failed to create conversation: {str(e)}")

    def send_message(self, message: str, **kwargs) -> GenerateContentResponse:
        """
        Send a message in the chat session.

        Args:
            message: The message to send
            **kwargs: Additional parameters to override defaults

        Returns:
            GenerateContentResponse with the model's reply

        Example:
            response = chat.send_message("What's the weather like?")
            print(response.text)
        """
        # Merge generation config with kwargs
        params = {
            "temperature": kwargs.get(
                "temperature", self.generation_config.temperature
            ),
            "max_tokens": kwargs.get(
                "max_tokens", self.generation_config.max_output_tokens
            ),
            "chat_mode": kwargs.get("chat_mode", "balanced"),
            "use_multi_agent": kwargs.get("use_multi_agent", False),
        }

        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in params:
                params[key] = value

        try:
            response_data = self.client.send_message(
                message=message,
                model_id=self.model_id,
                conversation_id=self.conversation_id,
                **params,
            )

            # Add to history
            self.history.append(
                {"role": "user", "content": message, "timestamp": time.time()}
            )

            response_text = response_data.get("data", {}).get("response", "")
            self.history.append(
                {
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": time.time(),
                    "metadata": response_data.get("data", {}),
                }
            )

            return GenerateContentResponse(response_data)

        except Exception as e:
            if isinstance(e, CostKatanaError):
                raise
            raise CostKatanaError(f"Failed to send message: {str(e)}")

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history"""
        if not self.conversation_id:
            return self.history

        try:
            history_response = self.client.get_conversation_history(
                self.conversation_id
            )
            return history_response.get("data", [])
        except Exception:
            # Fall back to local history if API call fails
            return self.history

    def clear_history(self):
        """Clear the local conversation history"""
        self.history = []

    def delete_conversation(self):
        """Delete the conversation from the server"""
        try:
            self.client.delete_conversation(self.conversation_id)
            self.conversation_id = None
            self.history = []
        except Exception as e:
            raise CostKatanaError(f"Failed to delete conversation: {str(e)}")


class GenerativeModel:
    """
    A generative AI model with a simple interface similar to google-generative-ai.
    All requests are routed through Cost Katana for optimization and cost management.
    """

    def __init__(
        self,
        client: CostKatanaClient,
        model_name: str,
        generation_config: Optional[GenerationConfig] = None,
        **kwargs,
    ):
        """
        Initialize a generative model.

        Args:
            client: Cost Katana client instance
            model_name: Name of the model (e.g., 'gemini-2.0-flash', 'claude-3-sonnet')
            generation_config: Generation configuration
            **kwargs: Additional model parameters
        """
        self.client = client
        self.model_name = model_name
        self.model_id = client.config.get_model_mapping(model_name)
        self.generation_config = generation_config or GenerationConfig()
        self.model_params = kwargs

        # Validate model is available
        self._validate_model()

    def _validate_model(self):
        """Validate that the model is available"""
        try:
            available_models = self.client.get_available_models()
            model_ids = [
                model.get("id", model.get("modelId", "")) for model in available_models
            ]

            if self.model_id not in model_ids and self.model_name not in model_ids:
                raise ModelNotAvailableError(
                    f"Model '{self.model_name}' (ID: {self.model_id}) is not available. "
                    f"Available models: {', '.join(model_ids[:5])}..."
                )
        except ModelNotAvailableError:
            raise
        except Exception as e:
            # If we can't validate, log but don't fail - the model might still work
            print(f"Warning: Could not validate model availability: {e}")

    def generate_content(
        self,
        prompt: Union[str, List[str]],
        generation_config: Optional[GenerationConfig] = None,
        **kwargs,
    ) -> GenerateContentResponse:
        """
        Generate content from a prompt.

        Args:
            prompt: Text prompt or list of prompts
            generation_config: Generation configuration (overrides instance config)
            **kwargs: Additional parameters

        Returns:
            GenerateContentResponse with the generated content

        Example:
            model = cost_katana.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content("Tell me about AI")
            print(response.text)
            print(f"Cost: ${response.usage_metadata.cost:.4f}")
        """
        # Handle multiple prompts
        if isinstance(prompt, list):
            prompt = "\n\n".join(str(p) for p in prompt)

        # Use provided config or instance config
        config = generation_config or self.generation_config

        # Prepare parameters
        params = {
            "temperature": kwargs.get("temperature", config.temperature),
            "max_tokens": kwargs.get("max_tokens", config.max_output_tokens),
            "chat_mode": kwargs.get("chat_mode", "balanced"),
            "use_multi_agent": kwargs.get("use_multi_agent", False),
        }

        # Add any additional parameters from model_params or kwargs
        params.update(self.model_params)
        for key, value in kwargs.items():
            if key not in params:
                params[key] = value

        try:
            response_data = self.client.send_message(
                message=prompt, model_id=self.model_id, **params
            )

            return GenerateContentResponse(response_data)

        except Exception as e:
            if isinstance(e, CostKatanaError):
                raise
            raise CostKatanaError(f"Failed to generate content: {str(e)}")

    def start_chat(
        self, history: Optional[List[Dict[str, Any]]] = None, **kwargs
    ) -> ChatSession:
        """
        Start a chat session.

        Args:
            history: Optional conversation history
            **kwargs: Additional chat configuration

        Returns:
            ChatSession instance

        Example:
            model = cost_katana.GenerativeModel('gemini-2.0-flash')
            chat = model.start_chat()
            response = chat.send_message("Hello!")
            print(response.text)
        """
        chat_session = ChatSession(
            client=self.client,
            model_id=self.model_id,
            generation_config=self.generation_config,
            **kwargs,
        )

        # Add history if provided
        if history:
            chat_session.history = history

        return chat_session

    def count_tokens(self, prompt: str) -> Dict[str, int]:
        """
        Count tokens in a prompt (estimated).
        Note: This is a client-side estimate. Actual tokenization happens on the server.
        """
        # Simple word-based estimation - not accurate but gives an idea
        words = len(prompt.split())
        estimated_tokens = int(words * 1.3)  # Rough approximation

        return {
            "total_tokens": estimated_tokens,
            "prompt_tokens": estimated_tokens,
            "completion_tokens": 0,
        }

    def __repr__(self) -> str:
        return f"GenerativeModel(model_name='{self.model_name}', model_id='{self.model_id}')"
