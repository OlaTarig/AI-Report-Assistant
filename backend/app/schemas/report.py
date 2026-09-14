from pydantic import BaseModel, Field


class ReportTable(BaseModel):
    headers: list[str]
    rows: list[list[str]]


class ReportSection(BaseModel):
    id: str
    heading: str
    body: str
    table: ReportTable | None = Field(default=None, description="Tabular data for this section, if any.")
    image_file_ids: list[str] = Field(
        default_factory=list,
        description="IDs of previously uploaded image files to embed in this section, if relevant.",
    )


class ReportContent(BaseModel):
    """The full, current shape of a report — what's stored in ReportVersion.content."""

    title: str
    sections: list[ReportSection] = []


class ReportPatch(BaseModel):
    """What the AI returns for an edit: only what changed, not the whole report."""

    title: str = Field(
        description="The report's current title. If it isn't changing, repeat the existing title "
        "exactly as given in the current report state. Never output a generic placeholder like "
        "'New Report' once real content exists."
    )
    updated_sections: list[ReportSection] = Field(
        default_factory=list,
        description="Sections that are new or whose content changed. Only include sections "
        "that actually changed — do not include unchanged sections.",
    )
    removed_section_ids: list[str] = Field(
        default_factory=list, description="IDs of sections to delete, if any."
    )


class AssistantTurn(BaseModel):
    reply: str = Field(description="The conversational reply to show the user in chat.")
    patch: ReportPatch


class ReportOut(BaseModel):
    title: str
    sections: list[ReportSection]
    version_number: int
