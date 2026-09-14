from collections.abc import AsyncIterator

from google import genai
from google.genai import types as genai_types

from app.services.ai.base import AIProvider, AIResponse, ChatMessage, FileContext, MessageRole
from app.services.ai.schema_utils import pydantic_to_gemini_schema

_ROLE_MAP = {
    MessageRole.USER: "user",
    MessageRole.ASSISTANT: "model",
}


def _build_contents(messages: list[ChatMessage], files: list[FileContext] | None) -> list[dict]:
    contents: list[dict] = []

    for msg in messages:
        if msg.role == MessageRole.SYSTEM:
            continue
        contents.append({"role": _ROLE_MAP[msg.role], "parts": [{"text": msg.content}]})

    if files:
        file_parts = []
        for f in files:
            if f.image_bytes and f.image_mime_type:
                file_parts.append(
                    {"inline_data": {"mime_type": f.image_mime_type, "data": f.image_bytes}}
                )
            file_parts.append({"text": f"[Attached file: {f.filename}]\n{f.text_summary}"})

        if contents and contents[-1]["role"] == "user":
            contents[-1]["parts"] = file_parts + contents[-1]["parts"]
        else:
            contents.append({"role": "user", "parts": file_parts})

    return contents


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.1-flash-lite"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate(
        self,
        messages: list[ChatMessage],
        files: list[FileContext] | None = None,
        system_prompt: str | None = None,
    ) -> AIResponse:
        contents = _build_contents(messages, files)
        config = genai_types.GenerateContentConfig(system_instruction=system_prompt)

        response = await self._client.aio.models.generate_content(
            model=self._model, contents=contents, config=config
        )
        return AIResponse(text=response.text or "", raw_provider_response=response)

    async def generate_stream(
        self,
        messages: list[ChatMessage],
        files: list[FileContext] | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        contents = _build_contents(messages, files)
        config = genai_types.GenerateContentConfig(system_instruction=system_prompt)

        stream = await self._client.aio.models.generate_content_stream(
            model=self._model, contents=contents, config=config
        )
        async for chunk in stream:
            if chunk.text:
                yield chunk.text

    async def generate_structured(
        self,
        messages: list[ChatMessage],
        schema: type,
        files: list[FileContext] | None = None,
        system_prompt: str | None = None,
    ):
        contents = _build_contents(messages, files)
        config = genai_types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=pydantic_to_gemini_schema(schema),
        )
        response = await self._client.aio.models.generate_content(
            model=self._model, contents=contents, config=config
        )
        return schema.model_validate_json(response.text)
