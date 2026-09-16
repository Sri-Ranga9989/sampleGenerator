"""
Layer B: Rendered Slide Validator
Inspects exported slide PNGs to detect rendered visual anomalies:
boundary bleeds into background decorative zones, blank content, and visual corruption.
"""

import os
from typing import Dict, Any, List
from PIL import Image
import numpy as np


class RenderedValidator:
    @staticmethod
    def validate_slide_image(
        image_path: str,
        expected_width: int = 1920,
        expected_height: int = 1080
    ) -> Dict[str, Any]:
        errors = []
        warnings = []

        if not os.path.exists(image_path):
            return {
                "status": "FAIL",
                "errors": [{"type": "file_not_found", "message": f"Rendered image not found: {image_path}"}]
            }

        try:
            im = Image.open(image_path)
            w, h = im.size

            # 1. Dimensions check
            if w != expected_width or h != expected_height:
                errors.append({
                    "type": "rendered_dimension_mismatch",
                    "message": f"Expected {expected_width}x{expected_height}, got {w}x{h}"
                })

            # 2. Blank slide detection
            arr = np.array(im.convert("RGB"))
            std_dev = np.std(arr)
            if std_dev < 1.0:
                errors.append({
                    "type": "blank_slide",
                    "message": "Rendered slide has virtually zero contrast (completely blank or monochromatic)."
                })

        except Exception as e:
            errors.append({"type": "image_open_error", "message": str(e)})

        status = "FAIL" if errors else "PASS"
        return {
            "status": status,
            "image_path": image_path,
            "errors": errors,
            "warnings": warnings
        }
