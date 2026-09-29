import re
from pathlib import Path

import openpyxl
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font, PatternFill

from app.schemas.report import ReportContent

ACCENT_COLOR = "1F4E79"
HEADER_FILL = PatternFill(start_color="FFE8D6", end_color="FFE8D6", fill_type="solid")

_TAG_PATTERN = re.compile(
    r'\*\*(.+?)\*\*|\*(.+?)\*|<mark color="\w+">(.*?)</mark>|<color name="\w+">(.*?)</color>'
    r'|<font(?: name="\w+")?(?: size="\d+")?>(.*?)</font>',
    re.DOTALL,
)

_CELL_BG_PATTERN = re.compile(r"^\[\[bg:(\w+)\]\](.*)", re.DOTALL)
_CELL_BG_FILLS = {
    name: PatternFill(start_color=hexcode, end_color=hexcode, fill_type="solid")
    for name, hexcode in {
        "yellow": "FFF3B0",
        "green": "C6E8C6",
        "red": "F4C7C3",
        "blue": "C9DDF2",
        "pink": "F5C6DE",
        "gray": "E0E0E0",
        "orange": "FFDAB3",
        "purple": "E3D0F0",
    }.items()
}

_MD_SEPARATOR_ROW = re.compile(r"^\|[\s:\-|]+\|$")


def _parse_markdown_table(text: str) -> tuple[list[str], list[list[str]]] | None:
    """Same safety net as docx_export: catches a markdown pipe-table
    written in body text and renders it as real spreadsheet rows instead
    of a wall of pipe characters in one cell."""
    lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
    if len(lines) < 2:
        return None
    if not all(ln.startswith("|") and ln.endswith("|") for ln in lines):
        return None
    if not _MD_SEPARATOR_ROW.match(lines[1]):
        return None

    def split_row(ln: str) -> list[str]:
        return [c.strip() for c in ln.strip("|").split("|")]

    headers = split_row(lines[0])
    rows = [split_row(ln) for ln in lines[2:]]
    return headers, rows


def _strip_formatting(text: str) -> str:
    def _replace(m: re.Match) -> str:
        return next(g for g in m.groups() if g is not None)

    return _TAG_PATTERN.sub(_replace, text)


def _write_table(ws, start_row: int, headers: list[str], rows: list[list[str]]) -> int:
    """Writes a table's headers and rows starting at start_row, honoring
    per-cell [[bg:COLOR]] backgrounds on both headers and data cells.
    Returns the next free row after the table."""
    row = start_row
    for col_idx, header in enumerate(headers, start=1):
        bg_match = _CELL_BG_PATTERN.match(header)
        if bg_match:
            color_name, actual_text = bg_match.group(1), bg_match.group(2)
            cell = ws.cell(row=row, column=col_idx, value=_strip_formatting(actual_text))
            cell.fill = _CELL_BG_FILLS.get(color_name.lower(), HEADER_FILL)
        else:
            cell = ws.cell(row=row, column=col_idx, value=_strip_formatting(header))
            cell.fill = HEADER_FILL
        cell.font = Font(bold=True)
    row += 1

    for data_row in rows:
        for col_idx, value in enumerate(data_row, start=1):
            bg_match = _CELL_BG_PATTERN.match(value)
            if bg_match:
                color_name, actual_value = bg_match.group(1), bg_match.group(2)
                cell = ws.cell(row=row, column=col_idx, value=_strip_formatting(actual_value))
                cell.fill = _CELL_BG_FILLS.get(color_name.lower(), cell.fill)
            else:
                ws.cell(row=row, column=col_idx, value=_strip_formatting(value))
        row += 1

    return row


def build_xlsx(content: ReportContent, image_paths_by_id: dict[str, Path], output_path: Path) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report"

    ws.column_dimensions["A"].width = 60
    for col in "BCDEFG":
        ws.column_dimensions[col].width = 20

    row = 1
    title_cell = ws.cell(row=row, column=1, value=content.title)
    title_cell.font = Font(size=16, bold=True, color=ACCENT_COLOR)
    row += 2

    for sec in content.sections:
        heading_cell = ws.cell(row=row, column=1, value=sec.heading)
        heading_cell.font = Font(size=13, bold=True, color=ACCENT_COLOR)
        row += 1

        for block in sec.body.split("\n\n"):
            block = block.strip()
            if not block:
                continue
            parsed = _parse_markdown_table(block)
            if parsed:
                row = _write_table(ws, row, parsed[0], parsed[1])
                row += 1
            else:
                plain_body = _strip_formatting(block)
                body_cell = ws.cell(row=row, column=1, value=plain_body)
                body_cell.alignment = Alignment(wrap_text=True, vertical="top")
                ws.row_dimensions[row].height = max(15, 15 * (plain_body.count("\n") + 2))
                row += 1

        if sec.table:
            row = _write_table(ws, row, sec.table.headers, sec.table.rows)

        for fid in sec.image_file_ids:
            path = image_paths_by_id.get(fid)
            if path and path.exists():
                try:
                    img = XLImage(str(path))
                    img.width = 300
                    img.height = 200
                    ws.add_image(img, f"A{row}")
                    row += 12
                except Exception:
                    pass

        row += 1

    wb.save(output_path)
    return output_path