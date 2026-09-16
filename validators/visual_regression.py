"""
Visual Regression Validator
Compares generated slide PNG against the authoritative reference PNG.
If reference PNG is absent, status is strictly SKIPPED (never passed).
"""

import os
from typing import Dict, Any, Optional
from PIL import Image, ImageChops
import numpy as np


class VisualRegressionValidator:
    @staticmethod
    def compare_images(
        reference_path: str,
        generated_path: str,
        diff_output_dir: str = "assets/templates/mining_ugv/diff",
        tolerance_percent: float = 5.0
    ) -> Dict[str, Any]:
        """
        Compares reference PNG against generated PNG.
        Returns:
            status: PASS, FAIL, or SKIPPED
        """
        # Rule 1: If authoritative reference image is missing, return SKIPPED
        if not os.path.exists(reference_path):
            return {
                "status": "SKIPPED",
                "message": f"Authoritative reference PNG not found at: {reference_path}. Comparison skipped.",
                "reference_path": reference_path,
                "generated_path": generated_path
            }

        if not os.path.exists(generated_path):
            return {
                "status": "FAIL",
                "message": f"Generated PNG not found at: {generated_path}.",
                "reference_path": reference_path,
                "generated_path": generated_path
            }

        try:
            ref_img = Image.open(reference_path).convert("RGB")
            gen_img = Image.open(generated_path).convert("RGB")

            # Check dimensions match
            if ref_img.size != gen_img.size:
                gen_img = gen_img.resize(ref_img.size)

            diff = ImageChops.difference(ref_img, gen_img)
            diff_arr = np.array(diff)

            # Calculate pixel diff percentage
            total_pixels = diff_arr.shape[0] * diff_arr.shape[1]
            diff_pixels = np.count_nonzero(np.any(diff_arr > 20, axis=2))
            diff_pct = (diff_pixels / total_pixels) * 100.0

            # Save diff image
            os.makedirs(diff_output_dir, exist_ok=True)
            diff_filename = f"{os.path.splitext(os.path.basename(generated_path))[0]}_diff.png"
            diff_save_path = os.path.join(diff_output_dir, diff_filename)
            diff.save(diff_save_path)

            status = "PASS" if diff_pct <= tolerance_percent else "FAIL"
            return {
                "status": status,
                "diff_percentage": round(diff_pct, 2),
                "diff_image_path": diff_save_path,
                "tolerance": tolerance_percent
            }

        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Error during image comparison: {e}"
            }
