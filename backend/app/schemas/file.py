import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadedFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    mime_type: str
    size_bytes: int
    created_at: datetime
