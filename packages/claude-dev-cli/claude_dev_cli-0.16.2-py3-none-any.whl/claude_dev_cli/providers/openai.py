"""OpenAI (GPT-4, GPT-3.5) AI provider implementation."""

from datetime import datetime
from typing import Iterator, Optional, List, Dict, Any

from claude_dev_cli.providers.base import (
    AIProvider,
    ModelInfo,
    UsageInfo,
    InsufficientCreditsError,
    ProviderConnectionError,
    ModelNotFoundError,
    ProviderError,
)

# Try to import openai, handle gracefully if not installed
try:
    from openai import OpenAI, APIError, AuthenticationError, RateLimitError, NotFoundError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore
    APIError = Exception  # type: ignore
    AuthenticationError = Exception  # type: ignore
    RateLimitError = Exception  # type: ignore
    NotFoundError = Exception  # type: ignore


class OpenAIProvider(AIProvider):
    """OpenAI GPT API provider implementation."""
    
    # Known OpenAI models with their capabilities
    KNOWN_MODELS = {
        "gpt-4-turbo-preview": {
            "display_name": "GPT-4 Turbo",
            "context_window": 128000,
            "input_price": 10.00,
            "output_price": 30.00,
            "capabilities": ["chat", "code", "analysis", "vision"]
        },
        "gpt-4-turbo": {
            "display_name": "GPT-4 Turbo",
            "context_window": 128000,
            "input_price": 10.00,
            "output_price": 30.00,
            "capabilities": ["chat", "code", "analysis", "vision"]
        },
        "gpt-4": {
            "display_name": "GPT-4",
            "context_window": 8192,
            "input_price": 30.00,
            "output_price": 60.00,
            "capabilities": ["chat", "code", "analysis"]
        },
        "gpt-3.5-turbo": {
            "display_name": "GPT-3.5 Turbo",
            "context_window": 16385,
            "input_price": 0.50,
            "output_price": 1.50,
            "capabilities": ["chat", "code"]
        },
    }
    
    def __init__(self, config: Any) -> None:
        """Initialize OpenAI provider.
        
        Args:
            config: ProviderConfig with api_key and optional base_url
        
        Raises:
            RuntimeError: If openai SDK is not installed
        """
        super().__init__(config)
        
        if not OPENAI_AVAILABLE:
            raise RuntimeError(
                "OpenAI provider requires the openai package. "
                "Install it with: pip install 'claude-dev-cli[openai]'"
            )
        
        # Extract API key from config
        api_key = getattr(config, 'api_key', None)
        if not api_key:
            raise ValueError("OpenAI provider requires api_key in config")
        
        # Get optional base_url for custom endpoints (Azure, proxies, etc.)
        base_url = getattr(config, 'base_url', None)
        
        # Initialize OpenAI client
        client_kwargs: Dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        self.client = OpenAI(**client_kwargs)
        self.last_usage: Optional[UsageInfo] = None
    
    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
    ) -> str:
        """Make a synchronous call to OpenAI API."""
        model = model or "gpt-4-turbo-preview"
        max_tokens = max_tokens or 4096
        
        # Build messages array (OpenAI format)
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        start_time = datetime.utcnow()
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                max_tokens=max_tokens,
                temperature=temperature
            )
        except AuthenticationError as e:
            raise ProviderConnectionError(
                f"OpenAI authentication failed: {e}",
                provider="openai"
            )
        except RateLimitError as e:
            raise ProviderError(f"OpenAI rate limit exceeded: {e}")
        except NotFoundError as e:
            raise ModelNotFoundError(
                f"Model not found: {model}",
                model=model,
                provider="openai"
            )
        except APIError as e:
            # Check for quota/billing issues
            error_message = str(e).lower()
            if "quota" in error_message or "billing" in error_message or "insufficient" in error_message:
                raise InsufficientCreditsError(
                    f"Insufficient OpenAI credits: {e}",
                    provider="openai"
                )
            raise ProviderConnectionError(
                f"OpenAI API error: {e}",
                provider="openai"
            )
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Calculate cost
        model_info = self.KNOWN_MODELS.get(model, {})
        input_price = model_info.get("input_price", 0.0)
        output_price = model_info.get("output_price", 0.0)
        
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        
        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * output_price
        total_cost = input_cost + output_cost
        
        # Store usage info
        self.last_usage = UsageInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            model=model,
            timestamp=end_time,
            cost_usd=total_cost
        )
        
        # Extract text from response
        if response.choices and len(response.choices) > 0:
            message = response.choices[0].message
            return message.content or ""
        return ""
    
    def call_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
    ) -> Iterator[str]:
        """Make a streaming call to OpenAI API."""
        model = model or "gpt-4-turbo-preview"
        max_tokens = max_tokens or 4096
        
        # Build messages array
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
                        
        except AuthenticationError as e:
            raise ProviderConnectionError(
                f"OpenAI authentication failed: {e}",
                provider="openai"
            )
        except RateLimitError as e:
            raise ProviderError(f"OpenAI rate limit exceeded: {e}")
        except APIError as e:
            error_message = str(e).lower()
            if "quota" in error_message or "billing" in error_message:
                raise InsufficientCreditsError(
                    f"Insufficient OpenAI credits: {e}",
                    provider="openai"
                )
            raise ProviderConnectionError(
                f"OpenAI API error: {e}",
                provider="openai"
            )
    
    def list_models(self) -> List[ModelInfo]:
        """List available OpenAI models."""
        models = []
        for model_id, info in self.KNOWN_MODELS.items():
            models.append(ModelInfo(
                model_id=model_id,
                display_name=info["display_name"],
                provider="openai",
                context_window=info["context_window"],
                input_price_per_mtok=info["input_price"],
                output_price_per_mtok=info["output_price"],
                capabilities=info["capabilities"]
            ))
        return models
    
    def get_last_usage(self) -> Optional[UsageInfo]:
        """Get usage information from the last API call."""
        return self.last_usage
    
    @property
    def provider_name(self) -> str:
        """Get the provider's name."""
        return "openai"
    
    def test_connection(self) -> bool:
        """Test if the OpenAI API is accessible."""
        try:
            # Make a minimal API call to test credentials
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False
