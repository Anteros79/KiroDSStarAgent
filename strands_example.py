"""
Simple Strands Agent Example

This example creates an agent with community tools that can:
- Perform calculations
- Execute Python code
- Make HTTP requests
"""

from strands import Agent
from strands_tools import calculator, python_repl, http_request

# Create an agent with community tools
# Uses Bedrock Claude 4 Sonnet by default (if AWS_BEDROCK_API_KEY is set)
agent = Agent(
    tools=[calculator, python_repl, http_request],
    system_prompt="You are a helpful assistant with access to tools for calculations, code execution, and web requests."
)

# Example 1: Simple calculation
print("Example 1: Calculation")
print("-" * 50)
response = agent("What is 15% of 2,450?")
print(f"Response: {response}\n")

# Example 2: Using conversation history
print("Example 2: Conversation Context")
print("-" * 50)
agent("My favorite number is 42")
response = agent("What's my favorite number multiplied by 3?")
print(f"Response: {response}\n")

# Example 3: Python code execution
print("Example 3: Python Code Execution")
print("-" * 50)
response = agent("Generate a list of the first 10 Fibonacci numbers using Python")
print(f"Response: {response}\n")
