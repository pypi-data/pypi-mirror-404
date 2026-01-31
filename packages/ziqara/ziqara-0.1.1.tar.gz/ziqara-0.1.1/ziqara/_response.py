"""
Response models - OpenAI-compatible structures.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """Chat message in a completion response."""

    role: str
    content: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Message":
        if isinstance(d, Message):
            return d
        return cls(role=d.get("role", "assistant"), content=(d.get("content") or ""))


@dataclass
class Choice:
    """A single completion choice."""

    index: int
    message: Message
    finish_reason: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Choice":
        if isinstance(d, Choice):
            return d
        msg = d.get("message", {})
        return cls(
            index=d.get("index", 0),
            message=Message.from_dict(msg) if isinstance(msg, dict) else Message(role="assistant", content=""),
            finish_reason=d.get("finish_reason"),
        )


class ChatCompletionResponse:
    """OpenAI-compatible chat completion response."""

    def __init__(self, **kwargs: Any):
        self.id = kwargs.get("id", "")
        self.object = kwargs.get("object", "chat.completion")
        self.created = kwargs.get("created", 0)
        self.model = kwargs.get("model", "")
        raw_choices = kwargs.get("choices", [])
        self.choices = [
            c if isinstance(c, Choice) else Choice.from_dict(c)
            for c in raw_choices
        ]

    @property
    def content(self) -> str:
        """Convenience: first choice message content."""
        if not self.choices:
            return ""
        return self.choices[0].message.content
