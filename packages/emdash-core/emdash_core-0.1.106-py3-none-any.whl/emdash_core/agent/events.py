"""Unified event stream for agent operations.

This module provides a centralized event system that both CLI and UI can consume,
ensuring consistent message handling across interfaces.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


class EventType(Enum):
    """Types of events emitted by agents."""

    # Tool lifecycle
    TOOL_START = "tool_start"
    TOOL_RESULT = "tool_result"

    # Sub-agent lifecycle
    SUBAGENT_START = "subagent_start"
    SUBAGENT_END = "subagent_end"

    # Agent thinking/progress
    THINKING = "thinking"
    PROGRESS = "progress"

    # Output
    RESPONSE = "response"
    PARTIAL_RESPONSE = "partial_response"
    ASSISTANT_TEXT = "assistant_text"  # Intermediate text between tool calls

    # Interaction
    CLARIFICATION = "clarification"
    CLARIFICATION_RESPONSE = "clarification_response"
    CHOICE_QUESTIONS = "choice_questions"
    CHOICE_RESPONSES = "choice_responses"
    PLAN_MODE_REQUESTED = "plan_mode_requested"
    PLAN_SUBMITTED = "plan_submitted"

    # Errors
    ERROR = "error"
    WARNING = "warning"

    # Session
    SESSION_START = "session_start"
    SESSION_END = "session_end"

    # Context
    CONTEXT_FRAME = "context_frame"

    # LLM iteration tracking
    LLM_STEP = "llm_step"  # Per-iteration LLM usage data


@dataclass
class AgentEvent:
    """A single event emitted by an agent.

    Attributes:
        type: The type of event
        data: Event-specific data payload
        timestamp: When the event occurred
        agent_name: Optional name of the agent that emitted this event
    """
    type: EventType
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    agent_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "agent_name": self.agent_name,
        }


class EventHandler(Protocol):
    """Protocol for event handlers."""

    def handle(self, event: AgentEvent) -> None:
        """Handle an emitted event."""
        ...


class AgentEventEmitter:
    """Emits and stores agent events for consumption by handlers.

    This is the central hub for the event stream. Agents emit events here,
    and handlers (CLI Rich renderer, JSON streamer, etc.) subscribe to receive them.

    Example:
        emitter = AgentEventEmitter()
        emitter.add_handler(RichConsoleHandler())

        # In agent code:
        emitter.emit(EventType.TOOL_START, {"name": "semantic_search", "args": {...}})
        result = execute_tool(...)
        emitter.emit(EventType.TOOL_RESULT, {"name": "semantic_search", "success": True})
    """

    def __init__(self, agent_name: str | None = None):
        """Initialize the emitter.

        Args:
            agent_name: Optional name to tag all events from this emitter
        """
        self._handlers: list[EventHandler] = []
        self._events: list[AgentEvent] = []
        self._agent_name = agent_name

    def add_handler(self, handler: EventHandler) -> None:
        """Add a handler to receive events.

        Args:
            handler: Handler that implements the EventHandler protocol
        """
        self._handlers.append(handler)

    def remove_handler(self, handler: EventHandler) -> None:
        """Remove a handler.

        Args:
            handler: Handler to remove
        """
        if handler in self._handlers:
            self._handlers.remove(handler)

    def is_cancelled(self) -> bool:
        """Check if any handler has signaled cancellation.

        Returns:
            True if any handler has a 'cancelled' property set to True.
            This is used to stop agent execution when client disconnects.
        """
        for handler in self._handlers:
            if hasattr(handler, 'cancelled') and handler.cancelled:
                return True
        return False

    def emit(self, event_type: EventType, data: dict[str, Any] | None = None) -> AgentEvent:
        """Emit an event to all handlers.

        Args:
            event_type: Type of event to emit
            data: Event-specific data payload

        Returns:
            The created AgentEvent
        """
        event = AgentEvent(
            type=event_type,
            data=data or {},
            agent_name=self._agent_name,
        )
        self._events.append(event)

        for handler in self._handlers:
            try:
                handler.handle(event)
            except Exception:
                # Don't let handler errors break the agent
                pass

        return event

    def emit_tool_start(
        self,
        name: str,
        args: dict[str, Any] | None = None,
        tool_id: str | None = None,
    ) -> AgentEvent:
        """Convenience method to emit a tool start event.

        Args:
            name: Tool name
            args: Tool arguments
            tool_id: Unique ID for this tool call (for matching with result)
        """
        return self.emit(EventType.TOOL_START, {
            "name": name,
            "tool_name": name,  # Alias for dashboard compatibility
            "args": args or {},
            "tool_input": args or {},  # Alias for dashboard compatibility
            "tool_id": tool_id,
        })

    def emit_tool_result(
        self,
        name: str,
        success: bool,
        summary: str | None = None,
        data: dict[str, Any] | None = None,
        tool_id: str | None = None,
        error: str | None = None,
    ) -> AgentEvent:
        """Convenience method to emit a tool result event.

        Args:
            name: Tool name
            success: Whether the tool succeeded
            summary: Brief summary of the result
            data: Full result data (may be truncated by handlers)
            tool_id: Unique ID for this tool call (for matching with start)
            error: Error message if tool failed
        """
        return self.emit(EventType.TOOL_RESULT, {
            "name": name,
            "tool_name": name,  # Alias for dashboard compatibility
            "success": success,
            "summary": summary,
            "data": data,
            "result": data,  # Alias for dashboard compatibility
            "tool_id": tool_id,
            "error": error if not success else None,
        })

    def emit_thinking(
        self,
        message: str,
        raw_response: dict[str, Any] | None = None,
    ) -> AgentEvent:
        """Convenience method to emit a thinking/progress message.

        Args:
            message: What the agent is thinking/doing
            raw_response: Optional LLM response metadata (tokens, stop_reason)
        """
        data = {"message": message}
        if raw_response is not None:
            data["raw_response"] = raw_response
        return self.emit(EventType.THINKING, data)

    def emit_progress(self, message: str, percent: float | None = None) -> AgentEvent:
        """Convenience method to emit a progress update.

        Args:
            message: Progress message
            percent: Optional completion percentage (0-100)
        """
        return self.emit(EventType.PROGRESS, {
            "message": message,
            "percent": percent,
        })

    def emit_response(self, content: str, is_final: bool = True) -> AgentEvent:
        """Convenience method to emit a response.

        Args:
            content: Response content (usually markdown)
            is_final: Whether this is the final response
        """
        event_type = EventType.RESPONSE if is_final else EventType.PARTIAL_RESPONSE
        return self.emit(event_type, {"content": content})

    def emit_assistant_text(self, content: str) -> AgentEvent:
        """Emit intermediate assistant text (shown between tool calls).

        Args:
            content: Text content from assistant (e.g., "Let me read the file...")
        """
        return self.emit(EventType.ASSISTANT_TEXT, {"content": content})

    def emit_clarification(
        self,
        question: str,
        context: str | None = None,
        options: list[str] | None = None,
    ) -> AgentEvent:
        """Convenience method to emit a clarification request.

        Args:
            question: The question to ask
            context: Why we're asking
            options: Suggested answers
        """
        return self.emit(EventType.CLARIFICATION, {
            "question": question,
            "context": context,
            "options": options,
        })

    def emit_choice_questions(
        self,
        choices: list[dict],
        context: str = "approach",
    ) -> AgentEvent:
        """Convenience method to emit choice questions.

        This is emitted when the agent calls ask_choice_questions tool,
        presenting selection-based choices to the user.

        Args:
            choices: List of choice questions, each with question and options
            context: Type of choice (approach, scope, requirement)
        """
        return self.emit(EventType.CHOICE_QUESTIONS, {
            "choices": choices,
            "context": context,
        })

    def emit_plan_mode_requested(
        self,
        reason: str,
    ) -> AgentEvent:
        """Convenience method to emit a plan mode request event.

        This is emitted when the agent calls enter_plan_mode tool,
        requesting user consent to enter plan mode.

        Args:
            reason: Why the agent wants to enter plan mode
        """
        return self.emit(EventType.PLAN_MODE_REQUESTED, {
            "reason": reason,
        })

    def emit_plan_submitted(self, plan: str) -> AgentEvent:
        """Convenience method to emit a plan submission event.

        Args:
            plan: The implementation plan as markdown
        """
        return self.emit(EventType.PLAN_SUBMITTED, {
            "plan": plan,
        })

    def emit_error(self, message: str, details: str | None = None) -> AgentEvent:
        """Convenience method to emit an error.

        Args:
            message: Error message
            details: Additional details (stack trace, etc.)
        """
        return self.emit(EventType.ERROR, {
            "message": message,
            "details": details,
        })

    def emit_start(
        self,
        goal: str,
        system_prompt: str | None = None,
        **kwargs,
    ) -> AgentEvent:
        """Convenience method to emit a session start event.

        Args:
            goal: The goal/query for this session
            system_prompt: The system prompt used for this session
            **kwargs: Additional data to include
        """
        data = {"goal": goal, **kwargs}
        if system_prompt is not None:
            data["system_prompt"] = system_prompt
        return self.emit(EventType.SESSION_START, data)

    def emit_end(
        self,
        success: bool = True,
        raw_response: dict[str, Any] | None = None,
        **kwargs,
    ) -> AgentEvent:
        """Convenience method to emit a session end event.

        Args:
            success: Whether the session completed successfully
            raw_response: Optional cumulative usage data (tokens)
            **kwargs: Additional data to include
        """
        data = {"success": success, **kwargs}
        if raw_response is not None:
            data["raw_response"] = raw_response
        return self.emit(EventType.SESSION_END, data)

    def emit_context_frame(
        self,
        adding: dict[str, Any] | None = None,
        reading: dict[str, Any] | None = None,
    ) -> AgentEvent:
        """Convenience method to emit a context frame update.

        Args:
            adding: What's being added to context (modified_files, exploration_steps, tokens)
            reading: What's being read from context (items with scores, tokens)
        """
        return self.emit(EventType.CONTEXT_FRAME, {
            "adding": adding or {},
            "reading": reading or {},
        })

    def emit_message_start(self) -> AgentEvent:
        """Convenience method to emit message start event."""
        self._accumulated_content = ""
        return self.emit(EventType.PARTIAL_RESPONSE, {"status": "start"})

    def emit_message_delta(self, content: str) -> AgentEvent:
        """Convenience method to emit message delta (streaming content).

        Args:
            content: The content chunk to stream
        """
        if hasattr(self, '_accumulated_content'):
            self._accumulated_content += content
        return self.emit(EventType.PARTIAL_RESPONSE, {"content": content})

    def emit_message_end(
        self,
        raw_response: dict[str, Any] | None = None,
    ) -> AgentEvent:
        """Convenience method to emit message end event with accumulated content.

        Args:
            raw_response: Optional LLM response metadata (tokens, stop_reason)
        """
        content = getattr(self, '_accumulated_content', "")
        data = {"content": content}
        if raw_response is not None:
            data["raw_response"] = raw_response
        return self.emit(EventType.RESPONSE, data)

    def emit_llm_step(
        self,
        iteration: int,
        input_tokens: int,
        output_tokens: int,
        thinking_tokens: int = 0,
        cost: float | None = None,
        response_text: str | None = None,
        has_tool_calls: bool = False,
        tool_call_names: list[str] | None = None,
        cache_creation_input_tokens: int | None = None,
        cache_read_input_tokens: int | None = None,
        duration_ms: int | None = None,
        model: str | None = None,
    ) -> AgentEvent:
        """Emit per-iteration LLM usage data.

        This fires after each LLM response, before tool calls are processed.
        Used by dashboards to track per-step token usage and correlate with tool calls.

        Args:
            iteration: Current iteration number
            input_tokens: Tokens in the request
            output_tokens: Tokens in the response
            thinking_tokens: Tokens used for thinking (if available)
            cost: Cost in USD for this call
            response_text: Text content of the response (if any)
            has_tool_calls: Whether the response includes tool calls
            tool_call_names: Names of tools being called (if any)
            cache_creation_input_tokens: Tokens used to create cache (Anthropic)
            cache_read_input_tokens: Tokens read from cache (Anthropic)
            duration_ms: Duration of the LLM call in milliseconds
            model: Model name used for this call
        """
        return self.emit(EventType.LLM_STEP, {
            "iteration": iteration,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "thinking_tokens": thinking_tokens,
            "cost": cost,
            "response_text": response_text,
            "has_tool_calls": has_tool_calls,
            "tool_call_names": tool_call_names or [],
            "cache_creation_input_tokens": cache_creation_input_tokens,
            "cache_read_input_tokens": cache_read_input_tokens,
            "duration_ms": duration_ms,
            "model": model,
        })

    def get_events(self) -> list[AgentEvent]:
        """Get all events emitted so far.

        Returns:
            Copy of the events list
        """
        return self._events.copy()

    def clear_events(self) -> None:
        """Clear the events history."""
        self._events.clear()


# Default no-op emitter for backwards compatibility
class NullEmitter(AgentEventEmitter):
    """An emitter that does nothing - for backwards compatibility."""

    def emit(self, event_type: EventType, data: dict[str, Any] | None = None) -> AgentEvent:
        """Create event but don't store or dispatch it."""
        return AgentEvent(type=event_type, data=data or {}, agent_name=self._agent_name)


# Global default emitter (can be replaced)
_default_emitter: AgentEventEmitter | None = None


def get_default_emitter() -> AgentEventEmitter:
    """Get the default global emitter."""
    global _default_emitter
    if _default_emitter is None:
        _default_emitter = NullEmitter()
    return _default_emitter


def set_default_emitter(emitter: AgentEventEmitter) -> None:
    """Set the default global emitter."""
    global _default_emitter
    _default_emitter = emitter
