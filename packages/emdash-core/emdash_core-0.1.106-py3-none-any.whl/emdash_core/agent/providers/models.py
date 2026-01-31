"""Chat/LLM models enum - single source of truth for all supported models."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ChatModelSpec:
    """Specification for a chat/LLM model."""

    provider: str  # "anthropic", "openai", "fireworks"
    model_id: str  # The actual model identifier for the API
    api_model: str  # Model string to send to the API
    context_window: int  # Max context tokens
    max_output_tokens: int  # Max output tokens
    supports_tools: bool  # Whether model supports function calling
    supports_vision: bool  # Whether model supports image input
    supports_thinking: bool  # Whether model supports extended thinking
    description: str  # Human-readable description
    # Pricing per 1M tokens (USD)
    input_price: float = 0.0  # Cost per 1M input tokens
    output_price: float = 0.0  # Cost per 1M output tokens


class ChatModel(Enum):
    """
    All supported chat/LLM models.

    Format: PROVIDER_MODEL_NAME

    Usage:
        model = ChatModel.ANTHROPIC_CLAUDE_HAIKU_4
        print(model.spec.context_window)  # 200000
        print(model.spec.provider)        # "anthropic"
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # Anthropic Models
    # ═══════════════════════════════════════════════════════════════════════════

    ANTHROPIC_CLAUDE_OPUS_4 = ChatModelSpec(
        provider="anthropic",
        model_id="claude-opus-4-20250514",
        api_model="claude-opus-4-20250514",
        context_window=200000,
        max_output_tokens=32000,
        supports_tools=True,
        supports_vision=True,
        supports_thinking=True,
        description="Claude Opus 4 - Most capable, complex reasoning",
        input_price=15.0,
        output_price=75.0,
    )

    ANTHROPIC_CLAUDE_SONNET_4 = ChatModelSpec(
        provider="anthropic",
        model_id="claude-sonnet-4",
        api_model="claude-sonnet-4",
        context_window=200000,
        max_output_tokens=16000,
        supports_tools=True,
        supports_vision=True,
        supports_thinking=True,
        description="Claude Sonnet 4 - Balanced performance and cost",
        input_price=3.0,
        output_price=15.0,
    )

    ANTHROPIC_CLAUDE_HAIKU_4 = ChatModelSpec(
        provider="anthropic",
        model_id="claude-haiku-4-5",
        api_model="claude-haiku-4-5",
        context_window=200000,
        max_output_tokens=8192,
        supports_tools=True,
        supports_vision=True,
        supports_thinking=False,
        description="Claude Haiku 4.5 - Fast and efficient",
        input_price=0.80,
        output_price=4.0,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # OpenAI Models
    # ═══════════════════════════════════════════════════════════════════════════

    OPENAI_GPT_4O_MINI = ChatModelSpec(
        provider="openai",
        model_id="gpt-4o-mini",
        api_model="gpt-4o-mini",
        context_window=128000,
        max_output_tokens=16384,
        supports_tools=True,
        supports_vision=True,
        supports_thinking=False,
        description="GPT-4o Mini - Fast and cost-effective",
        input_price=0.15,
        output_price=0.60,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Fireworks AI Models
    # ═══════════════════════════════════════════════════════════════════════════

    FIREWORKS_GLM_4P7 = ChatModelSpec(
        provider="fireworks",
        model_id="accounts/fireworks/models/glm-4p7",
        api_model="accounts/fireworks/models/glm-4p7",
        context_window=128000,
        max_output_tokens=16384,
        supports_tools=True,
        supports_vision=False,
        supports_thinking=True,
        description="GLM-4P7 - Fireworks GLM model",
        input_price=0.60,
        output_price=2.20,
    )

    FIREWORKS_MINIMAX_M2P1 = ChatModelSpec(
        provider="fireworks",
        model_id="accounts/fireworks/models/minimax-m2p1",
        api_model="accounts/fireworks/models/minimax-m2p1",
        context_window=1000000,
        max_output_tokens=16384,
        supports_tools=True,
        supports_vision=False,  # Fireworks deployment doesn't expose vision
        supports_thinking=True,
        description="MiniMax M2P1 - Long context model",
        input_price=0.30,
        output_price=1.20,
    )

    FIREWORKS_KIMI_K2P5 = ChatModelSpec(
        provider="fireworks",
        model_id="accounts/fireworks/models/kimi-k2p5",
        api_model="accounts/fireworks/models/kimi-k2p5",
        context_window=128000,
        max_output_tokens=16384,
        supports_tools=True,
        supports_vision=True,
        supports_thinking=True,  # Returns reasoning_content in API response
        description="Kimi K2.5 - Moonshot multimodal model",
        input_price=0.60,
        output_price=2.40,
    )

    FIREWORKS_KIMI_K2_THINKING = ChatModelSpec(
        provider="fireworks",
        model_id="accounts/fireworks/models/kimi-k2-thinking",
        api_model="accounts/fireworks/models/kimi-k2-thinking",
        context_window=128000,
        max_output_tokens=96000,  # Thinking can output up to 96k reasoning tokens
        supports_tools=True,
        supports_vision=False,
        supports_thinking=True,
        description="Kimi K2 Thinking - Moonshot model with reasoning traces",
        input_price=0.60,
        output_price=2.40,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # OpenRouter Models
    # ═══════════════════════════════════════════════════════════════════════════


    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def spec(self) -> ChatModelSpec:
        """Get the model specification."""
        return self.value

    @property
    def provider(self) -> str:
        """Shortcut to get provider name."""
        return self.value.provider

    @property
    def model_id(self) -> str:
        """Shortcut to get the API model ID."""
        return self.value.model_id

    @property
    def api_model(self) -> str:
        """Shortcut to get the API model string."""
        return self.value.api_model

    @property
    def context_window(self) -> int:
        """Shortcut to get context window size."""
        return self.value.context_window

    @classmethod
    def get_default(cls) -> "ChatModel":
        """Get the default chat model."""
        return cls.FIREWORKS_GLM_4P7

    @classmethod
    def from_string(cls, value: str) -> Optional["ChatModel"]:
        """
        Parse model from string.

        Accepts:
            - Short aliases: "haiku", "sonnet" (checked first!)
            - Enum name: "ANTHROPIC_CLAUDE_HAIKU_4"
            - Provider:model: "anthropic:claude-haiku-4-5"
            - Just model_id: "claude-haiku-4-5"
        """
        value = value.strip()

        # Check short aliases FIRST (most common use case)
        aliases = {
            # Anthropic
            "haiku": cls.ANTHROPIC_CLAUDE_HAIKU_4,
            "sonnet": cls.ANTHROPIC_CLAUDE_SONNET_4,
            "opus": cls.ANTHROPIC_CLAUDE_OPUS_4,
            # OpenAI
            "gpt-4o-mini": cls.OPENAI_GPT_4O_MINI,
            # Fireworks
            "glm-4p7": cls.FIREWORKS_GLM_4P7,
            "minimax": cls.FIREWORKS_MINIMAX_M2P1,
            "kimi-k2p5": cls.FIREWORKS_KIMI_K2P5,
            "kimi": cls.FIREWORKS_KIMI_K2P5,
            "kimi-thinking": cls.FIREWORKS_KIMI_K2_THINKING,
            "kimi-k2-thinking": cls.FIREWORKS_KIMI_K2_THINKING,
        }
        if value.lower() in aliases:
            return aliases[value.lower()]

        # Try enum name
        try:
            return cls[value.upper().replace("-", "_").replace(":", "_")]
        except KeyError:
            pass

        # Try provider:model format
        if ":" in value:
            provider, model_id = value.split(":", 1)
            for model in cls:
                if model.provider == provider and model.model_id == model_id:
                    return model

        # Try exact model_id match
        for model in cls:
            if model.model_id == value:
                return model

        return None

    @classmethod
    def list_by_provider(cls, provider: str) -> list["ChatModel"]:
        """List all models for a specific provider."""
        return [m for m in cls if m.provider == provider]

    @classmethod
    def list_all(cls) -> list[dict]:
        """List all models with their specs for display."""
        return [
            {
                "name": m.name,
                "provider": m.provider,
                "model_id": m.model_id,
                "api_model": m.api_model,
                "context_window": m.context_window,
                "supports_tools": m.spec.supports_tools,
                "description": m.spec.description,
            }
            for m in cls
        ]

    def __str__(self) -> str:
        """String representation as provider:model_id."""
        return f"{self.provider}:{self.model_id}"


# ═══════════════════════════════════════════════════════════════════════════════
# Pricing Utilities
# ═══════════════════════════════════════════════════════════════════════════════

# Fallback pricing for models not in ChatModel enum (per 1M tokens)
FALLBACK_PRICING: dict[str, tuple[float, float]] = {
    # Format: "model_pattern": (input_price, output_price)
    # Anthropic
    "claude-opus": (15.0, 75.0),
    "claude-sonnet": (3.0, 15.0),
    "claude-haiku": (0.80, 4.0),
    # OpenAI
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.0),
    "gpt-4-turbo": (10.0, 30.0),
    # Fireworks (generic fallback)
    "fireworks": (0.50, 1.50),
    # Default fallback
    "default": (0.50, 1.50),
}


def get_model_pricing(model: str) -> tuple[float, float]:
    """Get pricing for a model (input_price, output_price per 1M tokens).

    Args:
        model: Model string (can be ChatModel, alias, or raw model ID)

    Returns:
        Tuple of (input_price, output_price) per 1M tokens
    """
    # Try to parse as ChatModel first
    parsed = ChatModel.from_string(model)
    if parsed:
        return (parsed.spec.input_price, parsed.spec.output_price)

    # Try fallback patterns
    model_lower = model.lower()
    for pattern, pricing in FALLBACK_PRICING.items():
        if pattern in model_lower:
            return pricing

    # Default fallback
    return FALLBACK_PRICING["default"]


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
    thinking_tokens: int = 0,
) -> float:
    """Calculate cost for token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model string
        thinking_tokens: Number of thinking tokens (charged as output)

    Returns:
        Total cost in USD
    """
    input_price, output_price = get_model_pricing(model)

    # Thinking tokens are typically charged at output rate
    total_output = output_tokens + thinking_tokens

    # Price is per 1M tokens
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (total_output / 1_000_000) * output_price

    return input_cost + output_cost
