"""Abstract base class for AI providers."""

from abc import ABC, abstractmethod
from typing import Iterator, Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModelInfo:
    """Information about an AI model."""
    
    model_id: str
    display_name: str
    provider: str
    context_window: int
    input_price_per_mtok: float
    output_price_per_mtok: float
    capabilities: List[str]  # e.g., ["chat", "code", "vision"]


@dataclass
class UsageInfo:
    """Usage information for a single API call."""
    
    input_tokens: int
    output_tokens: int
    duration_ms: int
    model: str
    timestamp: datetime
    cost_usd: float


class AIProvider(ABC):
    """Abstract base class for AI provider implementations.
    
    All AI providers (Anthropic, OpenAI, Ollama, etc.) must implement this interface.
    This allows the CLI to work with any provider transparently.
    """
    
    def __init__(self, config: Any) -> None:
        """Initialize provider with configuration.
        
        Args:
            config: Provider-specific configuration (ProviderConfig)
        """
        self.config = config
    
    @abstractmethod
    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
    ) -> str:
        """Make a synchronous call to the AI provider.
        
        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            model: Model ID or profile name to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-2.0)
            
        Returns:
            The AI's text response
            
        Raises:
            ProviderError: On API errors
            InsufficientCreditsError: When credits are too low
        """
        pass
    
    @abstractmethod
    def call_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
    ) -> Iterator[str]:
        """Make a streaming call to the AI provider.
        
        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            model: Model ID or profile name to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-2.0)
            
        Yields:
            Text chunks as they arrive from the provider
            
        Raises:
            ProviderError: On API errors
            InsufficientCreditsError: When credits are too low
        """
        pass
    
    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """List available models from this provider.
        
        Returns:
            List of ModelInfo objects describing available models
        """
        pass
    
    @abstractmethod
    def get_last_usage(self) -> Optional[UsageInfo]:
        """Get usage information from the last API call.
        
        Returns:
            UsageInfo for the most recent call, or None if no calls made
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider's name (e.g., 'anthropic', 'openai', 'ollama').
        
        Returns:
            Provider name string
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the provider is accessible and credentials are valid.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class InsufficientCreditsError(ProviderError):
    """Raised when API credits are insufficient."""
    
    def __init__(self, message: str, provider: str) -> None:
        super().__init__(message)
        self.provider = provider


class ProviderConnectionError(ProviderError):
    """Raised when provider connection fails."""
    
    def __init__(self, message: str, provider: str) -> None:
        super().__init__(message)
        self.provider = provider


class ModelNotFoundError(ProviderError):
    """Raised when requested model is not available."""
    
    def __init__(self, message: str, model: str, provider: str) -> None:
        super().__init__(message)
        self.model = model
        self.provider = provider
