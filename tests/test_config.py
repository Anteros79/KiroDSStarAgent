"""Tests for configuration module."""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.config import Config


def test_config_defaults():
    """Test that Config has correct default values."""
    config = Config()
    
    assert config.model_id == "us.amazon.nova-lite-v1:0"
    assert config.region == "us-west-2"
    assert config.verbose is False
    assert config.max_tokens == 4096
    assert config.temperature == 0.3
    assert config.output_dir == "./output"
    assert config.data_path == "./data/airline_operations.csv"
    assert config.retry_attempts == 3
    assert config.retry_delay_base == 1.0


def test_config_from_env(monkeypatch):
    """Test loading configuration from environment variables."""
    # Set environment variables
    monkeypatch.setenv("DS_STAR_MODEL_ID", "us.amazon.nova-pro-v1:0")
    monkeypatch.setenv("DS_STAR_REGION", "us-east-1")
    monkeypatch.setenv("DS_STAR_VERBOSE", "true")
    monkeypatch.setenv("DS_STAR_MAX_TOKENS", "8192")
    monkeypatch.setenv("DS_STAR_TEMPERATURE", "0.7")
    monkeypatch.setenv("DS_STAR_OUTPUT_DIR", "./custom_output")
    monkeypatch.setenv("DS_STAR_DATA_PATH", "./custom_data.csv")
    monkeypatch.setenv("DS_STAR_RETRY_ATTEMPTS", "5")
    monkeypatch.setenv("DS_STAR_RETRY_DELAY_BASE", "2.0")
    
    config = Config.from_env()
    
    assert config.model_id == "us.amazon.nova-pro-v1:0"
    assert config.region == "us-east-1"
    assert config.verbose is True
    assert config.max_tokens == 8192
    assert config.temperature == 0.7
    assert config.output_dir == "./custom_output"
    assert config.data_path == "./custom_data.csv"
    assert config.retry_attempts == 5
    assert config.retry_delay_base == 2.0


def test_config_from_env_aws_region_fallback(monkeypatch):
    """Test that AWS_REGION is used as fallback for region."""
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    
    config = Config.from_env()
    assert config.region == "eu-west-1"


def test_config_from_env_invalid_values(monkeypatch, caplog):
    """Test that invalid environment values fall back to defaults with warnings."""
    monkeypatch.setenv("DS_STAR_MAX_TOKENS", "invalid")
    monkeypatch.setenv("DS_STAR_TEMPERATURE", "not_a_float")
    monkeypatch.setenv("DS_STAR_RETRY_ATTEMPTS", "bad")
    
    config = Config.from_env()
    
    # Should use defaults
    assert config.max_tokens == 4096
    assert config.temperature == 0.3
    assert config.retry_attempts == 3
    
    # Should have logged warnings
    assert "Invalid DS_STAR_MAX_TOKENS" in caplog.text
    assert "Invalid DS_STAR_TEMPERATURE" in caplog.text
    assert "Invalid DS_STAR_RETRY_ATTEMPTS" in caplog.text


def test_config_from_json_file():
    """Test loading configuration from JSON file."""
    config_data = {
        "model_id": "us.amazon.nova-micro-v1:0",
        "region": "ap-southeast-1",
        "verbose": True,
        "max_tokens": 2048,
        "temperature": 0.5,
        "output_dir": "./json_output",
        "data_path": "./json_data.csv",
        "retry_attempts": 2,
        "retry_delay_base": 0.5
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = Config.from_file(temp_path)
        
        assert config.model_id == "us.amazon.nova-micro-v1:0"
        assert config.region == "ap-southeast-1"
        assert config.verbose is True
        assert config.max_tokens == 2048
        assert config.temperature == 0.5
        assert config.output_dir == "./json_output"
        assert config.data_path == "./json_data.csv"
        assert config.retry_attempts == 2
        assert config.retry_delay_base == 0.5
    finally:
        os.unlink(temp_path)


def test_config_from_yaml_file():
    """Test loading configuration from YAML file."""
    config_data = {
        "model_id": "us.amazon.nova-micro-v1:0",
        "region": "ap-southeast-1",
        "verbose": True,
        "max_tokens": 2048,
        "temperature": 0.5,
        "output_dir": "./yaml_output",
        "data_path": "./yaml_data.csv",
        "retry_attempts": 2,
        "retry_delay_base": 0.5
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = Config.from_file(temp_path)
        
        assert config.model_id == "us.amazon.nova-micro-v1:0"
        assert config.region == "ap-southeast-1"
        assert config.verbose is True
        assert config.max_tokens == 2048
        assert config.temperature == 0.5
        assert config.output_dir == "./yaml_output"
        assert config.data_path == "./yaml_data.csv"
        assert config.retry_attempts == 2
        assert config.retry_delay_base == 0.5
    finally:
        os.unlink(temp_path)


def test_config_from_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        Config.from_file("nonexistent.json")


def test_config_from_file_unsupported_format():
    """Test that ValueError is raised for unsupported file format."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("some content")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Unsupported config file format"):
            Config.from_file(temp_path)
    finally:
        os.unlink(temp_path)


def test_config_from_file_invalid_json():
    """Test that ValueError is raised for invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{invalid json")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Invalid JSON"):
            Config.from_file(temp_path)
    finally:
        os.unlink(temp_path)


def test_config_load_precedence(monkeypatch):
    """Test that environment variables override file values."""
    # Create a config file
    config_data = {
        "model_id": "file-model",
        "region": "file-region",
        "max_tokens": 1024
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        # Set environment variable that should override
        monkeypatch.setenv("DS_STAR_MODEL_ID", "env-model")
        
        config = Config.load(temp_path)
        
        # Env var should override file
        assert config.model_id == "env-model"
        # File value should be used where no env var
        assert config.region == "file-region"
        assert config.max_tokens == 1024
    finally:
        os.unlink(temp_path)


def test_config_validate():
    """Test configuration validation."""
    config = Config()
    assert config.validate() is True
    
    # Test invalid max_tokens
    config.max_tokens = -1
    with pytest.raises(ValueError, match="max_tokens must be positive"):
        config.validate()
    
    # Test invalid temperature
    config = Config()
    config.temperature = 1.5
    with pytest.raises(ValueError, match="temperature must be between"):
        config.validate()
    
    # Test invalid retry_attempts
    config = Config()
    config.retry_attempts = -1
    with pytest.raises(ValueError, match="retry_attempts must be non-negative"):
        config.validate()
    
    # Test invalid retry_delay_base
    config = Config()
    config.retry_delay_base = -0.5
    with pytest.raises(ValueError, match="retry_delay_base must be positive"):
        config.validate()
