"""
Custom exceptions for Cost Katana
"""


class CostKatanaError(Exception):
    """Base exception for Cost Katana errors"""

    pass


class AuthenticationError(CostKatanaError):
    """Raised when authentication fails"""

    pass


class ModelNotAvailableError(CostKatanaError):
    """Raised when requested model is not available"""

    pass


class RateLimitError(CostKatanaError):
    """Raised when rate limit is exceeded"""

    pass


class CostLimitExceededError(CostKatanaError):
    """Raised when cost limits are exceeded"""

    pass


class ConversationNotFoundError(CostKatanaError):
    """Raised when conversation is not found"""

    pass


class InvalidConfigurationError(CostKatanaError):
    """Raised when configuration is invalid"""

    pass


class NetworkError(CostKatanaError):
    """Raised when network requests fail"""

    pass


class ModelTimeoutError(CostKatanaError):
    """Raised when model request times out"""

    pass
