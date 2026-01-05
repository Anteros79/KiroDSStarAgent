# Lemonade Server Integration

## Overview

Added support for Lemonade Server as a model provider in the DS-Star Multi-Agent System. Lemonade Server is an OpenAI-compatible local LLM inference server optimized for AMD GPUs and NPUs.

## What is Lemonade Server?

[Lemonade Server](https://lemonade-server.ai/) provides an OpenAI-compatible API for running local LLMs, allowing you to:
- Run models locally on your AMD Ryzen AI NPU and iGPU
- Use the standard OpenAI API specification
- Avoid cloud API costs and maintain data privacy
- Access models through `http://localhost:8000/api/v1`

## Changes Made

### 1. Configuration (`src/config.py`)

**Added:**
- `DEFAULT_LEMONADE_MODEL_ID = "Qwen3-Next-80B-A3B-Instruct-GGUF"`
- `lemonade_base_url` field (default: `http://localhost:8000/api/v1`)
- Support for `DS_STAR_LEMONADE_BASE_URL` environment variable
- Lemonade as the **default provider** (changed from anthropic)

**Updated:**
- `model_provider` now supports: `"lemonade"`, `"anthropic"`, `"openai"`, `"ollama"`, or `"bedrock"`
- Provider validation includes lemonade
- Provider-specific default model logic includes lemonade

### 2. Main Application (`src/main.py`)

**Added:**
- Import of `OpenAIModel` from `strands.models.openai`
- Lemonade model initialization using OpenAIModel with custom base_url
- Validation for Lemonade server connection

**Model Initialization:**
```python
if self.config.model_provider == "lemonade":
    model = OpenAIModel(
        model_id=self.config.model_id,
        base_url=self.config.lemonade_base_url,
        api_key="not-needed",  # Lemonade doesn't require an API key
        max_tokens=self.config.max_tokens,
        temperature=self.config.temperature
    )
```

### 3. Environment Configuration (`.env.example`)

**Updated to show Lemonade as default:**
```bash
# Model Provider: "lemonade" (default), "anthropic", "openai", "ollama", or "bedrock"
DS_STAR_MODEL_PROVIDER=lemonade

# Lemonade Configuration (when using model_provider=lemonade)
DS_STAR_MODEL_ID=Qwen3-Next-80B-A3B-Instruct-GGUF
DS_STAR_LEMONADE_BASE_URL=http://localhost:8000/api/v1
```

## Usage

### Quick Start with Lemonade

1. **Install and start Lemonade Server** (see [Lemonade documentation](https://lemonade-server.ai/server/))

2. **Use default configuration** (Lemonade is now the default):
   ```bash
   python src/main.py
   ```

3. **Or explicitly set in `.env`:**
   ```bash
   DS_STAR_MODEL_PROVIDER=lemonade
   DS_STAR_MODEL_ID=Qwen3-Next-80B-A3B-Instruct-GGUF
   DS_STAR_LEMONADE_BASE_URL=http://localhost:8000/api/v1
   ```

### Switching Between Providers

The system still supports all previous providers:

**Lemonade (default):**
```bash
DS_STAR_MODEL_PROVIDER=lemonade
DS_STAR_MODEL_ID=Qwen3-Next-80B-A3B-Instruct-GGUF
```

**Anthropic:**
```bash
DS_STAR_MODEL_PROVIDER=anthropic
DS_STAR_MODEL_ID=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=your_api_key_here
```

**OpenAI:**
```bash
DS_STAR_MODEL_PROVIDER=openai
DS_STAR_MODEL_ID=gpt-4o
OPENAI_API_KEY=your_api_key_here
```

**Ollama:**
```bash
DS_STAR_MODEL_PROVIDER=ollama
DS_STAR_MODEL_ID=qwen3:30b
DS_STAR_OLLAMA_HOST=http://localhost:11434
```

**AWS Bedrock:**
```bash
DS_STAR_MODEL_PROVIDER=bedrock
DS_STAR_MODEL_ID=us.amazon.nova-lite-v1:0
AWS_REGION=us-west-2
```

## Configuration Options

### Lemonade-Specific Settings

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DS_STAR_LEMONADE_BASE_URL` | `http://localhost:8000/api/v1` | Lemonade server API endpoint |
| `DS_STAR_MODEL_ID` | `Qwen3-Next-80B-A3B-Instruct-GGUF` | Model name loaded in Lemonade |

### Common Settings (All Providers)

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DS_STAR_MAX_TOKENS` | `4096` | Maximum tokens for responses |
| `DS_STAR_TEMPERATURE` | `0.3` | Model temperature (0.0-1.0) |
| `DS_STAR_VERBOSE` | `false` | Enable detailed logging |

## Benefits of Lemonade

1. **Local Execution**: Run models entirely on your machine
2. **Privacy**: No data sent to cloud services
3. **Cost**: No API usage fees
4. **Performance**: Optimized for AMD Ryzen AI hardware
5. **Compatibility**: Standard OpenAI API means easy integration

## Troubleshooting

### Connection Issues

If you see "Lemonade server connection validation failed":

1. Verify Lemonade Server is running:
   ```bash
   # Check if server is accessible
   curl http://localhost:8000/api/v1/models
   ```

2. Check the model is loaded in Lemonade Server

3. Verify the base URL matches your Lemonade configuration

### Model Not Found

If the model ID doesn't match what's loaded in Lemonade:

1. Check loaded models in Lemonade Server UI
2. Update `DS_STAR_MODEL_ID` to match the loaded model name

## Technical Details

- Uses `strands.models.openai.OpenAIModel` with custom `base_url`
- No API key required (uses placeholder "not-needed")
- Fully compatible with OpenAI API specification
- Supports streaming, tool calling, and all DS-STAR features

## References

- [Lemonade Server Documentation](https://lemonade-server.ai/server/)
- [Lemonade Server Spec](https://lemonade-server.ai/server/server_spec.html)
- [AMD Ryzen AI Article](https://www.amd.com/en/developer/resources/technical-articles/unlocking-a-wave-of-llm-apps-on-ryzen-ai-through-lemonade-server.html)
- [Strands Agents OpenAI Provider](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/openai/)
