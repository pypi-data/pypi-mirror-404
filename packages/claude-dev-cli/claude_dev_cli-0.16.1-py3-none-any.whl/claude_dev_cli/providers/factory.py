"""Factory for creating AI provider instances."""

from typing import Any

from claude_dev_cli.providers.base import AIProvider, ProviderError
from claude_dev_cli.providers.anthropic import AnthropicProvider

# Try to import OpenAI provider, graceful fallback if not installed
try:
    from claude_dev_cli.providers.openai import OpenAIProvider
    OPENAI_PROVIDER_AVAILABLE = True
except (ImportError, RuntimeError):
    OpenAIProvider = None  # type: ignore
    OPENAI_PROVIDER_AVAILABLE = False

# Try to import Ollama provider, graceful fallback if not installed
try:
    from claude_dev_cli.providers.ollama import OllamaProvider
    OLLAMA_PROVIDER_AVAILABLE = True
except (ImportError, RuntimeError):
    OllamaProvider = None  # type: ignore
    OLLAMA_PROVIDER_AVAILABLE = False


class ProviderFactory:
    """Factory for creating AI provider instances based on configuration."""
    
    # Build registry of available providers
    @staticmethod
    def _build_provider_registry() -> dict:
        """Build registry of available providers based on installed dependencies."""
        registry = {
            "anthropic": AnthropicProvider,
        }
        
        # Add OpenAI if available
        if OPENAI_PROVIDER_AVAILABLE and OpenAIProvider:
            registry["openai"] = OpenAIProvider
        
        # Add Ollama if available
        if OLLAMA_PROVIDER_AVAILABLE and OllamaProvider:
            registry["ollama"] = OllamaProvider
        
        # Future providers:
        # "lmstudio": LMStudioProvider,  # v0.16.0
        
        return registry
    
    # Registry of available providers
    _PROVIDERS = None
    
    @staticmethod
    def create(config: Any) -> AIProvider:
        """Create a provider instance based on configuration.
        
        Args:
            config: Provider configuration (ProviderConfig or APIConfig)
                    Must have 'provider' attribute or defaults to 'anthropic'
                    
        Returns:
            AIProvider instance
            
        Raises:
            ProviderError: If provider type is unknown or unavailable
        """
        # Build registry if not already done
        if ProviderFactory._PROVIDERS is None:
            ProviderFactory._PROVIDERS = ProviderFactory._build_provider_registry()
        
        # Determine provider type
        provider_type = getattr(config, 'provider', 'anthropic')
        
        # Look up provider class
        provider_class = ProviderFactory._PROVIDERS.get(provider_type.lower())
        
        if not provider_class:
            available = ", ".join(ProviderFactory._PROVIDERS.keys())
            raise ProviderError(
                f"Unknown provider: {provider_type}. "
                f"Available providers: {available}"
            )
        
        # Instantiate and return provider
        try:
            return provider_class(config)
        except Exception as e:
            raise ProviderError(
                f"Failed to initialize {provider_type} provider: {e}"
            )
    
    @staticmethod
    def list_providers() -> list[str]:
        """List available provider types.
        
        Returns:
            List of provider type names (e.g., ['anthropic', 'openai'])
        """
        if ProviderFactory._PROVIDERS is None:
            ProviderFactory._PROVIDERS = ProviderFactory._build_provider_registry()
        return list(ProviderFactory._PROVIDERS.keys())
    
    @staticmethod
    def is_provider_available(provider_type: str) -> bool:
        """Check if a provider type is available.
        
        Args:
            provider_type: Provider type name (e.g., 'anthropic', 'openai')
            
        Returns:
            True if provider is available, False otherwise
        """
        if ProviderFactory._PROVIDERS is None:
            ProviderFactory._PROVIDERS = ProviderFactory._build_provider_registry()
        return provider_type.lower() in ProviderFactory._PROVIDERS
