"""Configuration module for DS-Star multi-agent system."""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# Default model IDs for each provider.
# Keep this in sync with `.env.example` and `README.md`.
DEFAULT_LEMONADE_MODEL_ID = "Qwen3-Next-80B-A3B-Instruct-GGUF"
DEFAULT_OLLAMA_MODEL_ID = "qwen3:30b"
DEFAULT_BEDROCK_MODEL_ID = "us.amazon.nova-lite-v1:0"
DEFAULT_ANTHROPIC_MODEL_ID = "claude-3-5-sonnet-20241022"
DEFAULT_OPENAI_MODEL_ID = "gpt-4o"


@dataclass
class Config:
    """Configuration for DS-Star multi-agent system.
    
    Attributes:
        model_provider: Model provider ("lemonade", "anthropic", "ollama", or "bedrock")
        model_id: Model identifier (e.g., "Qwen3-Next-80B-A3B-Instruct-GGUF" for Lemonade, "claude-3-5-sonnet-20241022" for Anthropic, "qwen3:30b" for Ollama, "us.amazon.nova-lite-v1:0" for Bedrock)
        lemonade_base_url: Lemonade server base URL (default: http://localhost:8000/api/v1)
        anthropic_api_key: Anthropic API key (for anthropic provider)
        ollama_host: Ollama server URL (default: http://127.0.0.1:11434)
        region: AWS region for Bedrock API
        verbose: Enable detailed logging and investigation stream output
        max_tokens: Maximum tokens for model responses
        temperature: Model temperature for response generation
        output_dir: Directory for chart and output files
        data_path: Path to airline operations dataset
        retry_attempts: Maximum retry attempts for API failures
        retry_delay_base: Base delay in seconds for exponential backoff
        
        Security settings:
        open_access_mode: Enable open access mode (default: True, bypasses RLS)
        session_ttl_hours: Session time-to-live in hours (default: 24)
        identity_provider: Identity provider type ("local", "azure_ad", "aws_iam")
        enable_audit_logging: Enable audit logging for access decisions (default: True)
    """
    
    model_provider: str = "lemonade"  # "lemonade" (default), "anthropic", "openai", "ollama", or "bedrock"
    model_id: str = DEFAULT_LEMONADE_MODEL_ID  # Default to Lemonade model
    lemonade_base_url: str = "http://localhost:8000/api/v1"
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_host: str = "http://127.0.0.1:11434"
    region: str = "us-west-2"
    verbose: bool = False
    max_tokens: int = 4096
    temperature: float = 0.3
    output_dir: str = "./output"
    data_path: str = "./data/airline_operations.csv"
    retry_attempts: int = 3
    retry_delay_base: float = 1.0
    
    # Security settings (Requirements 6.1, 6.4)
    open_access_mode: bool = True  # Default: open access, bypasses RLS
    session_ttl_hours: int = 24  # Session time-to-live in hours
    identity_provider: str = "local"  # "local", "azure_ad", "aws_iam"
    enable_audit_logging: bool = True  # Log all access decisions
    
    def _apply_provider_default_model(self) -> None:
        """Apply provider-specific default model if model_id hasn't been explicitly set.
        
        This ensures that when switching providers, the model_id defaults to an
        appropriate value for that provider rather than keeping a model from another provider.
        """
        provider_defaults = {
            "lemonade": DEFAULT_LEMONADE_MODEL_ID,
            "anthropic": DEFAULT_ANTHROPIC_MODEL_ID,
            "openai": DEFAULT_OPENAI_MODEL_ID,
            "ollama": DEFAULT_OLLAMA_MODEL_ID,
            "bedrock": DEFAULT_BEDROCK_MODEL_ID,
        }
        
        # Check if current model_id belongs to a different provider
        other_provider_models = {
            model for provider, model in provider_defaults.items() 
            if provider != self.model_provider
        }
        
        if self.model_id in other_provider_models:
            self.model_id = provider_defaults.get(self.model_provider, self.model_id)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.
        
        Environment variables:
            DS_STAR_MODEL_PROVIDER: Model provider ("lemonade", "anthropic", "openai", "ollama", or "bedrock", default: lemonade)
            DS_STAR_MODEL_ID: Model identifier (default varies by provider)
            DS_STAR_LEMONADE_BASE_URL: Lemonade server base URL (default: http://localhost:8000/api/v1)
            ANTHROPIC_API_KEY: Anthropic API key (required for anthropic provider)
            OPENAI_API_KEY: OpenAI API key (required for openai provider)
            DS_STAR_OLLAMA_HOST: Ollama server URL (default: http://127.0.0.1:11434)
            DS_STAR_REGION or AWS_REGION: AWS region (default: us-west-2)
            DS_STAR_VERBOSE: Enable verbose mode (default: False)
            DS_STAR_MAX_TOKENS: Maximum tokens (default: 4096)
            DS_STAR_TEMPERATURE: Model temperature (default: 0.3)
            DS_STAR_OUTPUT_DIR: Output directory (default: ./output)
            DS_STAR_DATA_PATH: Data file path (default: ./data/airline_operations.csv)
            DS_STAR_RETRY_ATTEMPTS: Retry attempts (default: 3)
            DS_STAR_RETRY_DELAY_BASE: Base retry delay (default: 1.0)
            
            Security settings:
            DS_STAR_OPEN_ACCESS_MODE: Enable open access mode (default: True)
            DS_STAR_SESSION_TTL_HOURS: Session TTL in hours (default: 24)
            DS_STAR_IDENTITY_PROVIDER: Identity provider (default: local)
            DS_STAR_ENABLE_AUDIT_LOGGING: Enable audit logging (default: True)
        
        Returns:
            Config instance with values from environment variables
        """
        config = cls()
        
        # Load model provider
        if model_provider := os.getenv("DS_STAR_MODEL_PROVIDER"):
            config.model_provider = model_provider.lower()

        # Load model ID (if explicitly set)
        if model_id := os.getenv("DS_STAR_MODEL_ID"):
            config.model_id = model_id
        else:
            # Apply provider-specific default if no explicit model_id
            config._apply_provider_default_model()
        
        # Lemonade base URL
        if lemonade_base_url := os.getenv("DS_STAR_LEMONADE_BASE_URL"):
            config.lemonade_base_url = lemonade_base_url
        
        # Anthropic API key
        if anthropic_api_key := os.getenv("ANTHROPIC_API_KEY"):
            config.anthropic_api_key = anthropic_api_key
        
        # OpenAI API key
        if openai_api_key := os.getenv("OPENAI_API_KEY"):
            config.openai_api_key = openai_api_key
        
        # Ollama host
        if ollama_host := os.getenv("DS_STAR_OLLAMA_HOST"):
            config.ollama_host = ollama_host
        
        # Check both DS_STAR_REGION and AWS_REGION
        if region := os.getenv("DS_STAR_REGION") or os.getenv("AWS_REGION"):
            config.region = region
        
        if verbose := os.getenv("DS_STAR_VERBOSE"):
            config.verbose = verbose.lower() in ("true", "1", "yes")
        
        if max_tokens := os.getenv("DS_STAR_MAX_TOKENS"):
            try:
                config.max_tokens = int(max_tokens)
            except ValueError:
                logger.warning(
                    f"Invalid DS_STAR_MAX_TOKENS value '{max_tokens}', using default {config.max_tokens}"
                )
        
        if temperature := os.getenv("DS_STAR_TEMPERATURE"):
            try:
                config.temperature = float(temperature)
            except ValueError:
                logger.warning(
                    f"Invalid DS_STAR_TEMPERATURE value '{temperature}', using default {config.temperature}"
                )
        
        if output_dir := os.getenv("DS_STAR_OUTPUT_DIR"):
            config.output_dir = output_dir
        
        if data_path := os.getenv("DS_STAR_DATA_PATH"):
            config.data_path = data_path
        
        if retry_attempts := os.getenv("DS_STAR_RETRY_ATTEMPTS"):
            try:
                config.retry_attempts = int(retry_attempts)
            except ValueError:
                logger.warning(
                    f"Invalid DS_STAR_RETRY_ATTEMPTS value '{retry_attempts}', using default {config.retry_attempts}"
                )
        
        if retry_delay_base := os.getenv("DS_STAR_RETRY_DELAY_BASE"):
            try:
                config.retry_delay_base = float(retry_delay_base)
            except ValueError:
                logger.warning(
                    f"Invalid DS_STAR_RETRY_DELAY_BASE value '{retry_delay_base}', using default {config.retry_delay_base}"
                )
        
        # Security settings (Requirements 6.1, 6.4)
        if open_access_mode := os.getenv("DS_STAR_OPEN_ACCESS_MODE"):
            config.open_access_mode = open_access_mode.lower() in ("true", "1", "yes")
        
        if session_ttl_hours := os.getenv("DS_STAR_SESSION_TTL_HOURS"):
            try:
                config.session_ttl_hours = int(session_ttl_hours)
            except ValueError:
                logger.warning(
                    f"Invalid DS_STAR_SESSION_TTL_HOURS value '{session_ttl_hours}', using default {config.session_ttl_hours}"
                )
        
        if identity_provider := os.getenv("DS_STAR_IDENTITY_PROVIDER"):
            config.identity_provider = identity_provider.lower()
        
        if enable_audit_logging := os.getenv("DS_STAR_ENABLE_AUDIT_LOGGING"):
            config.enable_audit_logging = enable_audit_logging.lower() in ("true", "1", "yes")
        
        return config
    
    @classmethod
    def from_file(cls, path: str) -> "Config":
        """Load configuration from JSON or YAML file.
        
        Args:
            path: Path to configuration file (.json or .yaml/.yml)
        
        Returns:
            Config instance with values from file
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is unsupported or invalid
        """
        file_path = Path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        # Determine file format from extension
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == ".json":
                with open(file_path, "r") as f:
                    data = json.load(f)
            elif suffix in (".yaml", ".yml"):
                with open(file_path, "r") as f:
                    data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported config file format: {suffix}. Use .json, .yaml, or .yml")
            
            # Create config with defaults, then update with file values
            config = cls()
            
            # Update fields from file data with validation
            if "model_provider" in data:
                config.model_provider = str(data["model_provider"]).lower()

            # Load model ID (if explicitly set)
            if "model_id" in data:
                config.model_id = str(data["model_id"])
            else:
                # Apply provider-specific default if no explicit model_id
                config._apply_provider_default_model()
            
            if "anthropic_api_key" in data:
                config.anthropic_api_key = str(data["anthropic_api_key"])
            
            if "openai_api_key" in data:
                config.openai_api_key = str(data["openai_api_key"])
            
            if "ollama_host" in data:
                config.ollama_host = str(data["ollama_host"])
            
            if "region" in data:
                config.region = str(data["region"])
            
            if "verbose" in data:
                config.verbose = bool(data["verbose"])
            
            if "max_tokens" in data:
                try:
                    config.max_tokens = int(data["max_tokens"])
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid max_tokens value in config file, using default {config.max_tokens}"
                    )
            
            if "temperature" in data:
                try:
                    config.temperature = float(data["temperature"])
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid temperature value in config file, using default {config.temperature}"
                    )
            
            if "output_dir" in data:
                config.output_dir = str(data["output_dir"])
            
            if "data_path" in data:
                config.data_path = str(data["data_path"])
            
            if "retry_attempts" in data:
                try:
                    config.retry_attempts = int(data["retry_attempts"])
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid retry_attempts value in config file, using default {config.retry_attempts}"
                    )
            
            if "retry_delay_base" in data:
                try:
                    config.retry_delay_base = float(data["retry_delay_base"])
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid retry_delay_base value in config file, using default {config.retry_delay_base}"
                    )
            
            # Security settings (Requirements 6.1, 6.4)
            if "open_access_mode" in data:
                config.open_access_mode = bool(data["open_access_mode"])
            
            if "session_ttl_hours" in data:
                try:
                    config.session_ttl_hours = int(data["session_ttl_hours"])
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid session_ttl_hours value in config file, using default {config.session_ttl_hours}"
                    )
            
            if "identity_provider" in data:
                config.identity_provider = str(data["identity_provider"]).lower()
            
            if "enable_audit_logging" in data:
                config.enable_audit_logging = bool(data["enable_audit_logging"])
            
            # Support nested security section in config file
            if "security" in data and isinstance(data["security"], dict):
                security = data["security"]
                if "open_access_mode" in security:
                    config.open_access_mode = bool(security["open_access_mode"])
                if "session_ttl_hours" in security:
                    try:
                        config.session_ttl_hours = int(security["session_ttl_hours"])
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Invalid security.session_ttl_hours value in config file, using default {config.session_ttl_hours}"
                        )
                if "identity_provider" in security:
                    config.identity_provider = str(security["identity_provider"]).lower()
                if "enable_audit_logging" in security:
                    config.enable_audit_logging = bool(security["enable_audit_logging"])
            
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
    
    @classmethod
    def load(cls, config_file: Optional[str] = None) -> "Config":
        """Load configuration with precedence: env vars > file > defaults.
        
        Args:
            config_file: Optional path to config file. If provided, loads from file first,
                        then overrides with environment variables.
        
        Returns:
            Config instance with merged values
        """
        # Best-effort load `.env` (if present) so local dev config works without
        # manually exporting environment variables.
        try:
            from dotenv import load_dotenv  # type: ignore

            env_path = Path.cwd() / ".env"
            if env_path.exists():
                load_dotenv(dotenv_path=env_path, override=False)
        except Exception:
            # ImportError (python-dotenv missing) or any dotenv parsing issues
            # should not prevent the app from starting with defaults.
            pass

        if config_file:
            try:
                config = cls.from_file(config_file)
                logger.info(f"Loaded configuration from file: {config_file}")
            except (FileNotFoundError, ValueError) as e:
                logger.warning(f"Could not load config file: {e}. Using defaults.")
                config = cls()
        else:
            config = cls()
        
        # Override with environment variables
        env_config = cls.from_env()
        
        # Merge: only override if env var was explicitly set (differs from default)
        default_config = cls()
        
        if env_config.model_provider != default_config.model_provider:
            config.model_provider = env_config.model_provider
        if env_config.model_id != default_config.model_id:
            config.model_id = env_config.model_id
        if env_config.anthropic_api_key is not None:
            config.anthropic_api_key = env_config.anthropic_api_key
        if env_config.openai_api_key is not None:
            config.openai_api_key = env_config.openai_api_key
        if env_config.ollama_host != default_config.ollama_host:
            config.ollama_host = env_config.ollama_host
        if env_config.region != default_config.region:
            config.region = env_config.region
        if env_config.verbose != default_config.verbose:
            config.verbose = env_config.verbose
        if env_config.max_tokens != default_config.max_tokens:
            config.max_tokens = env_config.max_tokens
        if env_config.temperature != default_config.temperature:
            config.temperature = env_config.temperature
        if env_config.output_dir != default_config.output_dir:
            config.output_dir = env_config.output_dir
        if env_config.data_path != default_config.data_path:
            config.data_path = env_config.data_path
        if env_config.retry_attempts != default_config.retry_attempts:
            config.retry_attempts = env_config.retry_attempts
        if env_config.retry_delay_base != default_config.retry_delay_base:
            config.retry_delay_base = env_config.retry_delay_base
        
        # Security settings (Requirements 6.1, 6.4)
        if env_config.open_access_mode != default_config.open_access_mode:
            config.open_access_mode = env_config.open_access_mode
        if env_config.session_ttl_hours != default_config.session_ttl_hours:
            config.session_ttl_hours = env_config.session_ttl_hours
        if env_config.identity_provider != default_config.identity_provider:
            config.identity_provider = env_config.identity_provider
        if env_config.enable_audit_logging != default_config.enable_audit_logging:
            config.enable_audit_logging = env_config.enable_audit_logging

        # Apply provider-specific default model if needed
        config._apply_provider_default_model()
        
        return config
    
    def validate(self) -> bool:
        """Validate configuration values.
        
        Returns:
            True if configuration is valid
        
        Raises:
            ValueError: If any configuration value is invalid
        """
        # Validate model provider
        valid_providers = {"lemonade", "anthropic", "openai", "ollama", "bedrock"}
        if self.model_provider not in valid_providers:
            raise ValueError(
                f"model_provider must be one of {valid_providers}, got '{self.model_provider}'"
            )
        
        # Validate provider-specific requirements
        if self.model_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("anthropic_api_key is required when using Anthropic provider")
        
        if self.model_provider == "openai" and not self.openai_api_key:
            raise ValueError("openai_api_key is required when using OpenAI provider")
        
        if self.max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")
        
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError(f"temperature must be between 0.0 and 1.0, got {self.temperature}")
        
        if self.retry_attempts < 0:
            raise ValueError(f"retry_attempts must be non-negative, got {self.retry_attempts}")
        
        if self.retry_delay_base <= 0:
            raise ValueError(f"retry_delay_base must be positive, got {self.retry_delay_base}")
        
        # Validate security settings (Requirements 6.1, 6.4)
        valid_identity_providers = {"local", "azure_ad", "aws_iam"}
        if self.identity_provider not in valid_identity_providers:
            raise ValueError(
                f"identity_provider must be one of {valid_identity_providers}, got '{self.identity_provider}'"
            )
        
        if self.session_ttl_hours <= 0:
            raise ValueError(f"session_ttl_hours must be positive, got {self.session_ttl_hours}")
        
        return True
