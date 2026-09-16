"""
Centralized Coordinate System Converter
Translates 1920x1080 reference pixel canvas coordinates into PowerPoint units (Inches, Points, EMUs).
"""

from pptx.util import Inches, Pt, Emu

# Canonical canvas dimensions
CANVAS_WIDTH_PX = 1920
CANVAS_HEIGHT_PX = 1080
ASPECT_RATIO = "16:9"

# PowerPoint 16:9 Widescreen dimensions
SLIDE_WIDTH_INCHES = 13.333333333333334
SLIDE_HEIGHT_INCHES = 7.5

# Conversion multipliers
PX_TO_INCHES = SLIDE_WIDTH_INCHES / CANVAS_WIDTH_PX   # ~0.006944444444444445 in/px
PX_TO_PT = PX_TO_INCHES * 72.0                        # 0.5 pt/px
PX_TO_EMU_FACTOR = 914400 * PX_TO_INCHES              # 6350 emu/px


def px_to_inches(px: float) -> float:
    """Convert reference pixels to inches."""
    return float(px) * PX_TO_INCHES


def px_to_pt(px: float) -> float:
    """Convert reference pixels to typographic points."""
    return float(px) * PX_TO_PT


def px_to_emu(px: float) -> Emu:
    """Convert reference pixels to PowerPoint EMUs."""
    return Emu(int(round(float(px) * PX_TO_EMU_FACTOR)))


def pt_to_emu(pt: float) -> Emu:
    """Convert typographic points to EMUs."""
    return Pt(pt)


def bbox_to_pptx_emu(x: float, y: float, width: float, height: float):
    """
    Convert a reference bounding box (x, y, width, height in 1920x1080 px)
    into PowerPoint (left, top, width, height) in EMUs.
    """
    return (
        px_to_emu(x),
        px_to_emu(y),
        px_to_emu(width),
        px_to_emu(height)
    )


def bbox_to_pptx_inches(x: float, y: float, width: float, height: float):
    """
    Convert a reference bounding box into PowerPoint (left, top, width, height) in Inches.
    """
    return (
        Inches(px_to_inches(x)),
        Inches(px_to_inches(y)),
        Inches(px_to_inches(width)),
        Inches(px_to_inches(height))
    )
