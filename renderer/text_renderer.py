"""
Shared Text Renderer
Renders headings, paragraphs, subtitles, and labels with exact typography tokens.
"""

from typing import Optional, Dict, Any
from pptx.slide import Slide as PptxSlide
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN
from layout.coordinate_system import bbox_to_pptx_emu
from config.theme import Theme, hex_to_rgb_color


class TextRenderer:
    @staticmethod
    def render_text(
        slide: PptxSlide,
        text: str,
        x: float,
        y: float,
        width: float,
        height: float,
        font_size_pt: float = 12.0,
        font_name: str = Theme.FONT_PRIMARY,
        bold: bool = False,
        color_hex: str = Theme.TEXT_DARK,
        alignment: str = "left",
        vertical_alignment: str = "top",
        line_spacing: float = 1.15
    ):
        """Creates a PowerPoint text box with precise coordinates and typography."""
        left, top, w, h = bbox_to_pptx_emu(x, y, width, height)
        tx_box = slide.shapes.add_textbox(left, top, w, h)
        tf = tx_box.text_frame
        tf.word_wrap = True
        
        # Zero out default internal margins for precise alignment
        tf.margin_left = Pt(2)
        tf.margin_right = Pt(2)
        tf.margin_top = Pt(2)
        tf.margin_bottom = Pt(2)

        p = tf.paragraphs[0]
        p.text = text
        p.font.name = font_name
        p.font.size = Pt(font_size_pt)
        p.font.bold = bold
        p.font.color.rgb = hex_to_rgb_color(color_hex)
        p.line_spacing = line_spacing

        # Alignment
        align_map = {
            "left": PP_ALIGN.LEFT,
            "center": PP_ALIGN.CENTER,
            "right": PP_ALIGN.RIGHT,
            "justify": PP_ALIGN.JUSTIFY
        }
        p.alignment = align_map.get(alignment.lower(), PP_ALIGN.LEFT)

        return tx_box
