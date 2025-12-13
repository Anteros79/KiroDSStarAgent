"""Pytest configuration and fixtures for DS-Star tests."""

import sys
import pytest


# Create a proper mock for the tool decorator that acts as a passthrough
class MockStrandsModule:
    @staticmethod
    def tool(func):
        """Mock tool decorator that just returns the function unchanged."""
        return func
    
    class Agent:
        pass


class MockBedrockModule:
    class BedrockModel:
        pass


def pytest_configure(config):
    """
    Pytest hook that runs before test collection.
    This is the earliest point we can mock the strands library.
    """
    # Remove any existing strands modules from sys.modules to force our mock
    modules_to_remove = [
        'strands',
        'strands_bedrock',
        'strands.tool',
        'strands_agents',
        'src.agents.specialists.data_analyst',
        'src.agents.specialists.ml_engineer',
        'src.agents.specialists.visualization_expert',
        'src.agents.specialists',
    ]
    
    for module in modules_to_remove:
        if module in sys.modules:
            del sys.modules[module]
    
    # Mock strands modules before any imports happen
    sys.modules['strands'] = MockStrandsModule()
    sys.modules['strands_bedrock'] = MockBedrockModule()
    sys.modules['strands_agents'] = MockStrandsModule()


# Also set up the mock at module level as a fallback
if 'strands' not in sys.modules:
    sys.modules['strands'] = MockStrandsModule()
if 'strands_bedrock' not in sys.modules:
    sys.modules['strands_bedrock'] = MockBedrockModule()
if 'strands_agents' not in sys.modules:
    sys.modules['strands_agents'] = MockStrandsModule()
