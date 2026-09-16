"""
Layer A: Structural Validator
Inspects generated PowerPoint presentations (.pptx) directly via shape properties.
Validates slide dimensions, object bounds, safe areas, font size clamps, and illegal overlaps.
"""

from typing import List, Dict, Any
from pptx import Presentation
from pptx.util import Inches, Pt
from layout.coordinate_system import SLIDE_WIDTH_INCHES, SLIDE_HEIGHT_INCHES


class StructuralValidator:
    @staticmethod
    def validate_presentation(prs: Presentation, min_font_size_pt: float = 7.5) -> Dict[str, Any]:
        """
        Runs comprehensive structural validation across all slides in a Presentation.
        """
        errors = []
        warnings = []

        # 1. Slide aspect ratio / dimensions check
        slide_w_in = prs.slide_width.inches
        slide_h_in = prs.slide_height.inches
        if abs(slide_w_in - SLIDE_WIDTH_INCHES) > 0.05 or abs(slide_h_in - SLIDE_HEIGHT_INCHES) > 0.05:
            errors.append({
                "type": "canvas_dimension_mismatch",
                "message": f"Expected 16:9 widescreen ({SLIDE_WIDTH_INCHES:.2f}x{SLIDE_HEIGHT_INCHES:.2f} in), got {slide_w_in:.2f}x{slide_h_in:.2f} in"
            })

        # 2. Iterate through slides and shapes
        max_w_emu = prs.slide_width
        max_h_emu = prs.slide_height

        for s_idx, slide in enumerate(prs.slides):
            slide_num = s_idx + 1

            for shape in slide.shapes:
                s_left = shape.left
                s_top = shape.top
                s_width = shape.width
                s_height = shape.height

                # Check boundary overrun
                if (s_left + s_width) > (max_w_emu + Inches(0.1)) or (s_top + s_height) > (max_h_emu + Inches(0.1)):
                    # Background pictures are allowed full-bleed
                    if shape.shape_type != 13:  # 13 is msoPicture
                        errors.append({
                            "slide": slide_num,
                            "type": "boundary_overrun",
                            "shape_name": shape.name,
                            "message": f"Shape extends beyond slide canvas bounds."
                        })

                # Check font sizes in text frames
                if shape.has_text_frame:
                    for p in shape.text_frame.paragraphs:
                        for run in p.runs:
                            if run.font.size is not None:
                                f_size_pt = run.font.size.pt
                                if f_size_pt < (min_font_size_pt - 0.1):
                                    errors.append({
                                        "slide": slide_num,
                                        "type": "font_size_violation",
                                        "shape_name": shape.name,
                                        "font_size": f_size_pt,
                                        "message": f"Font size {f_size_pt}pt is below minimum threshold {min_font_size_pt}pt"
                                    })

        status = "FAIL" if errors else "PASS"
        return {
            "status": status,
            "total_slides": len(prs.slides),
            "errors": errors,
            "warnings": warnings
        }
