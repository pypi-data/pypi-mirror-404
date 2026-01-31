"""Pydantic models for agent API."""

import os
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def _default_use_worktree() -> bool:
    """Get default worktree setting from environment."""
    return os.environ.get("EMDASH_USE_WORKTREE", "false").lower() in ("true", "1", "yes")


class AgentMode(str, Enum):
    """Agent operation modes."""

    CODE = "code"
    RESEARCH = "research"
    REVIEW = "review"
    SPEC = "spec"
    PLAN = "plan"


class ImageData(BaseModel):
    """Image data for vision-capable models."""

    data: str = Field(..., description="Base64 encoded image data")
    format: str = Field(default="png", description="Image format (png, jpg, etc.)")


class AgentType(str, Enum):
    """Agent types available."""

    CODING = "coding"
    COWORKER = "coworker"


class AgentChatOptions(BaseModel):
    """Options for agent chat."""

    max_iterations: int = Field(default=100, description="Maximum agent iterations")
    verbose: bool = Field(default=True, description="Enable verbose output")
    mode: AgentMode = Field(default=AgentMode.CODE, description="Agent mode")
    context_threshold: float = Field(
        default=0.6,
        description="Context window threshold for summarization (0-1)"
    )
    use_worktree: bool = Field(
        default_factory=_default_use_worktree,
        description="Use git worktree for isolated changes (EMDASH_USE_WORKTREE env)"
    )
    # Agent type selection
    agent_type: AgentType = Field(
        default=AgentType.CODING,
        description="Type of agent to use (coding or coworker)"
    )
    # Coworker-specific options
    personality: Optional[str] = Field(
        default=None,
        description="Coworker personality (helpful_professional, creative_collaborator, etc.)"
    )
    domain_context: Optional[str] = Field(
        default=None,
        description="Domain context for coworker agent (e.g., 'marketing team')"
    )


class AgentChatRequest(BaseModel):
    """Request for agent chat endpoint."""

    message: str = Field(..., description="User message/task")
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity"
    )
    model: Optional[str] = Field(
        default=None,
        description="Model to use (defaults to server config)"
    )
    images: list[ImageData] = Field(
        default_factory=list,
        description="Images for vision-capable models"
    )
    history: list[dict] = Field(
        default_factory=list,
        description="Pre-loaded conversation history from saved session"
    )
    options: AgentChatOptions = Field(
        default_factory=AgentChatOptions,
        description="Agent options"
    )


class SessionInfo(BaseModel):
    """Information about an agent session."""

    session_id: str
    agent_name: str
    model: str
    created_at: str
    message_count: int
    is_active: bool
