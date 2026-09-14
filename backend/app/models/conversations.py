import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), default="New Report")
    language: Mapped[str] = mapped_column(String(2), default="en")  # "en" | "ar"

    # Nullable for now (single-user MVP); populated once real auth is added,
    # so this doesn't need a migration fight later.
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )
    files: Mapped[list["UploadedFile"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    report: Mapped["Report | None"] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
