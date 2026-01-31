"""AI Provider abstraction layer for claude-dev-cli.

This package provides a unified interface for multiple AI providers:
- Anthropic (Claude)
- OpenAI (GPT-4, GPT-3.5) - coming in v0.15.0
- Ollama (Local models) - coming in v0.16.0
- LM Studio (Local models) - coming in v0.16.0
"""

from claude_dev_cli.providers.base import (
    AIProvider,
    ModelInfo,
    UsageInfo,
    ProviderError,
    InsufficientCreditsError,
    ProviderConnectionError,
    ModelNotFoundError,
)

__all__ = [
    "AIProvider",
    "ModelInfo",
    "UsageInfo",
    "ProviderError",
    "InsufficientCreditsError",
    "ProviderConnectionError",
    "ModelNotFoundError",
]
