import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import UploadedFile
from app.schemas.report import ReportContent, ReportOut
from app.services.reports import docx_export, report_service, pdf_export
router = APIRouter(prefix="/conversations/{conversation_id}/report", tags=["reports"])


@router.get("", response_model=ReportOut)
async def get_report(conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ReportOut:
    report = await report_service.get_or_create_report(conversation_id, db)
    if report.current_version is None:
        raise HTTPException(status_code=404, detail="No report content yet — send a message first")
    return report_service.to_report_out(report.current_version)

async def _build_report_docx(conversation_id: uuid.UUID, db: AsyncSession) -> tuple[ReportContent, Path]:
    report = await report_service.get_or_create_report(conversation_id, db)
    if report.current_version is None:
        raise HTTPException(status_code=404, detail="No report content yet")

    content = ReportContent.model_validate(report.current_version.content)

    settings = get_settings()
    result = await db.execute(select(UploadedFile).where(UploadedFile.conversation_id == conversation_id))
    image_paths_by_id = {
        str(f.id): Path(settings.upload_dir) / f.stored_filename for f in result.scalars().all()
    }

    docx_path = Path(tempfile.gettempdir()) / f"report_{conversation_id}.docx"
    docx_export.build_docx(content, image_paths_by_id, docx_path)
    return content, docx_path

@router.get("/export")
async def export_report(conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> FileResponse:
    content, docx_path = await _build_report_docx(conversation_id, db)
    return FileResponse(
        path=docx_path,
        filename=f"{content.title or 'report'}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
@router.get("/export/pdf")
async def export_report_pdf(conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> FileResponse:
    content, docx_path = await _build_report_docx(conversation_id, db)

    try:
        pdf_path = pdf_export.convert_docx_to_pdf(docx_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return FileResponse(path=pdf_path, filename=f"{content.title or 'report'}.pdf", media_type="application/pdf")