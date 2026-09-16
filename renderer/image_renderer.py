"""
Shared Image Renderer
Renders full-slide backgrounds and inline hero visuals preserving aspect ratio.
"""

import os
from pptx.slide import Slide as PptxSlide
from pptx.util import Inches
from layout.coordinate_system import bbox_to_pptx_emu, px_to_emu, CANVAS_WIDTH_PX, CANVAS_HEIGHT_PX


class ImageRenderer:
    @staticmethod
    def render_background(slide: PptxSlide, asset_filename: str, backgrounds_dir: str = "assets/backgrounds"):
        """Renders full-bleed slide background image (1920x1080)."""
        bg_path = os.path.join(backgrounds_dir, asset_filename)
        if not os.path.exists(bg_path):
            return None

        # Full canvas dimensions
        left = 0
        top = 0
        width = px_to_emu(CANVAS_WIDTH_PX)
        height = px_to_emu(CANVAS_HEIGHT_PX)

        pic = slide.shapes.add_picture(bg_path, left, top, width=width, height=height)
        # Move background picture to the back
        slide.shapes._spTree.remove(pic._element)
        slide.shapes._spTree.insert(2, pic._element)
        return pic

    @staticmethod
    def render_image(
        slide: PptxSlide,
        image_path: str,
        x: float,
        y: float,
        width: float,
        height: float
    ):
        """Renders an image inside a specified reference pixel bounding box."""
        if not os.path.exists(image_path):
            return None

        left, top, w, h = bbox_to_pptx_emu(x, y, width, height)
        pic = slide.shapes.add_picture(image_path, left, top, width=w, height=h)
        return pic
