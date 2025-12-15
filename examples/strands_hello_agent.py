"""
Simple Strands Agent Example

This demonstrates the basic pattern for creating an AI agent with tools.
Make sure you have API credentials set before running:
  - AWS_BEDROCK_API_KEY (for Bedrock - default)
  - ANTHROPIC_API_KEY (for Anthropic)
  - OPENAI_API_KEY (for OpenAI)
"""

from strands import Agent, tool
from strands_tools import calculator

# Define a custom tool
@tool
def greet(name: str) -> str:
    """Greet someone by name.
    
    Args:
        name: The person's name to greet
    """
    return f"Hello, {name}! Welcome to Strands Agents!"


# Create an agent with tools
# Uses Bedrock Claude 4 Sonnet by default
agent = Agent(
    tools=[calculator, greet],
    system_prompt="You are a friendly assistant that can do math and greet people."
)

# Test the agent
if __name__ == "__main__":
    print("Testing the Strands Agent...")
    print("-" * 40)
    
    # Test greeting
    response = agent("Please greet Alice")
    print(f"Response: {response}")
    print("-" * 40)
    
    # Test calculator
    response = agent("What is 42 * 17?")
    print(f"Response: {response}")
    print("-" * 40)
    
    # Test conversation memory
    agent("My favorite number is 7")
    response = agent("What's my favorite number multiplied by 6?")
    print(f"Response: {response}")
