# HelloAgent

A simple AgentCore-compatible agent built with the Strands SDK and Amazon Bedrock.

## Features

- **Time Tool**: Get the current date and time
- **Calculator Tool**: Evaluate basic math expressions
- Uses Claude Sonnet 4 via Amazon Bedrock

## Requirements

- Python >= 3.10
- AWS credentials configured for Bedrock access

## Dependencies

```
strands-agents>=1.13.0
strands-agents-tools>=0.2.16
bedrock-agentcore>=1.0.3
python-dotenv>=1.2.1
boto3>=1.42.1
```

## Installation

```bash
cd HelloAgent
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Project Structure

```
HelloAgent/
├── src/
│   ├── main.py      # Agent entrypoint with tools
│   └── __init__.py
├── test/
│   ├── test_main.py
│   └── __init__.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Usage

### Local Development

Run the agent directly:

```bash
python src/main.py
```

Or use AgentCore CLI:

```bash
agentcore dev        # Start local server on 0.0.0.0:8080
agentcore invoke --dev "What time is it?"
```

### Deployment

```bash
agentcore configure  # Optional: customize settings
agentcore deploy     # Deploy to Amazon Bedrock AgentCore
agentcore invoke "What can you do?"
```

## Example Queries

- "What time is it?"
- "Calculate 25 * 4 + 10"
- "What's 100 / 5?"
