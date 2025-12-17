"""Minimal Ollama client (local) for DS-STAR.

We use Ollama's `/api/chat` endpoint directly to ensure the app can run fully locally
without requiring additional model-provider SDKs.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


def chat(
    *,
    host: str,
    model: str,
    prompt: str,
    num_predict: int = 1024,
    temperature: float = 0.2,
    timeout_s: int = 180,
) -> Tuple[Optional[str], int, Dict[str, Any]]:
    """Call Ollama `/api/chat` and return (content, latency_ms, raw_json).

    Notes:
    - Some reasoning-capable models may include internal "thinking" fields; we return only `message.content`.
    - If content is empty, callers should treat that as a failure and adjust prompt/options.
    """
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
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # nosec - local trusted endpoint
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

