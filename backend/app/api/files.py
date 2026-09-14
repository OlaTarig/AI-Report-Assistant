import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import Conversation, UploadedFile
from app.schemas.file import UploadedFileOut
from app.services.files import file_service, storage

router = APIRouter(prefix="/conversations/{conversation_id}/files", tags=["files"])
settings = get_settings()


async def _get_conversation_or_404(conversation_id: uuid.UUID, db: AsyncSession) -> Conversation:
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("", response_model=UploadedFileOut)
async def upload_file(
    conversation_id: uuid.UUID, file: UploadFile, db: AsyncSession = Depends(get_db)
) -> UploadedFile:
    await _get_conversation_or_404(conversation_id, db)

    file_service.get_file_kind(file.filename)  # raises 400 early if unsupported

    content = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"File exceeds the {settings.max_file_size_mb}MB limit"
        )

    stored_filename, full_path = await storage.save_upload(file.filename, content)
    extracted = file_service.process_file(full_path, file.filename)

    uploaded_file = UploadedFile(
        conversation_id=conversation_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        extracted_content=extracted,
    )
    db.add(uploaded_file)
    await db.commit()
    await db.refresh(uploaded_file)
    return uploaded_file


@router.get("", response_model=list[UploadedFileOut])
async def list_files(conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[UploadedFile]:
    await _get_conversation_or_404(conversation_id, db)
    result = await db.execute(
        select(UploadedFile).where(UploadedFile.conversation_id == conversation_id)
    )
    return list(result.scalars().all())
