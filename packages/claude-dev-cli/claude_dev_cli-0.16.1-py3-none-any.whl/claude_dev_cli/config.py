"""Configuration management for Claude Dev CLI."""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from pydantic import BaseModel, Field

from claude_dev_cli.secure_storage import SecureStorage


class ContextConfig(BaseModel):
    """Global context gathering configuration."""
    
    auto_context_default: bool = False  # Default for --auto-context flag
    max_file_lines: int = 1000  # Maximum lines per file in context
    max_related_files: int = 5  # Maximum related files to include
    max_diff_lines: int = 200  # Maximum lines of diff to include
    include_git: bool = True  # Include git context by default
    include_dependencies: bool = True  # Include dependencies by default
    include_tests: bool = True  # Include test files by default


class SummarizationConfig(BaseModel):
    """Conversation summarization configuration."""
    
    auto_summarize: bool = True  # Enable automatic summarization
    threshold_tokens: int = 8000  # Token threshold for auto-summarization
    keep_recent_messages: int = 4  # Number of recent message pairs to keep
    summary_max_words: int = 300  # Maximum words in generated summary


class APIConfig(BaseModel):
    """Configuration for a Claude API key.
    
    DEPRECATED: Use ProviderConfig instead. Maintained for backward compatibility.
    """
    
    name: str
    api_key: str
    description: Optional[str] = None
    default: bool = False
    default_model_profile: Optional[str] = None  # Default model profile for this API
    # Added for provider compatibility
    provider: str = "anthropic"  # Always anthropic for APIConfig


class ProviderConfig(BaseModel):
    """Configuration for an AI provider (Anthropic, OpenAI, Ollama, etc.)."""
    
    name: str  # User-friendly name (e.g., "personal-claude", "work-openai")
    provider: str  # Provider type: "anthropic", "openai", "ollama", "lmstudio"
    api_key: Optional[str] = None  # Not needed for local providers
    base_url: Optional[str] = None  # Custom endpoint URL (for local/enterprise)
    description: Optional[str] = None
    default: bool = False
    default_model_profile: Optional[str] = None


class ModelProfile(BaseModel):
    """Model profile with pricing information."""
    
    name: str  # User-friendly alias (e.g., "fast", "smart", "powerful")
    model_id: str  # Provider-specific model ID
    description: Optional[str] = None
    input_price_per_mtok: float  # Input cost per million tokens (USD)
    output_price_per_mtok: float  # Output cost per million tokens (USD)
    use_cases: List[str] = Field(default_factory=list)  # Task types
    provider: str = "anthropic"  # Provider type: "anthropic", "openai", "ollama"
    api_config_name: Optional[str] = None  # Tied to specific API/provider config, or None for global


class ProjectProfile(BaseModel):
    """Project-specific configuration."""
    
    name: str
    api_config: str  # Name of the API config to use
    system_prompt: Optional[str] = None
    allowed_commands: List[str] = Field(default_factory=lambda: ["all"])
    model_profile: Optional[str] = None  # Preferred model profile for this project
    
    # Project memory - preferences and patterns
    auto_context: bool = False  # Default value for --auto-context flag
    coding_style: Optional[str] = None  # Preferred coding style
    test_framework: Optional[str] = None  # Preferred test framework
    preferences: Dict[str, str] = Field(default_factory=dict)  # Custom preferences
    
    # Context gathering configuration
    max_context_files: int = 5  # Maximum number of related files to include
    max_diff_lines: int = 200  # Maximum lines of diff to include
    max_file_lines: int = 1000  # Maximum lines per file in context
    include_tests_by_default: bool = True  # Include test files in review context
    context_depth: int = 2  # How deep to search for related modules


class Config:
    """Manages configuration for Claude Dev CLI."""
    
    def __init__(self) -> None:
        """Initialize configuration."""
        # Determine home directory (respects HOME env var for testing)
        home = Path(os.environ.get("HOME", str(Path.home())))
        
        self.config_dir = home / ".claude-dev-cli"
        self.config_file = self.config_dir / "config.json"
        self.usage_log = self.config_dir / "usage.jsonl"
        
        self._ensure_config_dir()
        self._data: Dict = self._load_config()
        
        # Initialize secure storage
        self.secure_storage = SecureStorage(self.config_dir)
        
        # Auto-migrate if plaintext keys exist
        self._auto_migrate_keys()
    
    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        # Check if config_dir exists as a file (not directory)
        if self.config_dir.exists() and not self.config_dir.is_dir():
            raise RuntimeError(
                f"Configuration path {self.config_dir} exists but is not a directory. "
                f"Please remove or rename this file."
            )
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if usage_log exists as a directory (not file)
        if self.usage_log.exists() and self.usage_log.is_dir():
            raise RuntimeError(
                f"Usage log path {self.usage_log} is a directory. "
                f"Please remove this directory."
            )
        
        self.usage_log.touch(exist_ok=True)
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        if not self.config_file.exists():
            default_config = {
                "api_configs": [],
                "project_profiles": [],
                "model_profiles": self._get_default_model_profiles(),
                "default_model": "claude-sonnet-4-5-20250929",  # Legacy, kept for backwards compat
                "default_model_profile": "smart",
                "max_tokens": 4096,
                "context": ContextConfig().model_dump(),
                "summarization": SummarizationConfig().model_dump(),
            }
            self._save_config(default_config)
            return default_config
        
        # Check if config_file is actually a directory
        if self.config_file.is_dir():
            raise RuntimeError(
                f"Configuration file {self.config_file} is a directory. "
                f"Please remove this directory."
            )
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
                # Ensure required keys exist (for backwards compatibility)
                if "context" not in config:
                    config["context"] = ContextConfig().model_dump()
                if "summarization" not in config:
                    config["summarization"] = SummarizationConfig().model_dump()
                if "model_profiles" not in config:
                    config["model_profiles"] = self._get_default_model_profiles()
                if "default_model_profile" not in config:
                    config["default_model_profile"] = "smart"
                
                return config
        except (json.JSONDecodeError, IOError) as e:
            raise RuntimeError(
                f"Failed to load configuration from {self.config_file}: {e}"
            )
    
    def _save_config(self, data: Optional[Dict] = None) -> None:
        """Save configuration to file."""
        if data is None:
            data = self._data
        
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _get_default_model_profiles(self) -> List[Dict]:
        """Get default model profiles for all providers."""
        profiles = [
            # Anthropic (Claude) profiles
            {
                "name": "fast",
                "model_id": "claude-3-5-haiku-20241022",
                "description": "Fast and economical for simple tasks (Claude)",
                "input_price_per_mtok": 0.80,
                "output_price_per_mtok": 4.00,
                "use_cases": ["quick", "simple", "classification"],
                "provider": "anthropic",
                "api_config_name": None
            },
            {
                "name": "smart",
                "model_id": "claude-sonnet-4-5-20250929",
                "description": "Balanced performance and cost for most tasks (Claude)",
                "input_price_per_mtok": 3.00,
                "output_price_per_mtok": 15.00,
                "use_cases": ["general", "coding", "analysis"],
                "provider": "anthropic",
                "api_config_name": None
            },
            {
                "name": "powerful",
                "model_id": "claude-opus-4-20250514",
                "description": "Maximum capability for complex tasks (Claude)",
                "input_price_per_mtok": 15.00,
                "output_price_per_mtok": 75.00,
                "use_cases": ["complex", "research", "creative"],
                "provider": "anthropic",
                "api_config_name": None
            },
            # OpenAI (GPT) profiles - only added if OpenAI provider available
            {
                "name": "fast-openai",
                "model_id": "gpt-3.5-turbo",
                "description": "Fast and economical for simple tasks (OpenAI)",
                "input_price_per_mtok": 0.50,
                "output_price_per_mtok": 1.50,
                "use_cases": ["quick", "simple", "chat"],
                "provider": "openai",
                "api_config_name": None
            },
            {
                "name": "smart-openai",
                "model_id": "gpt-4-turbo",
                "description": "Balanced performance and cost for most tasks (OpenAI)",
                "input_price_per_mtok": 10.00,
                "output_price_per_mtok": 30.00,
                "use_cases": ["general", "coding", "analysis"],
                "provider": "openai",
                "api_config_name": None
            },
            {
                "name": "powerful-openai",
                "model_id": "gpt-4",
                "description": "High capability for complex tasks (OpenAI)",
                "input_price_per_mtok": 30.00,
                "output_price_per_mtok": 60.00,
                "use_cases": ["complex", "research", "reasoning"],
                "provider": "openai",
                "api_config_name": None
            },
            # Ollama (Local) profiles - zero cost!
            {
                "name": "fast-local",
                "model_id": "mistral",
                "description": "Fast local inference with Mistral 7B (zero cost)",
                "input_price_per_mtok": 0.0,
                "output_price_per_mtok": 0.0,
                "use_cases": ["quick", "chat", "general"],
                "provider": "ollama",
                "api_config_name": None
            },
            {
                "name": "smart-local",
                "model_id": "mixtral",
                "description": "Powerful local inference with Mixtral 8x7B (zero cost)",
                "input_price_per_mtok": 0.0,
                "output_price_per_mtok": 0.0,
                "use_cases": ["general", "analysis", "chat"],
                "provider": "ollama",
                "api_config_name": None
            },
            {
                "name": "code-local",
                "model_id": "codellama",
                "description": "Code-focused local inference with Code Llama (zero cost)",
                "input_price_per_mtok": 0.0,
                "output_price_per_mtok": 0.0,
                "use_cases": ["coding", "refactoring", "debugging"],
                "provider": "ollama",
                "api_config_name": None
            },
        ]
        
        return profiles
    
    def _auto_migrate_keys(self) -> None:
        """Automatically migrate plaintext API keys to secure storage."""
        api_configs = self._data.get("api_configs", [])
        migrated = False
        
        for config in api_configs:
            if "api_key" in config and config["api_key"]:
                # Migrate this key to secure storage
                self.secure_storage.store_key(config["name"], config["api_key"])
                # Remove from plaintext config
                config["api_key"] = ""  # Empty string indicates key is in secure storage
                migrated = True
        
        if migrated:
            self._save_config()
    
    def add_api_config(
        self,
        name: str,
        api_key: Optional[str] = None,
        description: Optional[str] = None,
        make_default: bool = False
    ) -> None:
        """Add a new API configuration."""
        # Get API key from env if not provided
        if api_key is None:
            env_var = f"{name.upper()}_ANTHROPIC_API_KEY"
            api_key = os.environ.get(env_var)
            if not api_key:
                raise ValueError(
                    f"API key not provided and {env_var} environment variable not set"
                )
        
        # Check if name already exists
        api_configs = self._data.get("api_configs", [])
        for config in api_configs:
            if config["name"] == name:
                raise ValueError(f"API config with name '{name}' already exists")
        
        # Store API key in secure storage
        self.secure_storage.store_key(name, api_key)
        
        # If this is the first config or make_default is True, set as default
        if make_default or not api_configs:
            for config in api_configs:
                config["default"] = False
        
        # Store metadata without the actual key (empty string indicates secure storage)
        api_config = APIConfig(
            name=name,
            api_key="",  # Empty string indicates key is in secure storage
            description=description,
            default=make_default or not api_configs
        )
        
        api_configs.append(api_config.model_dump())
        self._data["api_configs"] = api_configs
        self._save_config()
    
    def get_api_config(self, name: Optional[str] = None) -> Optional[APIConfig]:
        """Get API configuration by name or default."""
        api_configs = self._data.get("api_configs", [])
        
        config_data = None
        if name:
            for config in api_configs:
                if config["name"] == name:
                    config_data = config
                    break
        else:
            # Return default
            for config in api_configs:
                if config.get("default", False):
                    config_data = config
                    break
        
        if not config_data:
            return None
        
        # Retrieve actual API key from secure storage
        api_key = self.secure_storage.get_key(config_data["name"])
        if not api_key:
            # Fallback to plaintext if not in secure storage (shouldn't happen after migration)
            api_key = config_data.get("api_key", "")
        
        # Return config with actual key
        return APIConfig(
            name=config_data["name"],
            api_key=api_key,
            description=config_data.get("description"),
            default=config_data.get("default", False)
        )
    
    def list_api_configs(self) -> List[APIConfig]:
        """List all API configurations."""
        configs = []
        for c in self._data.get("api_configs", []):
            # Retrieve actual API key from secure storage
            api_key = self.secure_storage.get_key(c["name"])
            if not api_key:
                # Fallback to plaintext
                api_key = c.get("api_key", "")
            
            configs.append(APIConfig(
                name=c["name"],
                api_key=api_key,
                description=c.get("description"),
                default=c.get("default", False)
            ))
        return configs
    
    def add_project_profile(
        self,
        name: str,
        api_config: str,
        system_prompt: Optional[str] = None,
        allowed_commands: Optional[List[str]] = None
    ) -> None:
        """Add a project profile."""
        profiles = self._data.get("project_profiles", [])
        
        profile = ProjectProfile(
            name=name,
            api_config=api_config,
            system_prompt=system_prompt,
            allowed_commands=allowed_commands or ["all"]
        )
        
        profiles.append(profile.model_dump())
        self._data["project_profiles"] = profiles
        self._save_config()
    
    def get_project_profile(self, cwd: Optional[Path] = None) -> Optional[ProjectProfile]:
        """Get project profile for current directory."""
        if cwd is None:
            cwd = Path.cwd()
        
        # Check for .claude-dev-cli file in current or parent directories
        current = cwd
        while current != current.parent:
            config_file = current / ".claude-dev-cli"
            if config_file.exists() and config_file.is_file():
                try:
                    with open(config_file, 'r') as f:
                        data = json.load(f)
                        return ProjectProfile(**data)
                except (json.JSONDecodeError, IOError):
                    # Skip invalid project config files
                    pass
            current = current.parent
        
        return None
    
    def get_model(self) -> str:
        """Get default model."""
        return self._data.get("default_model", "claude-sonnet-4-20250514")
    
    def set_model(self, model: str) -> None:
        """Set default model."""
        self._data["default_model"] = model
        self._save_config()
    
    def get_max_tokens(self) -> int:
        """Get default max tokens."""
        return self._data.get("max_tokens", 4096)
    
    def get_context_config(self) -> ContextConfig:
        """Get context gathering configuration."""
        context_data = self._data.get("context", {})
        return ContextConfig(**context_data) if context_data else ContextConfig()
    
    def get_summarization_config(self) -> SummarizationConfig:
        """Get conversation summarization configuration."""
        summ_data = self._data.get("summarization", {})
        return SummarizationConfig(**summ_data) if summ_data else SummarizationConfig()
    
    # Model Profile Management
    
    def add_model_profile(
        self,
        name: str,
        model_id: str,
        input_price: float,
        output_price: float,
        description: Optional[str] = None,
        use_cases: Optional[List[str]] = None,
        api_config_name: Optional[str] = None,
        make_default: bool = False
    ) -> None:
        """Add a model profile."""
        profiles = self._data.get("model_profiles", [])
        
        # Check if name already exists
        for profile in profiles:
            if profile["name"] == name:
                raise ValueError(f"Model profile '{name}' already exists")
        
        profile = ModelProfile(
            name=name,
            model_id=model_id,
            description=description,
            input_price_per_mtok=input_price,
            output_price_per_mtok=output_price,
            use_cases=use_cases or [],
            api_config_name=api_config_name
        )
        
        profiles.append(profile.model_dump())
        self._data["model_profiles"] = profiles
        
        if make_default:
            if api_config_name:
                # Set as default for specific API config
                self.set_api_default_model_profile(api_config_name, name)
            else:
                # Set as global default
                self._data["default_model_profile"] = name
        
        self._save_config()
    
    def get_model_profile(
        self,
        name: str,
        api_config_name: Optional[str] = None
    ) -> Optional[ModelProfile]:
        """Get model profile by name.
        
        If api_config_name is provided, prefer API-specific profiles.
        """
        profiles = self._data.get("model_profiles", [])
        
        # First, try to find API-specific profile
        if api_config_name:
            for p in profiles:
                if p["name"] == name and p.get("api_config_name") == api_config_name:
                    return ModelProfile(**p)
        
        # Fall back to global profile (api_config_name = None)
        for p in profiles:
            if p["name"] == name and p.get("api_config_name") is None:
                return ModelProfile(**p)
        
        # Fall back to any profile with that name
        for p in profiles:
            if p["name"] == name:
                return ModelProfile(**p)
        
        return None
    
    def list_model_profiles(
        self,
        api_config_name: Optional[str] = None
    ) -> List[ModelProfile]:
        """List model profiles.
        
        If api_config_name is provided, include both global and API-specific profiles.
        """
        profiles = self._data.get("model_profiles", [])
        result = []
        
        for p in profiles:
            profile_api = p.get("api_config_name")
            # Include if: global profile OR matches requested API
            if profile_api is None or (api_config_name and profile_api == api_config_name):
                result.append(ModelProfile(**p))
        
        return result
    
    def remove_model_profile(self, name: str) -> bool:
        """Remove a model profile."""
        profiles = self._data.get("model_profiles", [])
        original_count = len(profiles)
        
        self._data["model_profiles"] = [
            p for p in profiles if p["name"] != name
        ]
        
        if len(self._data["model_profiles"]) < original_count:
            self._save_config()
            return True
        return False
    
    def set_default_model_profile(self, name: str) -> None:
        """Set global default model profile."""
        # Verify profile exists
        if not self.get_model_profile(name):
            raise ValueError(f"Model profile '{name}' not found")
        
        self._data["default_model_profile"] = name
        self._save_config()
    
    def get_default_model_profile(self, api_config_name: Optional[str] = None) -> str:
        """Get default model profile name.
        
        Resolution order:
        1. API-specific default
        2. Global default
        3. Fallback to 'smart'
        """
        # Check API-specific default
        if api_config_name:
            api_configs = self._data.get("api_configs", [])
            for config in api_configs:
                if config["name"] == api_config_name:
                    api_default = config.get("default_model_profile")
                    if api_default:
                        return api_default
        
        # Global default
        return self._data.get("default_model_profile", "smart")
    
    def set_api_default_model_profile(self, api_config_name: str, profile_name: str) -> None:
        """Set default model profile for a specific API config."""
        api_configs = self._data.get("api_configs", [])
        
        found = False
        for config in api_configs:
            if config["name"] == api_config_name:
                config["default_model_profile"] = profile_name
                found = True
                break
        
        if not found:
            raise ValueError(f"API config '{api_config_name}' not found")
        
        self._save_config()
