# Error Handling Components

This directory contains error handling utilities for the DS-Star multi-agent system.

## BedrockRetryHandler

Handles transient Bedrock API failures with exponential backoff.

### Usage

```python
from src.handlers import BedrockRetryHandler

# Create handler with custom settings
handler = BedrockRetryHandler(max_attempts=3, base_delay=1.0)

# Execute function with retry logic
result = handler.execute_with_retry(lambda: bedrock_api_call())

# Or use the decorator
from src.handlers import with_retry

@with_retry(max_attempts=3, base_delay=1.0)
def my_api_call():
    return bedrock.invoke_model(...)
```

### Exponential Backoff

The retry delays follow the formula: `delay = base_delay * (2 ^ attempt)`

For example, with `base_delay=1.0`:
- Attempt 0: 1s delay
- Attempt 1: 2s delay  
- Attempt 2: 4s delay

### Retryable Errors

The handler automatically retries on:
- Throttling exceptions
- Service unavailable errors
- Connection errors
- Timeout errors
- Rate limit errors

Non-retryable errors (like validation errors) are raised immediately.

## safe_specialist_call

Wraps specialist agent invocations with error handling and fallback responses.

### Usage

```python
from src.handlers import safe_specialist_call
from src.agents.specialists.data_analyst import data_analyst

# Call specialist with error handling
response = safe_specialist_call(data_analyst, "What is the average delay?")

# Response is always a SpecialistResponse, even on error
print(response.response)  # User-friendly message
```

### Error Messages

The wrapper provides context-aware error messages:
- **Timeout errors**: "taking longer than expected"
- **Connection errors**: "connection issues"
- **Authentication errors**: "authentication issue"
- **Not found errors**: "couldn't find the required resources"
- **Invalid input**: "received an invalid request"
- **Generic**: "encountered an issue"

### With Context

For specialists that accept context:

```python
from src.handlers import safe_specialist_call_with_context

response = safe_specialist_call_with_context(
    data_analyst,
    "What about delays?",
    {"previous_query": "Show me flight data"}
)
```

## Integration Example

Here's how to use both components together in the orchestrator:

```python
from src.handlers import BedrockRetryHandler, safe_specialist_call
from src.config import Config

# Initialize retry handler from config
config = Config.from_env()
retry_handler = BedrockRetryHandler(
    max_attempts=config.retry_attempts,
    base_delay=config.retry_delay_base
)

# Call specialist with both retry and error handling
def invoke_specialist(specialist_func, query):
    # Wrap the specialist call with retry logic
    return retry_handler.execute_with_retry(
        lambda: safe_specialist_call(specialist_func, query)
    )

# Use it
response = invoke_specialist(data_analyst, "Analyze delays")
```

## Testing

All error handling components are thoroughly tested in `tests/test_error_handling.py`:
- Retry logic and exponential backoff
- Error detection and classification
- Fallback response generation
- Decorator functionality

Run tests with:
```bash
pytest tests/test_error_handling.py -v
```
