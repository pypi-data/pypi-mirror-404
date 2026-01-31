"""
Cost Katana - The Simplest AI SDK for Python

Usage and cost tracking is always on; there is no option to disable it
(required for usage attribution and cost visibility).

Example:
    import cost_katana as ck

    # Just works!
    response = ck.ai('gpt-4', 'Hello, world!')
    print(response.text)
    print(f"Cost: ${response.cost}")
"""

from typing import Optional, List, Dict, Any

from .client import CostKatanaClient, get_global_client
from .models import ChatSession
from .exceptions import (
    CostKatanaError,
    AuthenticationError,
    ModelNotAvailableError,
    RateLimitError,
    CostLimitExceededError,
)
from .config import Config
from .logging import AILogger, ai_logger, Logger, logger
from .templates import TemplateManager, template_manager
from .models_constants import (
    openai,
    anthropic,
    google,
    aws_bedrock,
    xai,
    deepseek,
    mistral,
    cohere,
    groq,
    meta,
    is_model_constant,
    get_all_model_constants,
    get_provider_from_model,
)

__version__ = "2.2.6"

# Import configure function from client
from .client import configure


def create_generative_model(model_name: str, **kwargs):
    """
    Create a generative model instance (traditional API).

    Args:
        model_name: Name of the model (e.g., 'gemini-2.0-flash', 'claude-3-sonnet', 'gpt-4')
        **kwargs: Additional model configuration

    Returns:
        GenerativeModel instance

    Example:
        model = ck.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Hello, world!")
    """
    client = get_global_client()
    from .models import GenerativeModel as GM

    return GM(client, model_name, **kwargs)


# ============================================================================
# ULTRA-SIMPLE API - The easiest way to use AI in Python
# ============================================================================


class SimpleResponse:
    """Simple response object with all the info you need."""

    def __init__(
        self,
        text: str,
        cost: float,
        tokens: int,
        model: str,
        provider: str,
        cached: bool = False,
        optimized: bool = False,
    ):
        self.text = text
        self.cost = cost
        self.tokens = tokens
        self.model = model
        self.provider = provider
        self.cached = cached
        self.optimized = optimized
        self.saved_amount = 0.0

    def __repr__(self):
        return f"<Response text='{self.text[:50]}...' cost=${self.cost:.4f}>"


class SimpleChat:
    """Simple chat session with automatic cost tracking (always on; no option to disable)."""

    def __init__(
        self, model: str, system_message: Optional[str] = None, **options: Any
    ):
        self.model = model
        self.system_message = system_message
        self.options = options
        self.history: List[Dict[str, str]] = []
        self.total_cost = 0.0
        self.total_tokens = 0

        # Use the existing GenerativeModel under the hood
        self._gen_model = create_generative_model(model, **options)
        self._chat = self._gen_model.start_chat(
            history=[], system_message=system_message
        )

    def send(
        self, 
        message: str,
        template_id: str = None,
        template_variables: dict = None
    ) -> str:
        """Send a message and get response."""
        # Handle template if provided
        actual_message = message
        if template_id:
            resolution = template_manager.resolve_template(
                template_id, template_variables or {}
            )
            actual_message = resolution["prompt"]

        response = self._chat.send_message(actual_message)

        # Track metrics
        if hasattr(response, "usage_metadata"):
            self.total_cost += getattr(response.usage_metadata, "cost", 0)
            self.total_tokens += getattr(response.usage_metadata, "total_tokens", 0)

        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": response.text})

        return response.text

    def clear(self):
        """Clear conversation history."""
        self.history = []
        self.total_cost = 0.0
        self.total_tokens = 0
        self._chat = self._gen_model.start_chat(
            history=[], system_message=self.system_message
        )


def ai(
    model: str,
    prompt: str,
    template_id: str = None,
    template_variables: dict = None,
    enable_ai_logging: bool = True,
    **options
) -> SimpleResponse:
    """
    The simplest way to use AI in Python.

    Usage and cost tracking is always on; no configuration required.

    Args:
        model: AI model name or constant (e.g., openai.gpt_4, 'gpt-4')
        prompt: Your prompt text
        template_id: Optional template ID to use
        template_variables: Optional variables for template
        enable_ai_logging: Enable AI logging (default: True)
        **options: Optional parameters:
            - system_message (str): System prompt
            - temperature (float): 0-2, default 0.7
            - max_tokens (int): Max response tokens, default 1000
            - cache (bool): Enable caching, default False
            - cortex (bool): Enable optimization, default False

    Returns:
        SimpleResponse with text, cost, tokens, model, provider

    Example:
        >>> import cost_katana as ck
        >>> from cost_katana import openai
        >>> response = ck.ai(openai.gpt_4, 'Hello, world!')
        >>> print(response.text)
        Hello! How can I help you today?
        >>> print(f"Cost: ${response.cost}")
        Cost: $0.0012
    """
    import time
    import warnings
    
    # Add deprecation warning for string model names
    if not is_model_constant(model):
        warnings.warn(
            "⚠️  Deprecation Warning: Using string model names is deprecated and will be removed in a future version.\n"
            "   Please use type-safe model constants instead for better autocomplete and error prevention:\n"
            "   Example: from cost_katana import openai, anthropic, google\n"
            "            response = ck.ai(openai.gpt_4, 'your prompt')\n"
            "            response = ck.ai(anthropic.claude_3_5_sonnet_20241022, 'your prompt')\n"
            "            response = ck.ai(google.gemini_2_5_pro, 'your prompt')",
            DeprecationWarning,
            stacklevel=2
        )
    
    start_time = time.time()
    actual_prompt = prompt
    template_used = False
    template_name_val = None

    try:
        # Handle template if provided
        if template_id:
            resolution = template_manager.resolve_template(
                template_id, template_variables or {}
            )
            actual_prompt = resolution["prompt"]
            template_used = True
            template_name_val = resolution["template"].get("name")
            logger.debug(f"Template resolved: {template_id}")

        # Get or create model
        gen_model = create_generative_model(model)

        # Generate content
        response = gen_model.generate_content(actual_prompt, **options)

        # Extract metadata
        cost = (
            getattr(response.usage_metadata, "cost", 0.0)
            if hasattr(response, "usage_metadata")
            else 0.0
        )
        tokens = (
            getattr(response.usage_metadata, "total_tokens", 0)
            if hasattr(response, "usage_metadata")
            else 0
        )
        cached = (
            getattr(response.usage_metadata, "cache_hit", False)
            if hasattr(response, "usage_metadata")
            else False
        )

        # Determine provider from model name
        provider = _infer_provider(model)
        response_time = int((time.time() - start_time) * 1000)

        # Log AI call if enabled
        if enable_ai_logging:
            ai_logger.log_ai_call({
                "service": provider,
                "operation": "chat_completion",
                "aiModel": model,
                "statusCode": 200,
                "responseTime": response_time,
                "prompt": actual_prompt,
                "result": response.text,
                "inputTokens": getattr(response.usage_metadata, "prompt_tokens", 0) if hasattr(response, "usage_metadata") else 0,
                "outputTokens": getattr(response.usage_metadata, "completion_tokens", 0) if hasattr(response, "usage_metadata") else 0,
                "totalTokens": tokens,
                "cost": cost,
                "success": True,
                "cacheHit": cached,
                "cortexEnabled": options.get("cortex", False),
                "templateId": template_id,
                "templateName": template_name_val,
                "templateVariables": template_variables,
            })

        result = SimpleResponse(
            text=response.text,
            cost=cost,
            tokens=tokens,
            model=model,
            provider=provider,
            cached=cached,
            optimized=options.get("cortex", False),
        )
        result.templateUsed = template_used
        return result

    except Exception as e:
        raise CostKatanaError(
            f"AI request failed: {str(e)}\n\n"
            f"Troubleshooting:\n"
            f"1. Check your API key is set correctly\n"
            f"2. Verify the model name is correct\n"
            f"3. Ensure you have internet connection\n"
            f"4. Check your Cost Katana dashboard for usage limits\n\n"
            f"Get help at: https://docs.costkatana.com/python"
        )


def chat(
    model: str, system_message: Optional[str] = None, **options: Any
) -> SimpleChat:
    """
    Create a chat session with conversation history.

    Args:
        model: AI model name or constant (e.g., openai.gpt_4, 'gpt-4')
        system_message: Optional system prompt for the session
        **options: Additional options (temperature, max_tokens, etc.)

    Returns:
        SimpleChat session object

    Example:
        >>> import cost_katana as ck
        >>> from cost_katana import openai
        >>> session = ck.chat(openai.gpt_4)
        >>> session.send('Hello!')
        'Hi! How can I help you today?'
        >>> session.send('Tell me a joke')
        'Why did the...'
        >>> print(f"Total: ${session.total_cost}")
        Total: $0.0023
    """
    import warnings
    
    # Add deprecation warning for string model names
    if not is_model_constant(model):
        warnings.warn(
            "⚠️  Deprecation Warning: Using string model names is deprecated and will be removed in a future version.\n"
            "   Please use type-safe model constants instead:\n"
            "   Example: from cost_katana import openai, anthropic\n"
            "            session = ck.chat(openai.gpt_4, system_message='...')\n"
            "            session = ck.chat(anthropic.claude_3_5_sonnet_20241022, system_message='...')",
            DeprecationWarning,
            stacklevel=2
        )
    
    return SimpleChat(model, system_message, **options)


def _infer_provider(model: str) -> str:
    """Infer provider from model name."""
    model_lower = model.lower()

    if "gpt" in model_lower or "dall-e" in model_lower:
        return "openai"
    elif "claude" in model_lower:
        return "anthropic"
    elif "gemini" in model_lower or "palm" in model_lower:
        return "google"
    elif "nova" in model_lower or "titan" in model_lower:
        return "aws"
    elif "command" in model_lower:
        return "cohere"
    elif "llama" in model_lower or "mixtral" in model_lower:
        return "meta"
    else:
        return "unknown"


# Legacy compatibility - keep GenerativeModel
GenerativeModel = create_generative_model

# Export everything
__all__ = [
    # Simple API (recommended)
    "ai",
    "chat",
    "configure",
    # Model Constants
    "openai",
    "anthropic",
    "google",
    "aws_bedrock",
    "xai",
    "deepseek",
    "mistral",
    "cohere",
    "groq",
    "meta",
    "is_model_constant",
    "get_all_model_constants",
    "get_provider_from_model",
    # Traditional API (compatibility)
    "GenerativeModel",
    "create_generative_model",
    "ChatSession",
    "CostKatanaClient",
    # Logging & Templates
    "AILogger",
    "ai_logger",
    "Logger",
    "logger",
    "TemplateManager",
    "template_manager",
    # Exceptions
    "CostKatanaError",
    "AuthenticationError",
    "ModelNotAvailableError",
    "RateLimitError",
    "CostLimitExceededError",
    # Config
    "Config",
]
