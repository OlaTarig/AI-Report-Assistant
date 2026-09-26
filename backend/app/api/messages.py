import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.models import Conversation, Message, UploadedFile
from app.schemas.conversation import MessageCreate, MessageOut
from app.schemas.report import AssistantTurn
from app.services.ai import get_ai_provider
from app.services.ai.base import AIProvider, ChatMessage, FileContext, MessageRole
from app.services.ai.prompts import REPORT_SYSTEM_PROMPT
from app.services.files import file_service
from app.services.reports import report_service

router = APIRouter(prefix="/conversations/{conversation_id}/messages", tags=["messages"])
settings = get_settings()


async def _get_conversation_or_404(conversation_id: uuid.UUID, db: AsyncSession) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages), selectinload(Conversation.files))
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def _build_file_context(f: UploadedFile) -> FileContext:
    kind = file_service.get_file_kind(f.original_filename)
    text_summary = (f.extracted_content or {}).get("text_summary", "")

    image_bytes = None
    image_mime_type = None
    if kind == "image":
        full_path = Path(settings.upload_dir) / f.stored_filename
        image_bytes = full_path.read_bytes()
        image_mime_type = f.mime_type

    return FileContext(
        filename=f.original_filename,
        kind=kind,
        text_summary=text_summary,
        image_bytes=image_bytes,
        image_mime_type=image_mime_type,
    )


@router.post("", response_model=list[MessageOut])
async def send_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
) -> list[Message]:
    conversation = await _get_conversation_or_404(conversation_id, db)

    history = [
        ChatMessage(role=MessageRole(m.role), content=m.content) for m in conversation.messages
    ]
    history.append(ChatMessage(role=MessageRole.USER, content=payload.content))

    file_contexts = [_build_file_context(f) for f in conversation.files]

    report = await report_service.get_or_create_report(conversation_id, db)
    content = report_service.current_content(report)

    file_list = "\n".join(
        f"- id: {f.id}, filename: {f.original_filename}, type: {file_service.get_file_kind(f.original_filename)}"
        for f in conversation.files
    )

    dynamic_system_prompt = (
        f"{REPORT_SYSTEM_PROMPT}\n\n"
        f"## Current report state\n"
        f"{content.model_dump_json()}\n\n"
        f"When editing, reference section 'id' values from above. "
        f"For a brand-new section, invent a short lowercase-hyphenated id.\n\n"
        f"## Available uploaded files\n"
        f"{file_list or '(none uploaded yet)'}"
    )

    try:
        turn = await provider.generate_structured(
            messages=history,
            schema=AssistantTurn,
            files=file_contexts,
            system_prompt=dynamic_system_prompt,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}") from exc

    user_message = Message(conversation_id=conversation.id, role="user", content=payload.content)
    assistant_message = Message(conversation_id=conversation.id, role="assistant", content=turn.reply)
    db.add(user_message)
    db.add(assistant_message)
    conversation.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user_message)
    await db.refresh(assistant_message)

    has_changes = turn.patch.updated_sections or turn.patch.removed_section_ids or (
        turn.patch.title != content.title
    )
    if has_changes:
        await report_service.apply_patch(report, turn.patch, db)
        # Auto-name the conversation from the report's title the first time
        # it gets a real one — mirrors how chat apps auto-title new threads.
        if conversation.title == "New Report" and turn.patch.title and turn.patch.title != "New Report":
            conversation.title = turn.patch.title[:255]
            await db.commit()

    return [user_message, assistant_message]
