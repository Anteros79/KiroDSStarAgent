# DS-STAR Model Provider Quick Reference

**Last Updated:** January 4, 2026

## Supported Providers

DS-STAR supports five model providers. **Lemonade is the default.**

| Provider | Type | Cost | Privacy | Setup Difficulty |
|----------|------|------|---------|------------------|
| **Lemonade** ⭐ | Local | Free | 100% Private | Easy |
| Anthropic | Cloud API | Paid | Cloud | Easy |
| OpenAI | Cloud API | Paid | Cloud | Easy |
| Ollama | Local | Free | 100% Private | Easy |
| AWS Bedrock | Cloud API | Paid | Cloud | Medium |

## Quick Setup

### 1. Lemonade (Default) 🍋

**Best for:** Local execution on AMD Ryzen AI hardware

```bash
# .env file (or use defaults)
DS_STAR_MODEL_PROVIDER=lemonade
DS_STAR_MODEL_ID=Qwen3-Next-80B-A3B-Instruct-GGUF
DS_STAR_LEMONADE_BASE_URL=http://localhost:8000/api/v1
```

**Prerequisites:**
- Install Lemonade Server from https://lemonade-server.ai/
- Load a model in Lemonade Server
- Start the server

**Run:**
```bash
python src/main.py
```

---

### 2. Anthropic

**Best for:** High-quality cloud-based reasoning

```bash
# .env file
DS_STAR_MODEL_PROVIDER=anthropic
DS_STAR_MODEL_ID=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=your_api_key_here
```

**Prerequisites:**
- Get API key from https://console.anthropic.com/

**Run:**
```bash
python src/main.py
```

---

### 3. OpenAI

**Best for:** GPT-4 quality with broad compatibility

```bash
# .env file
DS_STAR_MODEL_PROVIDER=openai
DS_STAR_MODEL_ID=gpt-4o
OPENAI_API_KEY=your_api_key_here
```

**Prerequisites:**
- Get API key from https://platform.openai.com/

**Run:**
```bash
python src/main.py
```

---

### 4. Ollama

**Best for:** Local execution on any hardware

```bash
# .env file
DS_STAR_MODEL_PROVIDER=ollama
DS_STAR_MODEL_ID=qwen3:30b
DS_STAR_OLLAMA_HOST=http://localhost:11434
```

**Prerequisites:**
```bash
# Install Ollama
# Download from https://ollama.ai/

# Pull the model
ollama pull qwen3:30b

# Start Ollama (usually runs automatically)
ollama serve
```

**Run:**
```bash
python src/main.py
```

---

### 5. AWS Bedrock

**Best for:** Enterprise AWS deployments

```bash
# .env file
DS_STAR_MODEL_PROVIDER=bedrock
DS_STAR_MODEL_ID=us.amazon.nova-lite-v1:0
AWS_REGION=us-west-2
```

**Prerequisites:**
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-west-2
```

**Run:**
```bash
python src/main.py
```

---

## Switching Providers

### Method 1: Environment Variables

```bash
# Switch to Ollama
export DS_STAR_MODEL_PROVIDER=ollama
python src/main.py

# Switch to Lemonade
export DS_STAR_MODEL_PROVIDER=lemonade
python src/main.py
```

### Method 2: .env File

Edit `.env` and change `DS_STAR_MODEL_PROVIDER`:

```bash
DS_STAR_MODEL_PROVIDER=lemonade  # or anthropic, ollama, bedrock
```

### Method 3: Command Line

```bash
DS_STAR_MODEL_PROVIDER=ollama python src/main.py
```

---

## Common Configuration

These settings work with all providers:

```bash
# Performance
DS_STAR_MAX_TOKENS=4096
DS_STAR_TEMPERATURE=0.3

# Debugging
DS_STAR_VERBOSE=true

# Data
DS_STAR_DATA_PATH=./data/airline_operations.csv
DS_STAR_OUTPUT_DIR=./output
```

---

## Troubleshooting

### Lemonade Issues

```bash
# Check if server is running
curl http://localhost:8000/api/v1/models

# Check logs
# Look in Lemonade Server UI
```

### Ollama Issues

```bash
# Check if Ollama is running
ollama list

# Check if model is available
ollama pull qwen3:30b

# Test connection
curl http://localhost:11434/api/tags
```

### Anthropic Issues

```bash
# Verify API key
echo $ANTHROPIC_API_KEY

# Test API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

### OpenAI Issues

```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test API key (PowerShell)
curl https://api.openai.com/v1/models -H "Authorization: Bearer $env:OPENAI_API_KEY"

# Common issues:
# - "Invalid API key": Check key at https://platform.openai.com/api-keys
# - "Rate limit exceeded": Wait or upgrade plan
# - "Model not found": Verify model ID (gpt-4o, gpt-4-turbo, etc.)
```

### Bedrock Issues

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region us-west-2
```

---

## Performance Comparison

| Provider | Speed | Quality | Cost | Privacy |
|----------|-------|---------|------|---------|
| Lemonade | Fast (local) | Good | Free | ⭐⭐⭐⭐⭐ |
| Anthropic | Fast (cloud) | Excellent | $$$ | ⭐⭐ |
| Ollama | Medium (local) | Good | Free | ⭐⭐⭐⭐⭐ |
| OpenAI | Fast (cloud) | Excellent | $$ | ⭐⭐ |
| Bedrock | Fast (cloud) | Excellent | $ | ⭐⭐⭐ |

---

## Recommended Models

### Lemonade
- `Qwen3-Next-80B-A3B-Instruct-GGUF` (default, best quality)
- Check Lemonade Server for available models

### Anthropic
- `claude-3-5-sonnet-20241022` (default, best balance)
- `claude-3-opus-20240229` (highest quality)
- `claude-3-haiku-20240307` (fastest, cheapest)

### OpenAI
- `gpt-4o` (default, best balance of quality and speed)
- `gpt-4-turbo` (high quality, larger context)
- `gpt-4o-mini` (fastest, most cost-effective)

### Ollama
- `qwen3:30b` (default, good balance)
- `llama3.1:70b` (high quality)
- `mistral:7b` (fast, lightweight)

### Bedrock
- `us.amazon.nova-lite-v1:0` (default, cost-effective)
- `us.anthropic.claude-sonnet-4-20250514-v1:0` (highest quality)
- `us.anthropic.claude-3-5-haiku-20241022-v1:0` (fast)

---

## Need Help?

1. Check `LEMONADE_INTEGRATION.md` for detailed Lemonade setup
2. Check `README.md` for general DS-STAR documentation
3. Run with `DS_STAR_VERBOSE=true` for detailed logs
4. Check provider-specific documentation linked above
