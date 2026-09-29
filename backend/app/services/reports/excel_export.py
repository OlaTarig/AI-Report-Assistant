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


def _strip_formatting(text: str) -> str:
    """Excel cells don't support per-character rich formatting the way
    Word runs do, so rather than show the literal markdown/tag markup, we
    strip it and keep the plain text for the spreadsheet export."""

    def _replace(m: re.Match) -> str:
        return next(g for g in m.groups() if g is not None)

    return _TAG_PATTERN.sub(_replace, text)


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

        if sec.body.strip():
            plain_body = _strip_formatting(sec.body)
            body_cell = ws.cell(row=row, column=1, value=plain_body)
            body_cell.alignment = Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[row].height = max(15, 15 * (plain_body.count("\n") + 2))
            row += 1

        if sec.table:
            row += 1
            for col_idx, header in enumerate(sec.table.headers, start=1):
                cell = ws.cell(row=row, column=col_idx, value=header)
                cell.font = Font(bold=True)
                cell.fill = HEADER_FILL
            row += 1
            for data_row in sec.table.rows:
                for col_idx, value in enumerate(data_row, start=1):
                    bg_match = _CELL_BG_PATTERN.match(value)
                    if bg_match:
                        color_name, actual_value = bg_match.group(1), bg_match.group(2)
                        cell = ws.cell(row=row, column=col_idx, value=_strip_formatting(actual_value))
                        cell.fill = _CELL_BG_FILLS.get(color_name.lower(), cell.fill)
                    else:
                        ws.cell(row=row, column=col_idx, value=_strip_formatting(value))
                row += 1

        for fid in sec.image_file_ids:
            path = image_paths_by_id.get(fid)
            if path and path.exists():
                try:
                    img = XLImage(str(path))
                    img.width = 300
                    img.height = 200
                    ws.add_image(img, f"A{row}")
                    row += 12  # reserve enough rows so the next section doesn't overlap the image
                except Exception:
                    pass  # skip a file openpyxl can't read as an image rather than failing the export

        row += 1  # blank separator row between sections

    wb.save(output_path)
    return output_path