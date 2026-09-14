from pathlib import Path

from fastapi import HTTPException

from app.services.documents import docx_service, excel_service, image_service, pdf_service

_EXTENSION_MAP = {
    ".pdf": (pdf_service, "pdf"),
    ".docx": (docx_service, "docx"),
    ".xlsx": (excel_service, "excel"),
    ".xls": (excel_service, "excel"),
    ".png": (image_service, "image"),
    ".jpg": (image_service, "image"),
    ".jpeg": (image_service, "image"),
    ".webp": (image_service, "image"),
}


def get_file_kind(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in _EXTENSION_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(_EXTENSION_MAP))}",
        )
    return _EXTENSION_MAP[ext][1]


def process_file(path: Path, filename: str) -> dict:
    """Dispatch to the right processor based on file extension and return
    its extracted-content dict, ready to store in UploadedFile.extracted_content."""
    ext = Path(filename).suffix.lower()
    if ext not in _EXTENSION_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(_EXTENSION_MAP))}",
        )

    processor, _kind = _EXTENSION_MAP[ext]
    try:
        return processor.extract(path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to process '{filename}': {exc}") from exc
