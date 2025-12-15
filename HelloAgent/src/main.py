"""
Simple AgentCore Agent Example using Strands SDK.

This demonstrates the basic structure of an AgentCore-compatible agent.
"""
import os
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Create the AgentCore app wrapper
app = BedrockAgentCoreApp()


# Define a simple tool the agent can use
@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculate(expression: str) -> str:
    """
    Evaluate a simple math expression.
    
    Args:
        expression: A math expression like "2 + 2" or "10 * 5"
    """
    try:
        # Only allow safe math operations
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "Error: Only basic math operations are allowed"
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


# Create the Strands agent with Bedrock model
agent = Agent(
    model=BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0"),
    system_prompt="""You are a helpful assistant. You can:
    - Tell the current time using the get_current_time tool
    - Perform calculations using the calculate tool
    
    Be concise and helpful in your responses.""",
    tools=[get_current_time, calculate],
)


# Define the entrypoint for AgentCore
@app.entrypoint
def invoke(prompt: str, **kwargs) -> str:
    """
    Main entrypoint for the agent.
    
    Args:
        prompt: The user's input message
        
    Returns:
        The agent's response
    """
    response = agent(prompt)
    return str(response)


# For local development
if __name__ == "__main__":
    # Test the agent locally
    test_prompt = "What time is it?"
    print(f"Testing with: {test_prompt}")
    result = invoke(test_prompt)
    print(f"Response: {result}")
