from PIL import Image


def extract(path) -> dict:
    with Image.open(path) as img:
        width, height = img.size
        format_ = img.format

    return {
        "width": width,
        "height": height,
        "format": format_,
        "text_summary": f"[Image: {width}x{height} {format_}]",
    }
