import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"), unique=True
    )  # unique = enforces one report per conversation at the DB level

    # Nullable because a Report can briefly exist with zero versions
    # (created, then its first version inserted) — see report_service.
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("report_versions.id", use_alter=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="report")

    versions: Mapped[list["ReportVersion"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        foreign_keys="ReportVersion.report_id",
        order_by="ReportVersion.version_number",
    )
    current_version: Mapped["ReportVersion | None"] = relationship(
        foreign_keys=[current_version_id], post_update=True
    )
