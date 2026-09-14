import statistics

import fitz  # PyMuPDF


def _extract_with_headings(page) -> list[str]:
    """PDFs have no semantic heading markup — approximate it by treating
    lines with above-average font size as headings, tagged so the AI can
    tell them apart from body text."""
    page_dict = page.get_text("dict")
    lines_with_size: list[tuple[str, float]] = []

    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(s["text"] for s in spans).strip()
            if not text:
                continue
            avg_size = sum(s["size"] for s in spans) / len(spans)
            lines_with_size.append((text, avg_size))

    if not lines_with_size:
        return []

    sizes = [size for _, size in lines_with_size]
    median_size = statistics.median(sizes)

    result = []
    for text, size in lines_with_size:
        if size > median_size * 1.15:  # meaningfully larger than typical body text
            result.append(f"[HEADING] {text}")
        else:
            result.append(text)
    return result


def extract(path) -> dict:
    doc = fitz.open(path)
    all_lines = []
    for page in doc:
        all_lines.extend(_extract_with_headings(page))
    page_count = doc.page_count
    doc.close()

    full_text = "\n".join(all_lines).strip()
    if not full_text:
        full_text = "[No extractable text — this PDF may be scanned/image-based]"

    return {
        "page_count": page_count,
        "text_summary": full_text,
    }
