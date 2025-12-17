"""Configuration module for DS-Star multi-agent system."""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# Default local model tag for Ollama.
# Keep this in sync with `.env.example` and `README.md`.
DEFAULT_OLLAMA_MODEL_ID = "qwen3:30b"
DEFAULT_BEDROCK_MODEL_ID = "us.amazon.nova-lite-v1:0"


@dataclass
class Config:
    """Configuration for DS-Star multi-agent system.
    
    Attributes:
        model_provider: Model provider ("ollama" or "bedrock")
        model_id: Model identifier (e.g., "gemma3:27b" for Ollama, "us.amazon.nova-lite-v1:0" for Bedrock)
        ollama_host: Ollama server URL (default: http://127.0.0.1:11434)
        region: AWS region for Bedrock API
        verbose: Enable detailed logging and investigation stream output
        max_tokens: Maximum tokens for model responses
        temperature: Model temperature for response generation
        output_dir: Directory for chart and output files
        data_path: Path to airline operations dataset
        retry_attempts: Maximum retry attempts for API failures
        retry_delay_base: Base delay in seconds for exponential backoff
    """
    
    model_provider: str = "ollama"  # "ollama" or "bedrock"
    model_id: str = DEFAULT_OLLAMA_MODEL_ID  # Default to local Ollama model tag
    ollama_host: str = "http://127.0.0.1:11434"
    region: str = "us-west-2"
    verbose: bool = False
    max_tokens: int = 4096
    temperature: float = 0.3
    output_dir: str = "./output"
    data_path: str = "./data/airline_operations.csv"
    retry_attempts: int = 3
    retry_delay_base: float = 1.0
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.
        
        Environment variables:
            DS_STAR_MODEL_PROVIDER: Model provider ("ollama" or "bedrock", default: ollama)
            DS_STAR_MODEL_ID: Model identifier (default: gemma3:27b for ollama)
            DS_STAR_OLLAMA_HOST: Ollama server URL (default: http://127.0.0.1:11434)
            DS_STAR_REGION or AWS_REGION: AWS region (default: us-west-2)
            DS_STAR_VERBOSE: Enable verbose mode (default: False)
            DS_STAR_MAX_TOKENS: Maximum tokens (default: 4096)
            DS_STAR_TEMPERATURE: Model temperature (default: 0.3)
            DS_STAR_OUTPUT_DIR: Output directory (default: ./output)
            DS_STAR_DATA_PATH: Data file path (default: ./data/airline_operations.csv)
            DS_STAR_RETRY_ATTEMPTS: Retry attempts (default: 3)
            DS_STAR_RETRY_DELAY_BASE: Base retry delay (default: 1.0)
        
        Returns:
            Config instance with values from environment variables
        """
        config = cls()
        
        # Load model provider
        if model_provider := os.getenv("DS_STAR_MODEL_PROVIDER"):
            config.model_provider = model_provider.lower()

        # Provider-specific default model if the user didn't explicitly set one.
        if config.model_provider == "bedrock" and not os.getenv("DS_STAR_MODEL_ID"):
            config.model_id = DEFAULT_BEDROCK_MODEL_ID
        
        # Load each field from environment with validation
        if model_id := os.getenv("DS_STAR_MODEL_ID"):
            config.model_id = model_id
        
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

            # If the config switches to Bedrock but doesn't specify a model_id,
            # use the Bedrock default rather than an Ollama model tag.
            if config.model_provider == "bedrock" and "model_id" not in data:
                config.model_id = DEFAULT_BEDROCK_MODEL_ID
            
            if "model_id" in data:
                config.model_id = str(data["model_id"])
            
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

        # Provider-specific default model if provider changed but model_id wasn't set.
        if config.model_provider == "bedrock" and config.model_id == DEFAULT_OLLAMA_MODEL_ID:
            config.model_id = DEFAULT_BEDROCK_MODEL_ID
        
        return config
    
    def validate(self) -> bool:
        """Validate configuration values.
        
        Returns:
            True if configuration is valid
        
        Raises:
            ValueError: If any configuration value is invalid
        """
        if self.max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")
        
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError(f"temperature must be between 0.0 and 1.0, got {self.temperature}")
        
        if self.retry_attempts < 0:
            raise ValueError(f"retry_attempts must be non-negative, got {self.retry_attempts}")
        
        if self.retry_delay_base <= 0:
            raise ValueError(f"retry_delay_base must be positive, got {self.retry_delay_base}")
        
        return True
