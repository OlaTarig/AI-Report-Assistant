import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Report, ReportVersion
from app.schemas.report import ReportContent, ReportOut, ReportPatch, ReportSection


async def get_or_create_report(conversation_id: uuid.UUID, db: AsyncSession) -> Report:
    result = await db.execute(
        select(Report)
        .where(Report.conversation_id == conversation_id)
        .options(selectinload(Report.current_version))
    )
    report = result.scalar_one_or_none()
    if report:
        return report

    report = Report(conversation_id=conversation_id)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


def current_content(report: Report) -> ReportContent:
    if report.current_version is None:
        return ReportContent(title="New Report", sections=[])
    return ReportContent.model_validate(report.current_version.content)


def _merge(base: ReportContent, patch: ReportPatch) -> ReportContent:
    """Apply a patch to the base content: update/add changed sections,
    drop removed ones, keep everything else untouched, in original order."""
    sections_by_id: dict[str, ReportSection] = {s.id: s for s in base.sections}

    # Apply removals first, so a contradictory patch (an id listed as both
    # updated and removed) resolves to "removed" rather than crashing later.
    for removed_id in patch.removed_section_ids:
        sections_by_id.pop(removed_id, None)

    for updated in patch.updated_sections:
        if updated.id in patch.removed_section_ids:
            continue
        sections_by_id[updated.id] = updated

    ordered_ids = [s.id for s in base.sections if s.id in sections_by_id]
    new_ids = [
        u.id for u in patch.updated_sections if u.id in sections_by_id and u.id not in ordered_ids
    ]
    final_order = ordered_ids + new_ids

    return ReportContent(
        title=patch.title,
        sections=[sections_by_id[sid] for sid in final_order],
    )


async def apply_patch(report: Report, patch: ReportPatch, db: AsyncSession) -> ReportVersion:
    base = current_content(report)
    new_content = _merge(base, patch)

    next_version_number = (report.current_version.version_number + 1) if report.current_version else 1

    new_version = ReportVersion(
        report_id=report.id,
        version_number=next_version_number,
        content=new_content.model_dump(),
    )
    db.add(new_version)
    await db.flush()  # assigns new_version.id without committing yet

    report.current_version_id = new_version.id

    await db.commit()
    await db.refresh(new_version)
    return new_version


def to_report_out(version: ReportVersion) -> ReportOut:
    content = ReportContent.model_validate(version.content)
    return ReportOut(title=content.title, sections=content.sections, version_number=version.version_number)
