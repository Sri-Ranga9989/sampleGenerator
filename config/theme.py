"""
Centralized Design Tokens and Theme System
Defines colors, typography, chart palettes, and spacing tokens
derived from the reference Mining UGV visual standards.
"""

from typing import Tuple
from pptx.dml.color import RGBColor


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert hex color string (e.g. '#0D3166' or '0D3166') to (R, G, B)."""
    hex_clean = hex_str.lstrip('#')
    if len(hex_clean) == 3:
        hex_clean = ''.join(c * 2 for c in hex_clean)
    return (
        int(hex_clean[0:2], 16),
        int(hex_clean[2:4], 16),
        int(hex_clean[4:6], 16)
    )


def hex_to_rgb_color(hex_str: str) -> RGBColor:
    """Convert hex color string to pptx RGBColor."""
    r, g, b = hex_to_rgb(hex_str)
    return RGBColor(r, g, b)


class Theme:
    # Color Palette
    PRIMARY_NAVY = "#0D3166"       # Title, headers, primary brand
    DARK_BLUE = "#123378"          # Decorative accents
    ACCENT_BLUE = "#1E5BB0"        # Sub-accents, active items
    ACCENT_CYAN = "#3894D8"        # Highlights, chart secondary
    ACCENT_LIGHT = "#E8F0FE"       # Card backgrounds, light tints

    TEXT_DARK = "#1F2937"          # Body text, primary dark
    TEXT_MUTED = "#4A5568"         # Subtitles, secondary descriptions
    TEXT_LIGHT = "#718096"         # Footers, sources, metadata
    TEXT_WHITE = "#FFFFFF"         # Text on dark backgrounds

    BG_WHITE = "#FFFFFF"           # Slide content white canvas
    BG_CARD = "#F8FAFC"            # Insight boxes, card fills
    BORDER_LIGHT = "#D0D7DE"       # Table borders, dividers
    ROW_ALT_FILL = "#F4F7FB"       # Alternate table row shading

    # Chart Palette (Harmonious gradient-ready sequence)
    CHART_PALETTE = [
        "#0D3166",  # Deep Navy
        "#1E5BB0",  # Strong Blue
        "#3894D8",  # Medium Blue
        "#5CABE8",  # Sky Blue
        "#90CAF9",  # Soft Blue
        "#B3D8FC",  # Pale Blue
        "#D1E9FF"   # Very Light Blue
    ]

    # Typography Tokens
    FONT_PRIMARY = "Arial"
    FONT_SECONDARY = "Calibri"

    # Font Sizes (points in PPTX)
    SIZE_TITLE_COVER = 36.0        # Cover slide title
    SIZE_TITLE_SECTION = 28.0      # Section opener title
    SIZE_TITLE_SLIDE = 22.0        # Standard slide header
    SIZE_HEADING = 16.0            # Column / block heading
    SIZE_SUBHEADING = 14.0         # Card / table sub-heading
    SIZE_BODY = 12.0               # Standard body paragraph
    SIZE_BODY_SMALL = 10.0         # Secondary notes, bullets
    SIZE_TABLE_HEADER = 11.0       # Table header text
    SIZE_TABLE_CELL = 10.0         # Table data cell
    SIZE_FOOTER = 8.5              # Source, footer notes

    # Minimum Font Size Clamps (Never shrink below these)
    MIN_SIZE_TITLE = 18.0
    MIN_SIZE_HEADING = 12.0
    MIN_SIZE_BODY = 9.0
    MIN_SIZE_TABLE_CELL = 7.5
    MIN_SIZE_TOC_ITEM = 12.0

    # Spacing Tokens (in reference pixels)
    SPACING_XS = 8
    SPACING_SM = 16
    SPACING_MD = 24
    SPACING_LG = 36
    SPACING_XL = 48
