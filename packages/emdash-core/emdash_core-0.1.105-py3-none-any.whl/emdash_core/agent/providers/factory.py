"""Factory for creating LLM providers."""

import os
from typing import Union

from .base import LLMProvider
from .models import ChatModel
from .openai_provider import OpenAIProvider


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration - Single source of truth
# ═══════════════════════════════════════════════════════════════════════════════

# Default model alias - check EMDASH_MODEL first, then legacy EMDASH_DEFAULT_MODEL
DEFAULT_MODEL = os.environ.get(
    "EMDASH_MODEL",
    os.environ.get("EMDASH_DEFAULT_MODEL", "fireworks:accounts/fireworks/models/minimax-m2p1")
)

# Vision model - used when images are present and primary model doesn't support vision
# Defaults to Fireworks Qwen3-VL which has good vision capabilities
VISION_MODEL = os.environ.get("EMDASH_VISION_MODEL", "fireworks:accounts/fireworks/models/qwen3-vl-235b-a22b-thinking")

# Default API key environment variable (used by default model)
DEFAULT_API_KEY_ENV = "FIREWORKS_API_KEY"


# ═══════════════════════════════════════════════════════════════════════════════
# Factory functions
# ═══════════════════════════════════════════════════════════════════════════════


def get_provider(model: Union[str, ChatModel] = DEFAULT_MODEL) -> LLMProvider:
    """
    Get an LLM provider for the specified model.

    Uses OpenAI SDK with provider-specific base URLs for OpenAI, Anthropic, and Fireworks.
    For local models, uses HuggingFace Transformers.

    Args:
        model: Model specification - ChatModel enum or alias
            Examples:
                - ChatModel.ANTHROPIC_CLAUDE_HAIKU_4
                - "haiku", "sonnet", "opus"
                - "gpt-4o-mini"
                - "minimax"

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If model string not recognized
    """
    # Handle ChatModel enum directly
    if isinstance(model, ChatModel):
        return OpenAIProvider(model)

    # Try to parse as ChatModel
    parsed = ChatModel.from_string(model)
    if parsed:
        return OpenAIProvider(parsed)

    # Assume it's a raw model string
    return OpenAIProvider(model)


def get_default_model() -> ChatModel:
    """Get the default model."""
    return ChatModel.from_string(DEFAULT_MODEL) or ChatModel.get_default()


def get_default_api_key() -> str | None:
    """Get the default API key from environment."""
    return os.environ.get(DEFAULT_API_KEY_ENV)


def list_available_models() -> list[dict]:
    """List all available models."""
    return ChatModel.list_all()


def get_vision_provider() -> LLMProvider:
    """Get a vision-capable LLM provider.

    Uses EMDASH_VISION_MODEL env var, defaults to gpt-4o-mini.

    Returns:
        LLMProvider instance that supports vision
    """
    return get_provider(VISION_MODEL)


def get_vision_model() -> str:
    """Get the configured vision model name.

    Returns:
        Vision model string from EMDASH_VISION_MODEL or default
    """
    return VISION_MODEL
