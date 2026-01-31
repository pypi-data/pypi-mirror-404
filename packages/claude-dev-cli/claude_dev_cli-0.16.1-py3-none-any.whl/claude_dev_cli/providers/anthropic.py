"""Anthropic (Claude) AI provider implementation."""

import json
from datetime import datetime
from typing import Iterator, Optional, List, Dict, Any
from anthropic import Anthropic, APIError

from claude_dev_cli.providers.base import (
    AIProvider,
    ModelInfo,
    UsageInfo,
    InsufficientCreditsError,
    ProviderConnectionError,
    ModelNotFoundError,
)


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider implementation."""
    
    # Known Claude models with their capabilities
    KNOWN_MODELS = {
        "claude-3-5-haiku-20241022": {
            "display_name": "Claude 3.5 Haiku",
            "context_window": 200000,
            "input_price": 0.80,
            "output_price": 4.00,
            "capabilities": ["chat", "code", "analysis"]
        },
        "claude-sonnet-4-5-20250929": {
            "display_name": "Claude Sonnet 4.5",
            "context_window": 200000,
            "input_price": 3.00,
            "output_price": 15.00,
            "capabilities": ["chat", "code", "analysis", "vision"]
        },
        "claude-opus-4-20250514": {
            "display_name": "Claude Opus 4",
            "context_window": 200000,
            "input_price": 15.00,
            "output_price": 75.00,
            "capabilities": ["chat", "code", "analysis", "vision", "research"]
        },
        # Legacy models
        "claude-3-5-sonnet-20241022": {
            "display_name": "Claude 3.5 Sonnet",
            "context_window": 200000,
            "input_price": 3.00,
            "output_price": 15.00,
            "capabilities": ["chat", "code", "analysis", "vision"]
        },
    }
    
    def __init__(self, config: Any) -> None:
        """Initialize Anthropic provider.
        
        Args:
            config: ProviderConfig or APIConfig with api_key
        """
        super().__init__(config)
        
        # Extract API key from config
        api_key = getattr(config, 'api_key', None)
        if not api_key:
            raise ValueError("Anthropic provider requires api_key in config")
        
        self.client = Anthropic(api_key=api_key)
        self.last_usage: Optional[UsageInfo] = None
    
    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
    ) -> str:
        """Make a synchronous call to Claude API."""
        model = model or "claude-sonnet-4-5-20250929"
        max_tokens = max_tokens or 4096
        
        kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        start_time = datetime.utcnow()
        
        try:
            response = self.client.messages.create(**kwargs)
        except APIError as e:
            # Check for insufficient credits
            if e.status_code == 400 and "credit balance" in str(e).lower():
                raise InsufficientCreditsError(
                    f"Insufficient credits for Anthropic API: {e}",
                    provider="anthropic"
                )
            elif e.status_code == 404:
                raise ModelNotFoundError(
                    f"Model not found: {model}",
                    model=model,
                    provider="anthropic"
                )
            else:
                raise ProviderConnectionError(
                    f"Anthropic API error: {e}",
                    provider="anthropic"
                )
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Calculate cost
        model_info = self.KNOWN_MODELS.get(model, {})
        input_price = model_info.get("input_price", 0.0)
        output_price = model_info.get("output_price", 0.0)
        
        input_cost = (response.usage.input_tokens / 1_000_000) * input_price
        output_cost = (response.usage.output_tokens / 1_000_000) * output_price
        total_cost = input_cost + output_cost
        
        # Store usage info
        self.last_usage = UsageInfo(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            duration_ms=duration_ms,
            model=model,
            timestamp=end_time,
            cost_usd=total_cost
        )
        
        # Extract text from response
        text_blocks = [
            block.text for block in response.content if hasattr(block, 'text')
        ]
        return '\n'.join(text_blocks)
    
    def call_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
    ) -> Iterator[str]:
        """Make a streaming call to Claude API."""
        model = model or "claude-sonnet-4-5-20250929"
        max_tokens = max_tokens or 4096
        
        kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        try:
            with self.client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield text
        except APIError as e:
            if e.status_code == 400 and "credit balance" in str(e).lower():
                raise InsufficientCreditsError(
                    f"Insufficient credits for Anthropic API: {e}",
                    provider="anthropic"
                )
            else:
                raise ProviderConnectionError(
                    f"Anthropic API error: {e}",
                    provider="anthropic"
                )
    
    def list_models(self) -> List[ModelInfo]:
        """List available Claude models."""
        models = []
        for model_id, info in self.KNOWN_MODELS.items():
            models.append(ModelInfo(
                model_id=model_id,
                display_name=info["display_name"],
                provider="anthropic",
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
        return "anthropic"
    
    def test_connection(self) -> bool:
        """Test if the Anthropic API is accessible."""
        try:
            # Make a minimal API call to test credentials
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except APIError:
            return False
