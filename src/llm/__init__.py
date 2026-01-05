"""LLM helpers for local DS-STAR runtime."""

from src.llm.ollama_client import chat as ollama_chat
from src.llm.generic_client import chat as llm_chat

__all__ = ["ollama_chat", "llm_chat"]

