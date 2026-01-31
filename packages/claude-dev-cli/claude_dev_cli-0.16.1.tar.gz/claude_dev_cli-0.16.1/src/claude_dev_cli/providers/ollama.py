"""Ollama local AI provider implementation."""

import json
from datetime import datetime
from typing import Iterator, Optional, List, Dict, Any

from claude_dev_cli.providers.base import (
    AIProvider,
    ModelInfo,
    UsageInfo,
    ProviderConnectionError,
    ModelNotFoundError,
    ProviderError,
)

# Try to import requests, handle gracefully if not installed
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None  # type: ignore


class OllamaProvider(AIProvider):
    """Ollama local model provider implementation.
    
    Provides zero-cost local inference with models like:
    - llama2, mistral, codellama, phi, deepseek-coder, mixtral, etc.
    """
    
    # Known model templates for common models
    KNOWN_MODELS = {
        "mistral": {
            "display_name": "Mistral 7B",
            "context_window": 8192,
            "capabilities": ["chat", "code"]
        },
        "llama2": {
            "display_name": "Llama 2",
            "context_window": 4096,
            "capabilities": ["chat", "general"]
        },
        "codellama": {
            "display_name": "Code Llama",
            "context_window": 16384,
            "capabilities": ["code", "chat"]
        },
        "phi": {
            "display_name": "Phi",
            "context_window": 2048,
            "capabilities": ["chat", "reasoning"]
        },
        "deepseek-coder": {
            "display_name": "DeepSeek Coder",
            "context_window": 16384,
            "capabilities": ["code"]
        },
        "mixtral": {
            "display_name": "Mixtral 8x7B",
            "context_window": 32768,
            "capabilities": ["chat", "code", "analysis"]
        },
    }
    
    def __init__(self, config: Any) -> None:
        """Initialize Ollama provider.
        
        Args:
            config: ProviderConfig with optional base_url
        
        Raises:
            RuntimeError: If requests library is not installed
        """
        super().__init__(config)
        
        if not REQUESTS_AVAILABLE:
            raise RuntimeError(
                "Ollama provider requires the requests package. "
                "Install it with: pip install 'claude-dev-cli[ollama]'"
            )
        
        # No API key needed for local!
        self.base_url = getattr(config, 'base_url', None) or "http://localhost:11434"
        self.timeout = 120  # Local inference can be slow
        self.last_usage: Optional[UsageInfo] = None
    
    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
    ) -> str:
        """Make a synchronous call to Ollama API."""
        model = model or "mistral"
        
        # Build messages for chat endpoint
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        start_time = datetime.utcnow()
        
        try:
            # Use chat endpoint (preferred for conversational use)
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens or 4096,
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
        except requests.ConnectionError:
            raise ProviderConnectionError(
                "Cannot connect to Ollama. Is it running? Start with: ollama serve",
                provider="ollama"
            )
        except requests.Timeout:
            raise ProviderError(
                f"Ollama request timed out after {self.timeout}s. "
                "Local models can be slow - consider using a smaller model."
            )
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(
                    f"Model '{model}' not found. Pull it with: ollama pull {model}",
                    model=model,
                    provider="ollama"
                )
            raise ProviderError(f"Ollama API error: {e}")
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Extract response
        response_text = data.get("message", {}).get("content", "")
        
        # Get token counts if available
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        
        # Store usage info (always zero cost!)
        self.last_usage = UsageInfo(
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            duration_ms=duration_ms,
            model=model,
            timestamp=end_time,
            cost_usd=0.0  # Free!
        )
        
        return response_text
    
    def call_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
    ) -> Iterator[str]:
        """Make a streaming call to Ollama API."""
        model = model or "mistral"
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens or 4096,
                    }
                },
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Stream chunks
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk:
                        content = chunk["message"].get("content", "")
                        if content:
                            yield content
                            
        except requests.ConnectionError:
            raise ProviderConnectionError(
                "Cannot connect to Ollama. Is it running? Start with: ollama serve",
                provider="ollama"
            )
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(
                    f"Model '{model}' not found. Pull it with: ollama pull {model}",
                    model=model,
                    provider="ollama"
                )
            raise ProviderError(f"Ollama API error: {e}")
    
    def list_models(self) -> List[ModelInfo]:
        """List available Ollama models."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model_data in data.get("models", []):
                model_name = model_data.get("name", "")
                base_name = model_name.split(":")[0]  # Remove tag (e.g., "mistral:7b" -> "mistral")
                
                # Get info from known models or use defaults
                info = self.KNOWN_MODELS.get(base_name, {
                    "display_name": model_name,
                    "context_window": 4096,
                    "capabilities": ["chat"]
                })
                
                models.append(ModelInfo(
                    model_id=model_name,
                    display_name=info.get("display_name", model_name),
                    provider="ollama",
                    context_window=info.get("context_window", 4096),
                    input_price_per_mtok=0.0,  # Free!
                    output_price_per_mtok=0.0,  # Free!
                    capabilities=info.get("capabilities", ["chat"])
                ))
            
            return models
            
        except requests.ConnectionError:
            raise ProviderConnectionError(
                "Cannot connect to Ollama. Is it running? Start with: ollama serve",
                provider="ollama"
            )
        except Exception as e:
            raise ProviderError(f"Failed to list Ollama models: {e}")
    
    def get_last_usage(self) -> Optional[UsageInfo]:
        """Get usage information from the last API call."""
        return self.last_usage
    
    @property
    def provider_name(self) -> str:
        """Get the provider's name."""
        return "ollama"
    
    def test_connection(self) -> bool:
        """Test if Ollama is accessible."""
        try:
            response = requests.get(
                f"{self.base_url}/api/version",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
