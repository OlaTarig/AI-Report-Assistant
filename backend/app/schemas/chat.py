from pydantic import BaseModel


class ChatTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatTurn]


class ChatResponse(BaseModel):
    reply: str
