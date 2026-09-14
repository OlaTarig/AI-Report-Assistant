from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai import get_ai_provider
from app.services.ai.base import AIProvider, ChatMessage, MessageRole
from app.services.ai.prompts import REPORT_SYSTEM_PROMPT

router = APIRouter(prefix="/chat", tags=["chat"])


def _to_chat_messages(request: ChatRequest) -> list[ChatMessage]:
    return [ChatMessage(role=MessageRole(turn.role), content=turn.content) for turn in request.messages]


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, provider: AIProvider = Depends(get_ai_provider)) -> ChatResponse:
    response = await provider.generate(messages=_to_chat_messages(request), system_prompt=REPORT_SYSTEM_PROMPT)
    return ChatResponse(reply=response.text)


@router.post("/stream")
async def chat_stream(request: ChatRequest, provider: AIProvider = Depends(get_ai_provider)):
    async def event_source():
        async for chunk in provider.generate_stream(
            messages=_to_chat_messages(request), system_prompt=REPORT_SYSTEM_PROMPT
        ):
            yield f"data: {chunk}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")
