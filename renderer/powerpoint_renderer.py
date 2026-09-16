"""
PowerPoint Deck Renderer
Constructs a native .pptx PowerPoint presentation from a sequence of LayoutResult objects.
Decoupled entirely from layout logic: takes pure geometry and emits PowerPoint shapes.
Maintains a provenance map for 100% content completeness validation.
"""

from typing import List, Dict, Any, Tuple, Optional
from pptx import Presentation
from pptx.util import Inches
from layout.layout_result import LayoutResult, ComponentGeometry
from layout.coordinate_system import SLIDE_WIDTH_INCHES, SLIDE_HEIGHT_INCHES
from renderer.image_renderer import ImageRenderer
from renderer.text_renderer import TextRenderer
from renderer.list_renderer import ListRenderer
from renderer.table_renderer import TableRenderer
from renderer.chart_renderer import ChartRenderer
from renderer.component_renderer import ComponentRenderer
from models.report_model import Report, TOCItem, IndexItem, BulletListBlock, InsightBlock, ChartBlock, TableBlock, TextBlock


class PowerPointRenderer:
    def __init__(self, backgrounds_dir: str = "assets/backgrounds"):
        self.backgrounds_dir = backgrounds_dir

    def create_presentation(self, layout_results: List[LayoutResult]) -> Tuple[Presentation, Dict[str, Dict[str, Any]]]:
        """
        Builds a native PowerPoint presentation from layout results.
        Returns:
            prs: Presentation object
            provenance_map: Dict mapping input_id -> {slide_index, component_type, bounds}
        """
        prs = Presentation()
        # Enforce exact 16:9 Widescreen dimensions
        prs.slide_width = Inches(SLIDE_WIDTH_INCHES)
        prs.slide_height = Inches(SLIDE_HEIGHT_INCHES)

        # Blank layout
        blank_layout = prs.slide_layouts[6]
        provenance_map: Dict[str, Dict[str, Any]] = {}

        for slide_idx, lr in enumerate(layout_results):
            slide = prs.slides.add_slide(blank_layout)

            # 1. Render background image
            if lr.background:
                ImageRenderer.render_background(slide, lr.background, backgrounds_dir=self.backgrounds_dir)

            # 2. Render each component geometry
            for comp in lr.components:
                self._render_component(slide, comp)

                # Record provenance if ID exists
                if comp.provenance_id:
                    provenance_map[comp.provenance_id] = {
                        "slide_index": slide_idx + 1,
                        "slide_id": lr.slide_id,
                        "component_id": comp.component_id,
                        "component_type": comp.component_type,
                        "x": comp.x,
                        "y": comp.y,
                        "width": comp.width,
                        "height": comp.height
                    }

        return prs, provenance_map

    def _render_component(self, slide, comp: ComponentGeometry):
        c_type = comp.component_type

        if c_type == "text":
            style = comp.style or {}
            TextRenderer.render_text(
                slide=slide,
                text=str(comp.data),
                x=comp.x,
                y=comp.y,
                width=comp.width,
                height=comp.height,
                font_size_pt=comp.font_size or 12.0,
                bold=style.get("bold", False),
                color_hex=style.get("color", "#1F2937"),
                alignment=style.get("align", "left"),
                line_spacing=style.get("line_spacing", 1.15)
            )

        elif c_type == "toc_item" and isinstance(comp.data, TOCItem):
            ListRenderer.render_toc_item(
                slide=slide,
                item=comp.data,
                x=comp.x,
                y=comp.y,
                width=comp.width,
                height=comp.height,
                font_size=comp.font_size or 14.0
            )

        elif c_type == "index_item" and isinstance(comp.data, IndexItem):
            ListRenderer.render_index_item(
                slide=slide,
                item=comp.data,
                x=comp.x,
                y=comp.y,
                width=comp.width,
                height=comp.height,
                font_size=comp.font_size or 13.0
            )

        elif c_type == "bullet_list" and isinstance(comp.data, BulletListBlock):
            ListRenderer.render_bullet_list(
                slide=slide,
                bullet_list=comp.data,
                x=comp.x,
                y=comp.y,
                width=comp.width,
                height=comp.height,
                font_size=comp.font_size or 11.0
            )

        elif c_type == "table":
            if isinstance(comp.data, TableBlock):
                from layout.table_layout import TableLayoutEngine
                rows_data = [[c.value for c in r.cells] for r in comp.data.rows]
                tbl_layout = TableLayoutEngine.layout_table(
                    headers=comp.data.headers,
                    rows=rows_data,
                    available_width=comp.width,
                    available_height=comp.height,
                    preferred_font_size=int(comp.font_size or 9),
                    minimum_font_size=7
                )
                TableRenderer.render_table(
                    slide=slide,
                    layout_result=tbl_layout,
                    x=comp.x,
                    y=comp.y,
                    width=comp.width,
                    height=comp.height
                )
            else:
                TableRenderer.render_table(
                    slide=slide,
                    layout_result=comp.data,
                    x=comp.x,
                    y=comp.y,
                    width=comp.width,
                    height=comp.height
                )

        elif c_type == "chart":
            chart_block, chart_layout = comp.data
            ChartRenderer.render_chart(
                slide=slide,
                chart_block=chart_block,
                layout_result=chart_layout,
                x=comp.x,
                y=comp.y,
                width=comp.width,
                height=comp.height
            )

        elif c_type == "insight" and isinstance(comp.data, InsightBlock):
            ComponentRenderer.render_insight_card(
                slide=slide,
                insight=comp.data,
                x=comp.x,
                y=comp.y,
                width=comp.width,
                height=comp.height
            )
