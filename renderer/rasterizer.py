"""
PowerPoint Slide Rasterizer
Uses native Microsoft PowerPoint COM automation on Windows to export slides directly to 1920x1080 PNGs.
Enables Layer B (RenderedValidator) and Visual Regression testing with authentic PowerPoint rendering.
"""

import os
import sys
from typing import List, Optional


class PowerPointRasterizer:
    @staticmethod
    def is_available() -> bool:
        """Checks if win32com and PowerPoint COM automation are available."""
        try:
            import win32com.client
            app = win32com.client.Dispatch("PowerPoint.Application")
            app.Quit()
            return True
        except Exception:
            return False

    @staticmethod
    def rasterize_pptx(pptx_path: str, output_dir: str, width: int = 1920, height: int = 1080) -> List[str]:
        """
        Exports each slide of pptx_path as a high-resolution PNG in output_dir.
        Returns a list of absolute paths to the exported PNG files.
        """
        abs_pptx = os.path.abspath(pptx_path)
        os.makedirs(output_dir, exist_ok=True)

        try:
            import win32com.client
            # 1 = ppFixedFormatTypePNG, or slide.Export
            app = win32com.client.Dispatch("PowerPoint.Application")
            app.Visible = 1  # Often required by PowerPoint COM
            pres = app.Presentations.Open(abs_pptx, WithWindow=False)
            
            output_pngs = []
            for idx, slide in enumerate(pres.Slides):
                png_path = os.path.join(output_dir, f"slide_{idx + 1:02d}.png")
                abs_png = os.path.abspath(png_path)
                slide.Export(abs_png, "PNG", width, height)
                output_pngs.append(abs_png)

            pres.Close()
            app.Quit()
            return output_pngs
        except Exception as e:
            print(f"[RASTERIZER WARNING] PowerPoint COM export failed: {e}")
            return []
