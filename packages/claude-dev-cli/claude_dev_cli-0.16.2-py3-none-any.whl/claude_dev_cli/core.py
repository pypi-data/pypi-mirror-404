"""Core Claude API client with routing and tracking."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from claude_dev_cli.config import Config, APIConfig, ProviderConfig
from claude_dev_cli.providers.factory import ProviderFactory
from claude_dev_cli.providers.base import AIProvider


class ClaudeClient:
    """AI client with multi-provider support and routing.
    
    Backward compatible wrapper around provider system.
    Uses AIProvider abstraction to support Anthropic, OpenAI, Ollama, etc.
    """
    
    def __init__(self, config: Optional[Config] = None, api_config_name: Optional[str] = None):
        """Initialize AI client.
        
        API routing hierarchy (highest to lowest priority):
        1. Explicit api_config_name parameter
        2. Project-specific .claude-dev-cli file
        3. Default API config
        """
        self.config = config or Config()
        
        # Determine which API config to use based on hierarchy
        if not api_config_name:
            # Check for project profile if no explicit config provided
            project_profile = self.config.get_project_profile()
            if project_profile:
                api_config_name = project_profile.api_config
        
        self.api_config = self.config.get_api_config(api_config_name)
        if not self.api_config:
            raise ValueError(
                "No API configuration found. Run 'cdc config add' to set up an API key."
            )
        
        # Create provider using factory pattern
        # APIConfig is treated as ProviderConfig with provider="anthropic"
        self.provider = ProviderFactory.create(self.api_config)
        
        self.model = self.config.get_model()
        self.max_tokens = self.config.get_max_tokens()
    
    def _resolve_model(self, model_or_profile: Optional[str] = None) -> str:
        """Resolve model profile name or ID to actual model ID.
        
        Resolution hierarchy:
        1. Explicit model_or_profile parameter (if provided)
        2. Project-specific model profile
        3. API-specific default model profile
        4. Global default model profile
        5. Legacy default model setting
        
        Returns actual model ID for API calls.
        """
        # Start with explicit parameter or legacy model setting
        profile_or_id = model_or_profile or self.model
        
        # If no explicit model, check hierarchical defaults
        if not model_or_profile:
            # Check project profile
            project_profile = self.config.get_project_profile()
            if project_profile and project_profile.model_profile:
                profile_or_id = project_profile.model_profile
            else:
                # Get API or global default profile name
                profile_or_id = self.config.get_default_model_profile(
                    api_config_name=self.api_config.name
                )
        
        # Try to resolve as profile name
        profile = self.config.get_model_profile(
            profile_or_id,
            api_config_name=self.api_config.name
        )
        if profile:
            return profile.model_id
        
        # Assume it's already a model ID
        return profile_or_id
    
    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        stream: bool = False
    ) -> str:
        """Make a call to AI provider.
        
        Args:
            model: Model ID or profile name (e.g., 'fast', 'smart', 'powerful')
        """
        # Resolve profile name to model ID
        resolved_model = self._resolve_model(model)
        max_tokens = max_tokens or self.max_tokens
        
        # Check project profile for system prompt
        project_profile = self.config.get_project_profile()
        if project_profile and project_profile.system_prompt and not system_prompt:
            system_prompt = project_profile.system_prompt
        
        # Call provider
        response = self.provider.call(
            prompt=prompt,
            system_prompt=system_prompt,
            model=resolved_model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Log usage
        usage = self.provider.get_last_usage()
        if usage:
            self._log_usage(
                prompt=prompt,
                usage=usage,
                api_config_name=self.api_config.name
            )
        
        return response
    
    def call_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0
    ):
        """Make a streaming call to AI provider.
        
        Args:
            model: Model ID or profile name (e.g., 'fast', 'smart', 'powerful')
        """
        # Resolve profile name to model ID
        resolved_model = self._resolve_model(model)
        max_tokens = max_tokens or self.max_tokens
        
        # Check project profile for system prompt
        project_profile = self.config.get_project_profile()
        if project_profile and project_profile.system_prompt and not system_prompt:
            system_prompt = project_profile.system_prompt
        
        # Use provider's streaming method
        for text in self.provider.call_streaming(
            prompt=prompt,
            system_prompt=system_prompt,
            model=resolved_model,
            max_tokens=max_tokens,
            temperature=temperature
        ):
            yield text
    
    def _log_usage(
        self,
        prompt: str,
        usage: Any,  # UsageInfo from provider
        api_config_name: str
    ) -> None:
        """Log API usage to file."""
        log_entry = {
            "timestamp": usage.timestamp.isoformat(),
            "api_config": api_config_name,
            "model": usage.model,
            "prompt_preview": prompt[:100],
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "duration_ms": usage.duration_ms,
            "cost_usd": usage.cost_usd,
            "provider": self.provider.provider_name
        }
        
        with open(self.config.usage_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
