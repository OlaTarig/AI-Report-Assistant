import subprocess
from pathlib import Path


def convert_docx_to_pdf(docx_path: Path) -> Path:
    """Shells out to LibreOffice in headless mode to convert an existing
    .docx into .pdf, preserving its exact formatting — reuses the same
    Word document we already build, rather than reimplementing tables,
    colors, and images in a separate PDF library."""
    output_dir = docx_path.parent
    try:
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(docx_path)],
            check=True,
            timeout=60,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"PDF conversion failed: {exc.stderr.decode(errors='replace')}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("PDF conversion timed out") from exc

    pdf_path = output_dir / f"{docx_path.stem}.pdf"
    if not pdf_path.exists():
        raise RuntimeError("PDF conversion did not produce an output file")
    return pdf_path