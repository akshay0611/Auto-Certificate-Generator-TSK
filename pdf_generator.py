from __future__ import annotations

import io
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT_DIR = Path(__file__).resolve().parent

while not (ROOT_DIR / "assets/fonts").exists():
    parent = ROOT_DIR.parent
    if parent == ROOT_DIR:
        ROOT_DIR = Path(__file__).resolve().parent
        break
    ROOT_DIR = parent

def register_fonts():
    pdfmetrics.registerFont(
        TTFont("IBM_Plex_Regular", str(ROOT_DIR / "assets/fonts/IBMPlexSans-Regular.ttf"))
    )

register_fonts()


def safe_certificate_filename(full_name: str, workshop_id: str) -> str:
    normalized_name = re.sub(r"\s+", "_", full_name.strip())
    normalized_workshop = re.sub(r"\s+", "_", workshop_id.strip())
    cleaned_name = re.sub(r"[^A-Za-z0-9_.-]", "", normalized_name) or "participant"
    cleaned_workshop = re.sub(r"[^A-Za-z0-9_.-]", "", normalized_workshop) or "workshop"
    return f"{cleaned_name}_{cleaned_workshop}.pdf"


def _draw_field(
    drawing_canvas: canvas.Canvas,
    value: str,
    field_settings: dict[str, Any],
    url: str | None = None,
) -> None:
    font_name = field_settings["font_name"]
    font_size = float(field_settings["font_size"])
    max_width = float(field_settings.get("max_width", 0))
    line_spacing = 1.2
    
    # Auto-scale font size if max_width is set
    if max_width > 0:
        while font_size > 22:  # Preferred minimum size for aesthetics
            text_width = drawing_canvas.stringWidth(value, font_name, font_size)
            if text_width <= max_width:
                break
            font_size -= 1

    # If still exceeds max_width, wrap into multiple lines
    lines = [value]
    if max_width > 0 and drawing_canvas.stringWidth(value, font_name, font_size) > max_width:
        words = value.split()
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            if drawing_canvas.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []
        if current_line:
            lines.append(" ".join(current_line))

    drawing_canvas.setFillColor(HexColor(field_settings["color_hex"]))
    drawing_canvas.setFont(font_name, font_size)
    align = str(field_settings.get("align", "center")).lower()
    x = float(field_settings["x"])
    y = float(field_settings["y"])
    
    for i, line in enumerate(lines):
        line_y = y - (i * font_size * line_spacing)
        
        if align == "left":
            drawing_canvas.drawString(x, line_y, line)
        elif align == "right":
            drawing_canvas.drawRightString(x, line_y, line)
        else:
            drawing_canvas.drawCentredString(x, line_y, line)
            
        if url and i == 0:
            text_width = drawing_canvas.stringWidth(line, font_name, font_size)
            if align == "left":
                rect = (x, line_y - 2, x + text_width, line_y + font_size)
            elif align == "right":
                rect = (x - text_width, line_y - 2, x, line_y + font_size)
            else:
                rect = (x - text_width / 2, line_y - 2, x + text_width / 2, line_y + font_size)
            drawing_canvas.linkURL(url, rect, relative=0, thickness=0)


def _build_overlay(page_width: float, page_height: float, values: dict[str, str], settings: dict[str, Any]) -> io.BytesIO:
    overlay_stream = io.BytesIO()
    overlay_canvas = canvas.Canvas(overlay_stream, pagesize=(page_width, page_height))
    cleanup_settings = settings.get("cleanup", {})
    if cleanup_settings.get("hide_left_logo_line"):
        boxes = cleanup_settings.get("left_logo_line_boxes")
        if not boxes:
            boxes = [cleanup_settings.get("left_logo_line_box", {})]
        for box in boxes:
            overlay_canvas.setFillColor(HexColor(box.get("color_hex", "#F5F5F5")))
            overlay_canvas.setStrokeColor(HexColor(box.get("color_hex", "#F5F5F5")))
            overlay_canvas.rect(
                float(box.get("x", 61)),
                float(box.get("y", 504)),
                float(box.get("width", 3)),
                float(box.get("height", 188)),
                stroke=0,
                fill=1,
            )
    _draw_field(overlay_canvas, values["name"], settings["name"])
    _draw_field(overlay_canvas, values["workshop"], settings["workshop"])
    _draw_field(overlay_canvas, values["date"], settings["date"])
    _draw_field(overlay_canvas, values["verify_url"], settings["verify_text"], url=values["verify_url"])
    overlay_canvas.save()
    overlay_stream.seek(0)
    return overlay_stream


def generate_certificate(registration: dict[str, Any], settings: dict[str, Any], template_path: str) -> bytes:
    template = Path(template_path)
    if not template.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    full_name = str(registration.get("full_name") or "").strip() or "Participant"
    workshop_id = str(registration.get("workshop_id") or "").strip() or "Workshop"
    workshop_title = str(registration.get("workshop_title") or "").strip() or workshop_id

    date_mode = settings.get("date_mode", "generation_date")
    if date_mode == "registration_date" and registration.get("created_at"):
        date_value = str(registration["created_at"])[:10]
    else:
        date_value = datetime.now().strftime(settings["date"].get("format", "%d %b %Y"))

    registration_id = str(registration.get("id") or "")
    if not registration_id:
        raise ValueError("Registration id is required to generate verification URL.")
    short_id = registration_id[:6]
    verify_url = f"{settings['VERIFY_BASE_URL'].rstrip('/')}/{short_id}"

    values = {
        "name": full_name,
        "workshop": workshop_title,
        "date": date_value,
        "verify_url": verify_url,
    }

    reader = PdfReader(template_path)
    page = reader.pages[0]
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)

    overlay_stream = _build_overlay(width, height, values, settings)
    overlay_page = PdfReader(overlay_stream).pages[0]
    page.merge_page(overlay_page)

    writer = PdfWriter()
    writer.add_page(page)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream.getvalue()


def render_preview_image(pdf_bytes: bytes) -> bytes:
    from pdf2image import convert_from_bytes

    images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
    image = images[0]
    image_buffer = io.BytesIO()
    image.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    return image_buffer.getvalue()
