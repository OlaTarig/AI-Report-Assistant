import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from app.schemas.report import ReportContent

ACCENT_COLOR = RGBColor(0x1F, 0x4E, 0x79)
HEADER_FILL = "1F4E79"
HEADER_TEXT_COLOR = RGBColor(0xFF, 0xFF, 0xFF)
CUSTOM_HEADER_TEXT_COLOR = RGBColor(0x3A, 0x2E, 0x2A)
DEFAULT_BODY_SIZE = Pt(12)

# <font> now matches ANY combination/order of name/size/color attributes —
# previously required a fixed order (name, then size, then color), which
# silently failed to match whenever the AI wrote them in a different order.
_INLINE_PATTERN = re.compile(
    r'(\*\*\*.+?\*\*\*|\*\*.+?\*\*|\*.+?\*|<mark color="\w+">.*?</mark>|<color name="\w+">.*?</color>'
    r'|<font(?:\s+\w+="[^"]*")*\s*>.*?</font>)',
    re.DOTALL,
)
_FONT_TAG_PATTERN = re.compile(r'<font((?:\s+\w+="[^"]*")*)\s*>(.*?)</font>', re.DOTALL)
_ATTR_PATTERN = re.compile(r'(\w+)="([^"]*)"')

_FONT_NAME_ALIASES = {
    "default": "Calibri",
    "serif": "Georgia",
    "mono": "Consolas",
    "times": "Times New Roman",
}
_MARK_PATTERN = re.compile(r'<mark color="(\w+)">(.*?)</mark>', re.DOTALL)
_COLOR_PATTERN = re.compile(r'<color name="(\w+)">(.*?)</color>', re.DOTALL)

_HIGHLIGHT_COLORS = {
    "yellow": WD_COLOR_INDEX.YELLOW,
    "green": WD_COLOR_INDEX.BRIGHT_GREEN,
    "red": WD_COLOR_INDEX.RED,
    "blue": WD_COLOR_INDEX.BLUE,
    "pink": WD_COLOR_INDEX.PINK,
    "gray": WD_COLOR_INDEX.GRAY_25,
}
_FONT_COLORS = {
    "yellow": RGBColor(0xC9, 0xA2, 0x00),
    "green": RGBColor(0x1E, 0x7B, 0x34),
    "red": RGBColor(0xC0, 0x1C, 0x1C),
    "blue": RGBColor(0x1F, 0x4E, 0x79),
    "pink": RGBColor(0xC2, 0x18, 0x5B),
    "gray": RGBColor(0x59, 0x59, 0x59),
    "orange": RGBColor(0xD9, 0x73, 0x0D),
    "purple": RGBColor(0x6A, 0x1B, 0x9A),
    "black": RGBColor(0x00, 0x00, 0x00),
}
_CELL_BG_PATTERN = re.compile(r"^\[\[bg:(\w+)\]\](.*)", re.DOTALL)
_CELL_BG_HEX = {
    "yellow": "FFF3B0",
    "green": "C6E8C6",
    "red": "F4C7C3",
    "blue": "C9DDF2",
    "pink": "F5C6DE",
    "gray": "E0E0E0",
    "orange": "FFDAB3",
    "purple": "E3D0F0",
}
_MD_SEPARATOR_ROW = re.compile(r"^\|[\s:\-|]+\|$")


def _parse_markdown_table(text: str) -> tuple[list[str], list[list[str]]] | None:
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


def _add_page_number(section) -> None:
    footer = section.footer
    paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = paragraph.add_run()
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")

    run._r.append(fld_char_begin)
    run._r.append(instr_text)
    run._r.append(fld_char_end)


def _shade_cell(cell, hex_color: str) -> None:
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(shading)


def _render_marks_into_paragraph(paragraph, text: str) -> None:
    pos = 0
    for match in _INLINE_PATTERN.finditer(text):
        if match.start() > pos:
            paragraph.add_run(text[pos : match.start()]).font.size = DEFAULT_BODY_SIZE

        token = match.group(0)
        if token.startswith("***"):
            run = paragraph.add_run(token[3:-3])
            run.bold = True
            run.italic = True
            run.font.size = DEFAULT_BODY_SIZE
        elif token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
            run.font.size = DEFAULT_BODY_SIZE
        elif token.startswith("<mark"):
            m = _MARK_PATTERN.match(token)
            run = paragraph.add_run(m.group(2))
            run.font.highlight_color = _HIGHLIGHT_COLORS.get(m.group(1).lower(), WD_COLOR_INDEX.YELLOW)
            run.font.size = DEFAULT_BODY_SIZE
        elif token.startswith("<color"):
            m = _COLOR_PATTERN.match(token)
            run = paragraph.add_run(m.group(2))
            run.font.color.rgb = _FONT_COLORS.get(m.group(1).lower(), RGBColor(0x00, 0x00, 0x00))
            run.font.size = DEFAULT_BODY_SIZE
        elif token.startswith("<font"):
            m = _FONT_TAG_PATTERN.match(token)
            attrs = dict(_ATTR_PATTERN.findall(m.group(1)))
            inner_text = m.group(2)
            font_key = attrs.get("name")
            size_str = attrs.get("size")
            color_key = attrs.get("color")

            # Recurse in case the AI nested another tag (e.g. <color>)
            # inside <font> despite being told not to — this way nested
            # content still renders correctly instead of showing as raw
            # literal tag text.
            start_index = len(paragraph.runs)
            _render_marks_into_paragraph(paragraph, inner_text)
            new_runs = paragraph.runs[start_index:]
            if not new_runs:
                continue
            for run in new_runs:
                if font_key:
                    run.font.name = _FONT_NAME_ALIASES.get(font_key.lower(), font_key)
                run.font.size = Pt(int(size_str)) if size_str else DEFAULT_BODY_SIZE
                # Only apply <font>'s own color if this run didn't already
                # get one from a nested <color>/<mark> tag during recursion.
                if color_key and run.font.color.rgb is None:
                    run.font.color.rgb = _FONT_COLORS.get(color_key.lower(), RGBColor(0x00, 0x00, 0x00))
        else:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
            run.font.size = DEFAULT_BODY_SIZE

        pos = match.end()

    if pos < len(text):
        paragraph.add_run(text[pos:]).font.size = DEFAULT_BODY_SIZE


def _add_paragraph_with_marks(doc: Document, text: str):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(8)
    _render_marks_into_paragraph(paragraph, text)
    return paragraph


def _add_table(doc: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = True

    header_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        para = header_cells[i].paragraphs[0]
        bg_match = _CELL_BG_PATTERN.match(header_text)
        if bg_match:
            color_name, actual_text = bg_match.group(1), bg_match.group(2)
            _render_marks_into_paragraph(para, actual_text)
            _shade_cell(header_cells[i], _CELL_BG_HEX.get(color_name.lower(), HEADER_FILL))
            text_color = CUSTOM_HEADER_TEXT_COLOR
        else:
            _render_marks_into_paragraph(para, header_text)
            _shade_cell(header_cells[i], HEADER_FILL)
            text_color = HEADER_TEXT_COLOR

        for run in para.runs:
            run.font.color.rgb = text_color
            run.font.bold = True

    for row_data in rows:
        row_cells = table.add_row().cells
        for i, value in enumerate(row_data):
            bg_match = _CELL_BG_PATTERN.match(value)
            if bg_match:
                color_name, actual_value = bg_match.group(1), bg_match.group(2)
                _render_marks_into_paragraph(row_cells[i].paragraphs[0], actual_value)
                _shade_cell(row_cells[i], _CELL_BG_HEX.get(color_name.lower(), "FFFFFF"))
            else:
                _render_marks_into_paragraph(row_cells[i].paragraphs[0], value)

    doc.add_paragraph()


def _add_images(doc: Document, image_paths: list[Path]) -> None:
    if not image_paths:
        return

    if len(image_paths) == 1:
        doc.add_picture(str(image_paths[0]), width=Inches(4))
        return

    columns = 2 if len(image_paths) <= 4 else 3
    cell_width = Inches(6 / columns)

    rows_needed = (len(image_paths) + columns - 1) // columns
    grid = doc.add_table(rows=rows_needed, cols=columns)
    grid.autofit = True

    for idx, img_path in enumerate(image_paths):
        cell = grid.rows[idx // columns].cells[idx % columns]
        paragraph = cell.paragraphs[0]
        run = paragraph.add_run()
        run.add_picture(str(img_path), width=cell_width)

    doc.add_paragraph()


def build_docx(content: ReportContent, image_paths_by_id: dict[str, Path], output_path: Path) -> Path:
    doc = Document()
    doc.styles["Normal"].font.size = DEFAULT_BODY_SIZE

    section = doc.sections[0]
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    _add_page_number(section)

    title_paragraph = doc.add_heading(content.title, level=0)
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title_paragraph.runs:
        run.font.color.rgb = ACCENT_COLOR

    for sec in content.sections:
        heading_paragraph = doc.add_heading("", level=1)
        _render_marks_into_paragraph(heading_paragraph, sec.heading)
        for run in heading_paragraph.runs:
            if not run.font.color.rgb:
                run.font.color.rgb = ACCENT_COLOR

        for para_text in sec.body.split("\n\n"):
            block = para_text.strip()
            if not block:
                continue
            parsed = _parse_markdown_table(block)
            if parsed:
                _add_table(doc, parsed[0], parsed[1])
            else:
                _add_paragraph_with_marks(doc, block)

        if sec.table:
            _add_table(doc, sec.table.headers, sec.table.rows)

        section_image_paths = [
            image_paths_by_id[fid] for fid in sec.image_file_ids if fid in image_paths_by_id
        ]
        _add_images(doc, section_image_paths)

    doc.save(output_path)
    return output_path