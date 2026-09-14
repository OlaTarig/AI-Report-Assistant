"""
Provider-agnostic AI interface.

The rest of the app talks to `AIProvider` only. Nothing outside this
`services/ai/` package should import a Gemini-specific (or any other
vendor) type. To add a new provider later (OpenRouter, Groq, etc.),
implement this interface and register it in `get_ai_provider()` —
no other code should need to change.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    role: MessageRole
    content: str


@dataclass
class FileContext:
    """Normalized, pre-extracted representation of an uploaded file,
    ready to be included in a prompt. Built by the file services —
    the AI layer never touches raw file bytes."""

    filename: str
    kind: str  # "pdf" | "docx" | "excel" | "image"
    text_summary: str
    image_bytes: bytes | None = None
    image_mime_type: str | None = None


@dataclass
class AIResponse:
    text: str
    raw_provider_response: object = field(default=None, repr=False)


class AIProvider(ABC):
    """Abstract interface every AI backend must implement."""

    @abstractmethod
    async def generate(
        self,
        messages: list[ChatMessage],
        files: list[FileContext] | None = None,
        system_prompt: str | None = None,
    ) -> AIResponse:
        raise NotImplementedError

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[ChatMessage],
        files: list[FileContext] | None = None,
        system_prompt: str | None = None,
    ):
        raise NotImplementedError
        yield  # pragma: no cover - makes this an async generator for type checkers

    @abstractmethod
    async def generate_structured(
        self,
        messages: list[ChatMessage],
        schema: type,
        files: list[FileContext] | None = None,
        system_prompt: str | None = None,
    ):
        """Same as generate(), but constrains the output to match `schema`
        (a Pydantic model class) and returns a validated instance of it."""
        raise NotImplementedError
