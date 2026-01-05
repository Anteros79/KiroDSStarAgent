"""Generic LLM client for DS-STAR supporting multiple providers.

Supports: Lemonade, OpenAI, Anthropic, Ollama, Bedrock
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


def chat(
    *,
    provider: str,
    model: str,
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.2,
    timeout_s: int = 180,
    # Provider-specific options
    ollama_host: str = "http://127.0.0.1:11434",
    lemonade_base_url: str = "http://localhost:8000/api/v1",
    openai_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
) -> Tuple[Optional[str], int, Dict[str, Any]]:
    """Call LLM and return (content, latency_ms, raw_response).
    
    Supports multiple providers with a unified interface.
    """
    provider = provider.lower()
    
    if provider == "ollama":
        return _ollama_chat(
            host=ollama_host,
            model=model,
            prompt=prompt,
            num_predict=max_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
        )
    elif provider == "lemonade":
        return _openai_compatible_chat(
            base_url=lemonade_base_url,
            api_key="not-needed",
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
        )
    elif provider == "openai":
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY", "")
        return _openai_compatible_chat(
            base_url="https://api.openai.com/v1",
            api_key=api_key,
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
        )
    elif provider == "anthropic":
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
        return _anthropic_chat(
            api_key=api_key,
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
        )
    elif provider == "bedrock":
        # For Bedrock, we'd need boto3 - for now return a helpful message
        return None, 0, {"error": "Bedrock provider requires boto3 SDK. Use main agent flow instead."}
    else:
        return None, 0, {"error": f"Unknown provider: {provider}"}


def _ollama_chat(
    *,
    host: str,
    model: str,
    prompt: str,
    num_predict: int = 1024,
    temperature: float = 0.2,
    timeout_s: int = 180,
) -> Tuple[Optional[str], int, Dict[str, Any]]:
    """Call Ollama /api/chat endpoint."""
    url = host.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8")
        raw: Dict[str, Any] = json.loads(body)
        msg = raw.get("message") if isinstance(raw, dict) else None
        content = msg.get("content") if isinstance(msg, dict) else None
        latency_ms = int((time.perf_counter() - start) * 1000)
        if isinstance(content, str) and content.strip():
            return content.strip(), latency_ms, raw
        return None, latency_ms, raw
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return None, latency_ms, {"error": str(e)}


def _openai_compatible_chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.2,
    timeout_s: int = 180,
) -> Tuple[Optional[str], int, Dict[str, Any]]:
    """Call OpenAI-compatible /chat/completions endpoint (works for OpenAI and Lemonade)."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Handle base_url that may or may not include /chat/completions
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        url = base
    elif base.endswith("/v1"):
        url = base + "/chat/completions"
    else:
        url = base + "/v1/chat/completions"
    
    logger.info(f"LLM request to: {url}")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
    }
    # Only add Authorization header if api_key is provided and not a placeholder
    if api_key and api_key != "not-needed":
        headers["Authorization"] = f"Bearer {api_key}"
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8")
        raw: Dict[str, Any] = json.loads(body)
        choices = raw.get("choices", [])
        if choices and isinstance(choices, list):
            msg = choices[0].get("message", {})
            content = msg.get("content")
            latency_ms = int((time.perf_counter() - start) * 1000)
            if isinstance(content, str) and content.strip():
                return content.strip(), latency_ms, raw
        latency_ms = int((time.perf_counter() - start) * 1000)
        return None, latency_ms, raw
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.error(f"LLM request failed: {e}, URL: {url}")
        return None, latency_ms, {"error": str(e), "url": url}


def _anthropic_chat(
    *,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.2,
    timeout_s: int = 180,
) -> Tuple[Optional[str], int, Dict[str, Any]]:
    """Call Anthropic Messages API."""
    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8")
        raw: Dict[str, Any] = json.loads(body)
        content_blocks = raw.get("content", [])
        if content_blocks and isinstance(content_blocks, list):
            text_block = content_blocks[0]
            if isinstance(text_block, dict) and text_block.get("type") == "text":
                content = text_block.get("text")
                latency_ms = int((time.perf_counter() - start) * 1000)
                if isinstance(content, str) and content.strip():
                    return content.strip(), latency_ms, raw
        latency_ms = int((time.perf_counter() - start) * 1000)
        return None, latency_ms, raw
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return None, latency_ms, {"error": str(e)}
