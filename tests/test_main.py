"""Tests for main CLI module."""

import argparse
import sys
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.config import Config


# Mock the strands imports before importing main
sys.modules['strands'] = MagicMock()
sys.modules['strands_bedrock'] = MagicMock()

from src.main import DSStarCLI, parse_arguments


def test_parse_arguments_defaults():
    """Test that parse_arguments returns correct defaults."""
    with patch('sys.argv', ['main.py']):
        args = parse_arguments()
        
        assert args.config is None
        assert args.model is None
        assert args.region is None
        assert args.verbose is False
        assert args.output_dir is None
        assert args.data_path is None


def test_parse_arguments_with_options():
    """Test parse_arguments with various options."""
    test_args = [
        'main.py',
        '--config', 'config.yaml',
        '--model', 'us.amazon.nova-pro-v1:0',
        '--region', 'us-east-1',
        '--verbose',
        '--output-dir', './custom_output',
        '--data-path', './custom_data.csv'
    ]
    
    with patch('sys.argv', test_args):
        args = parse_arguments()
        
        assert args.config == 'config.yaml'
        assert args.model == 'us.amazon.nova-pro-v1:0'
        assert args.region == 'us-east-1'
        assert args.verbose is True
        assert args.output_dir == './custom_output'
        assert args.data_path == './custom_data.csv'


def test_dsstar_cli_initialization():
    """Test DSStarCLI initialization."""
    config = Config()
    cli = DSStarCLI(config)
    
    assert cli.config == config
    assert cli.orchestrator is None
    assert cli.stream_handler is None


def test_dsstar_cli_initialization_verbose():
    """Test DSStarCLI initialization with verbose mode."""
    config = Config(verbose=True)
    
    with patch('logging.getLogger') as mock_logger:
        cli = DSStarCLI(config)
        assert cli.config.verbose is True


def test_dsstar_cli_display_welcome(capsys):
    """Test that display_welcome prints expected output."""
    config = Config()
    cli = DSStarCLI(config)
    
    cli.display_welcome()
    
    captured = capsys.readouterr()
    assert "DS-Star Multi-Agent System" in captured.out
    assert "Amazon Nova Lite" in captured.out
    assert "Data Analyst" in captured.out
    assert "ML Engineer" in captured.out
    assert "Visualization Expert" in captured.out


def test_dsstar_cli_display_help(capsys):
    """Test that display_help prints expected output."""
    config = Config()
    cli = DSStarCLI(config)
    
    cli.display_help()
    
    captured = capsys.readouterr()
    assert "DS-Star Help" in captured.out
    assert "help" in captured.out
    assert "quit" in captured.out
    assert "clear" in captured.out
    assert "history" in captured.out


def test_dsstar_cli_process_query_no_orchestrator():
    """Test process_query when orchestrator is not initialized."""
    config = Config()
    cli = DSStarCLI(config)
    
    result = cli.process_query("test query")
    assert result is None


def test_dsstar_cli_shutdown():
    """Test graceful shutdown."""
    config = Config()
    cli = DSStarCLI(config)
    
    # Create a mock orchestrator
    mock_orchestrator = Mock()
    cli.orchestrator = mock_orchestrator
    
    cli.shutdown()
    
    # Verify clear_history was called
    mock_orchestrator.clear_history.assert_called_once()


def test_main_with_invalid_credentials():
    """Test main function with invalid credentials."""
    test_args = ['main.py']
    
    with patch('sys.argv', test_args):
        with patch('src.main.Config.load') as mock_config_load:
            with patch('src.main.DSStarCLI') as mock_cli_class:
                # Setup mocks
                mock_config = Config()
                mock_config_load.return_value = mock_config
                
                mock_cli = Mock()
                mock_cli.validate_credentials.return_value = False
                mock_cli_class.return_value = mock_cli
                
                # Import and run main
                from src.main import main
                result = main()
                
                # Should return 1 (failure) when credentials are invalid
                assert result == 1
                mock_cli.validate_credentials.assert_called_once()


def test_main_with_initialization_failure():
    """Test main function when initialization fails."""
    test_args = ['main.py']
    
    with patch('sys.argv', test_args):
        with patch('src.main.Config.load') as mock_config_load:
            with patch('src.main.DSStarCLI') as mock_cli_class:
                # Setup mocks
                mock_config = Config()
                mock_config_load.return_value = mock_config
                
                mock_cli = Mock()
                mock_cli.validate_credentials.return_value = True
                mock_cli.initialize.return_value = False
                mock_cli_class.return_value = mock_cli
                
                # Import and run main
                from src.main import main
                result = main()
                
                # Should return 1 (failure) when initialization fails
                assert result == 1
                mock_cli.initialize.assert_called_once()


def test_main_keyboard_interrupt():
    """Test main function handles KeyboardInterrupt gracefully."""
    test_args = ['main.py']
    
    with patch('sys.argv', test_args):
        with patch('src.main.Config.load') as mock_config_load:
            with patch('src.main.DSStarCLI') as mock_cli_class:
                # Setup mocks
                mock_config = Config()
                mock_config_load.return_value = mock_config
                
                mock_cli = Mock()
                mock_cli.validate_credentials.return_value = True
                mock_cli.initialize.return_value = True
                mock_cli.run.side_effect = KeyboardInterrupt()
                mock_cli_class.return_value = mock_cli
                
                # Import and run main
                from src.main import main
                result = main()
                
                # Should return 0 (success) on KeyboardInterrupt
                assert result == 0
