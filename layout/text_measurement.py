"""
Deterministic Text Measurement Engine (Level 1 Pre-Render Layout Prediction)
Uses Pillow font metrics to measure text width, line heights, multiline wrapping,
and calculate dynamic font size reduction within strict limits.
"""

import os
from typing import List, Tuple, Optional, Dict, Any
from PIL import ImageFont, ImageDraw, Image

# Font cache to avoid repeated disk reads
_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}
_DUMMY_IMAGE = Image.new("RGB", (1, 1))
_DRAW = ImageDraw.Draw(_DUMMY_IMAGE)

WINDOWS_FONT_DIR = r"C:\Windows\Fonts"


def get_font(font_name: str = "arial", size_pt: int = 14) -> ImageFont.ImageFont:
    """Load TrueType font scaled to canvas pixels (1 pt in 16:9 canvas = 2.0 px)."""
    size_px = max(1, int(round(size_pt * 2.0)))
    cache_key = (font_name.lower(), size_px)
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    # Map generic names to Windows font files
    font_files = {
        "arial": "arial.ttf",
        "arial bold": "arialbd.ttf",
        "calibri": "calibri.ttf",
        "calibri bold": "calibrib.ttf",
        "segoe ui": "segoeui.ttf",
        "segoe ui bold": "segoeuib.ttf"
    }

    font_file = font_files.get(font_name.lower(), "arial.ttf")
    font_path = os.path.join(WINDOWS_FONT_DIR, font_file)

    try:
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, size_px)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    _FONT_CACHE[cache_key] = font
    return font


def measure_single_line(text: str, font_name: str, size_pt: int) -> Tuple[float, float]:
    """Returns (width_px, height_px) in canvas pixels of a single line of text."""
    if not text:
        return (0.0, float(size_pt) * 2.0 * 1.2)
    font = get_font(font_name, size_pt)
    bbox = _DRAW.textbbox((0, 0), text, font=font)
    width = float(bbox[2] - bbox[0])
    # Use font metric height or bbox height with baseline padding
    height = max(float(bbox[3] - bbox[1]), float(size_pt) * 2.0 * 1.2)
    return width, height


def wrap_text(text: str, font_name: str, size_pt: int, max_width_px: float) -> List[str]:
    """
    Deterministically wraps text into multiple lines such that no line
    exceeds max_width_px (unless a single word is longer than max_width_px).
    """
    if not text:
        return []

    font = get_font(font_name, size_pt)
    paragraphs = text.split("\n")
    wrapped_lines = []

    for para in paragraphs:
        words = para.split(" ")
        if not words or (len(words) == 1 and words[0] == ""):
            wrapped_lines.append("")
            continue

        current_line = words[0]
        for word in words[1:]:
            test_line = f"{current_line} {word}"
            bbox = _DRAW.textbbox((0, 0), test_line, font=font)
            line_w = bbox[2] - bbox[0]
            if line_w <= max_width_px:
                current_line = test_line
            else:
                wrapped_lines.append(current_line)
                current_line = word
        wrapped_lines.append(current_line)

    return wrapped_lines


def measure_multiline_text(
    text: str,
    font_name: str,
    size_pt: int,
    max_width_px: float = 0.0,
    line_spacing: float = 1.15,
    max_width: Optional[float] = None
) -> Dict[str, Any]:
    """
    Measures multiline wrapped text and returns:
    {
        'width': max_line_width,
        'height': total_height,
        'line_count': count,
        'lines': list_of_lines,
        'line_height': line_h
    }
    """
    effective_max_w = max_width if max_width is not None else max_width_px
    if not text:
        return {
            "width": 0.0,
            "height": 0.0,
            "line_count": 0,
            "lines": [],
            "line_height": float(size_pt) * 2.0 * line_spacing
        }

    lines = wrap_text(text, font_name, size_pt, effective_max_w)
    font = get_font(font_name, size_pt)

    max_w = 0.0
    for line in lines:
        bbox = _DRAW.textbbox((0, 0), line, font=font)
        w = float(bbox[2] - bbox[0])
        if w > max_w:
            max_w = w

    single_line_h = float(size_pt) * 2.0 * line_spacing
    total_h = len(lines) * single_line_h

    return {
        "width": max_w,
        "height": total_h,
        "line_count": len(lines),
        "lines": lines,
        "line_height": single_line_h
    }


def fit_text_to_budget(
    text: str,
    max_width_px: float,
    max_height_px: float,
    preferred_size_pt: int,
    minimum_size_pt: int,
    font_name: str = "arial",
    line_spacing: float = 1.15
) -> Dict[str, Any]:
    """
    Step-down font sizing within strict bounds [minimum_size_pt, preferred_size_pt].
    Never shrinks below minimum_size_pt.
    Returns measurement dict with 'fits': bool, 'font_size': int.
    """
    current_size = preferred_size_pt
    best_result = None

    while current_size >= minimum_size_pt:
        meas = measure_multiline_text(text, font_name, current_size, max_width_px, line_spacing)
        fits = (meas["width"] <= max_width_px + 0.5) and (meas["height"] <= max_height_px + 0.5)
        meas["fits"] = fits
        meas["font_size"] = current_size

        if fits:
            return meas

        best_result = meas
        current_size -= 1

    # Did not fit even at minimum size
    if best_result is None:
        best_result = measure_multiline_text(text, font_name, minimum_size_pt, max_width_px, line_spacing)
        best_result["fits"] = False
        best_result["font_size"] = minimum_size_pt
    else:
        best_result["fits"] = False

    return best_result
