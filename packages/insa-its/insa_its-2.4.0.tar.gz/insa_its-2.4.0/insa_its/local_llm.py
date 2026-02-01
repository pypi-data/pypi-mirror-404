"""
InsAIts SDK - Local LLM Integration
====================================
Ollama integration for local LLM-enhanced anomaly detection.

Supports user-configurable default model via:
- set_default_model("phi3")
- OLLAMA_MODEL env var
- Falls back to "llama3.2"
"""

import os
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Ollama URL can be configured via environment variable
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Default model: env var > fallback
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


def set_default_model(model: str) -> None:
    """
    Set the default Ollama model for all LLM operations.

    Args:
        model: Model name (e.g., "phi3", "llama3.2", "mistral")
    """
    global DEFAULT_MODEL
    DEFAULT_MODEL = model
    logger.info(f"Default Ollama model set to: {model}")


def get_default_model() -> str:
    """Get the current default Ollama model."""
    return DEFAULT_MODEL


def ollama_chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7
) -> Optional[str]:
    """
    Send a chat request to local Ollama instance.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Ollama model to use (None = use default model)
        temperature: Sampling temperature (0.0-1.0)

    Returns:
        Response text or None if Ollama unavailable
    """
    if model is None:
        model = DEFAULT_MODEL
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature}
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("message", {}).get("content", "")
        return None
    except requests.exceptions.RequestException:
        return None


def check_ollama_available() -> bool:
    """Check if Ollama is running locally."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def list_available_models() -> List[str]:
    """List available Ollama models."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        return []
    except requests.exceptions.RequestException:
        return []
