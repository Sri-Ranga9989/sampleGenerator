"""
Template Renderer
Executes layout algorithms for all 8 fundamental templates.
Emits decoupled LayoutResult objects and creates continuation slides when content overflows.
"""

import json
import os
from typing import List, Dict, Any, Optional
from layout.layout_result import LayoutResult, RegionGeometry, ComponentGeometry
from layout.text_measurement import measure_multiline_text, fit_text_to_budget
from layout.table_layout import TableLayoutEngine, TableLayoutResult
from layout.chart_layout import ChartLayoutEngine, ChartLayoutResult
from layout.stack_layout import StackLayoutEngine
from layout.overflow_engine import OverflowEngine
from models.report_model import Report, Slide, TextBlock, BulletListBlock, TableBlock, ChartBlock, InsightBlock, TOCItem, IndexItem, ImageBlock
from config.theme import Theme


class TemplateRenderer:
    def __init__(self, annotations_dir: str = "assets/templates/mining_ugv/annotations"):
        self.annotations_dir = annotations_dir
        self.annotations_cache: Dict[str, Dict[str, Any]] = {}
        self.overflow_engine = OverflowEngine()

    def get_annotation(self, template_id: str) -> Dict[str, Any]:
        if template_id not in self.annotations_cache:
            path = os.path.join(self.annotations_dir, f"{template_id}.json")
            with open(path, "r", encoding="utf-8") as f:
                self.annotations_cache[template_id] = json.load(f)
        return self.annotations_cache[template_id]

    def render_slide_layout(self, slide: Slide) -> List[LayoutResult]:
        """
        Calculates geometry for a slide according to its template annotation.
        Returns a list of LayoutResults (includes continuation slides if overflow occurs).
        """
        annotation = self.get_annotation(slide.template_id)
        background = annotation.get("background", {}).get("asset", "bg_02.png")

        handler_map = {
            "01_cover_title_image": self._layout_01,
            "02_toc_image": self._layout_02,
            "03_section_opener": self._layout_03,
            "04_table_chart": self._layout_04,
            "05_insight_information": self._layout_05,
            "06_large_table": self._layout_06,
            "07_large_chart": self._layout_07,
            "08_multi_table_dashboard_2col": self._layout_08,
        }

        handler = handler_map.get(slide.template_id, self._layout_05)
        return handler(slide, annotation, background)

    def render_report_layout(self, report: Report) -> List[LayoutResult]:
        """
        Renders all slides in a canonical Report manifest sequentially into LayoutResults,
        maintaining proper slide indices and accommodating dynamic continuation slides.
        """
        all_results: List[LayoutResult] = []
        for slide in report.slides:
            slide.slide_index = len(all_results)
            slide_results = self.render_slide_layout(slide)
            for sr in slide_results:
                sr.slide_index = len(all_results)
                all_results.append(sr)
        return all_results

    @staticmethod
    def _extract_text_and_id(val: Any, default_text: str, default_id: str):
        if isinstance(val, TextBlock):
            return val.text, val.id
        if hasattr(val, "id") and hasattr(val, "text"):
            return str(val.text), str(val.id)
        if hasattr(val, "id"):
            return str(val), str(val.id)
        return str(val if val is not None else default_text), default_id

    # -------------------------------------------------------------
    # 01_cover_title_image
    # -------------------------------------------------------------
    def _layout_01(self, slide: Slide, annotation: Dict[str, Any], background: str) -> List[LayoutResult]:
        lr = LayoutResult(
            slide_id=slide.slide_id,
            slide_index=slide.slide_index,
            template_id="01_cover_title_image",
            background=background,
            title=slide.title
        )

        data = slide.data.regions
        title_text, title_id = self._extract_text_and_id(data.get("title"), getattr(slide, "title", "Mining UGV Market Report"), f"s{slide.slide_index+1}_title")
        subtitle_text, subtitle_id = self._extract_text_and_id(data.get("subtitle"), "Comprehensive Market & Technology Assessment", f"s{slide.slide_index+1}_subtitle")
        meta_text, meta_id = self._extract_text_and_id(data.get("metadata"), "Published: 2026 | Antigravity Strategic Research", f"s{slide.slide_index+1}_metadata")

        # Measure title
        t_reg = annotation["regions"]["title"]
        t_meas = fit_text_to_budget(title_text, t_reg["width"], t_reg["height"], 36, 28)
        lr.components.append(ComponentGeometry(
            component_id="title",
            component_type="text",
            x=t_reg["x"],
            y=t_reg["y"],
            width=t_reg["width"],
            height=t_meas["height"],
            data=title_text,
            font_size=t_meas["font_size"],
            style={"bold": True, "color": Theme.PRIMARY_NAVY, "align": "left"},
            provenance_id=title_id
        ))

        # Subtitle
        s_reg = annotation["regions"]["subtitle"]
        s_meas = fit_text_to_budget(subtitle_text, s_reg["width"], s_reg["height"], 18, 14)
        lr.components.append(ComponentGeometry(
            component_id="subtitle",
            component_type="text",
            x=s_reg["x"],
            y=s_reg["y"],
            width=s_reg["width"],
            height=s_meas["height"],
            data=subtitle_text,
            font_size=s_meas["font_size"],
            style={"bold": False, "color": Theme.TEXT_MUTED, "align": "left"},
            provenance_id=subtitle_id
        ))

        # Metadata
        m_reg = annotation["regions"]["metadata"]
        lr.components.append(ComponentGeometry(
            component_id="metadata",
            component_type="text",
            x=m_reg["x"],
            y=m_reg["y"],
            width=m_reg["width"],
            height=m_reg["height"],
            data=meta_text,
            font_size=15,
            style={"bold": False, "color": Theme.TEXT_LIGHT, "align": "left"},
            provenance_id=meta_id
        ))

        return [lr]

    # -------------------------------------------------------------
    # 02_toc_image
    # -------------------------------------------------------------
    def _layout_02(self, slide: Slide, annotation: Dict[str, Any], background: str) -> List[LayoutResult]:
        items_raw = slide.data.regions.get("items", slide.data.regions.get("toc_items", []))
        items: List[TOCItem] = []
        for idx, it in enumerate(items_raw):
            if isinstance(it, TOCItem):
                items.append(it)
            elif isinstance(it, dict):
                items.append(TOCItem(
                    id=it.get("id", f"toc_item_{idx+1}"),
                    number=str(it.get("number", f"{idx+1:02d}")),
                    title=str(it.get("title", f"Section {idx+1}"))
                ))
            else:
                items.append(TOCItem(
                    id=f"toc_item_{idx+1}",
                    number=f"{idx+1:02d}",
                    title=str(it)
                ))

        # Check capacity & overflow
        chunks = self.overflow_engine.resolve_toc_overflow(items, column_height=875.0, max_items_per_slide=18)
        results = []

        for chunk_idx, chunk_items in enumerate(chunks):
            is_cont = chunk_idx > 0
            slide_id = f"{slide.slide_id}_cont{chunk_idx}" if is_cont else slide.slide_id
            lr = LayoutResult(
                slide_id=slide_id,
                slide_index=slide.slide_index + chunk_idx,
                template_id="02_toc_image",
                background=background,
                title="TABLE OF CONTENTS" if not is_cont else "TABLE OF CONTENTS (CONTINUED)",
                overflow_status="CONTINUED" if is_cont else ("SPLIT" if len(chunks) > 1 else "FIT")
            )

            # Slide Title
            t_reg = annotation["regions"]["title"]
            lr.components.append(ComponentGeometry(
                component_id="title",
                component_type="text",
                x=t_reg["x"],
                y=t_reg["y"],
                width=t_reg["width"],
                height=t_reg["height"],
                data=lr.title,
                font_size=24,
                style={"bold": True, "color": Theme.PRIMARY_NAVY, "align": "center"}
            ))

            # Distribute items into left and right columns
            num_left = (len(chunk_items) + 1) // 2
            left_items = chunk_items[:num_left]
            right_items = chunk_items[num_left:]

            # Layout columns
            l_col = annotation["regions"]["left_column"]
            r_col = annotation["regions"]["right_column"]
            item_h = 60.0
            gap = max(12.0, min(26.0, (l_col["height"] - (num_left * item_h)) / max(1, num_left - 1)))

            # Left column items
            for i, it in enumerate(left_items):
                y_pos = l_col["y"] + i * (item_h + gap)
                lr.components.append(ComponentGeometry(
                    component_id=f"toc_{it.id}",
                    component_type="toc_item",
                    x=l_col["x"],
                    y=y_pos,
                    width=l_col["width"],
                    height=item_h,
                    data=it,
                    font_size=18,
                    provenance_id=it.id
                ))

            # Right column items
            for i, it in enumerate(right_items):
                y_pos = r_col["y"] + i * (item_h + gap)
                lr.components.append(ComponentGeometry(
                    component_id=f"toc_{it.id}",
                    component_type="toc_item",
                    x=r_col["x"],
                    y=y_pos,
                    width=r_col["width"],
                    height=item_h,
                    data=it,
                    font_size=18,
                    provenance_id=it.id
                ))

            results.append(lr)

        return results

    # -------------------------------------------------------------
    # 03_section_opener
    # -------------------------------------------------------------
    def _layout_03(self, slide: Slide, annotation: Dict[str, Any], background: str) -> List[LayoutResult]:
        sec_title, sec_title_id = self._extract_text_and_id(slide.data.regions.get("section_title"), slide.title or "Section Title", f"s{slide.slide_index+1}_section_title")
        items_raw = slide.data.regions.get("index_list", slide.data.regions.get("items", []))
        
        index_items: List[IndexItem] = []
        for idx, it in enumerate(items_raw):
            if isinstance(it, IndexItem):
                index_items.append(it)
            elif isinstance(it, dict):
                index_items.append(IndexItem(
                    id=it.get("id", f"idx_{idx+1}"),
                    number=str(it.get("number", f"{idx+1}")),
                    title=str(it.get("title", f"Subsection {idx+1}"))
                ))
            else:
                index_items.append(IndexItem(id=f"idx_{idx+1}", number=f"{idx+1}", title=str(it)))

        # Primary slide
        lr = LayoutResult(
            slide_id=slide.slide_id,
            slide_index=slide.slide_index,
            template_id="03_section_opener",
            background=background,
            title=sec_title
        )

        # Section title
        t_reg = annotation["regions"]["section_title"]
        t_meas = fit_text_to_budget(sec_title, t_reg["width"], 150.0, 34, 26)
        lr.components.append(ComponentGeometry(
            component_id="section_title",
            component_type="text",
            x=t_reg["x"],
            y=t_reg["y"],
            width=t_reg["width"],
            height=t_meas["height"],
            data=sec_title,
            font_size=t_meas["font_size"],
            style={"bold": True, "color": Theme.PRIMARY_NAVY, "align": "left"},
            provenance_id=sec_title_id
        ))

        # Index list
        idx_reg = annotation["regions"]["index_list"]
        primary_items, overflow_items = self.overflow_engine.resolve_index_overflow(index_items, idx_reg["height"], item_height=38.0)

        curr_y = max(float(idx_reg["y"]), t_reg["y"] + t_meas["height"] + 28.0)
        for it in primary_items:
            lr.components.append(ComponentGeometry(
                component_id=f"idx_{it.id}",
                component_type="index_item",
                x=idx_reg["x"],
                y=curr_y,
                width=idx_reg["width"],
                height=34.0,
                data=it,
                font_size=13,
                provenance_id=it.id
            ))
            curr_y += 38.0

        results = [lr]

        # If overflow items exist -> route to 05_insight_information (multi-column index list)
        if overflow_items:
            lr.overflow_status = "SPLIT"
            cont_lr = LayoutResult(
                slide_id=f"{slide.slide_id}_cont_05",
                slide_index=slide.slide_index + 1,
                template_id="05_insight_information",
                background="bg_02.png",
                title=f"{sec_title} (Continued Index)",
                overflow_status="CONTINUED"
            )

            # Distribute overflow items into 2 columns
            num_left = (len(overflow_items) + 1) // 2
            left_col_items = overflow_items[:num_left]
            right_col_items = overflow_items[num_left:]

            # Left column
            curr_y_l = 180.0
            for it in left_col_items:
                cont_lr.components.append(ComponentGeometry(
                    component_id=f"cont_idx_{it.id}",
                    component_type="index_item",
                    x=105.0,
                    y=curr_y_l,
                    width=750.0,
                    height=34.0,
                    data=it,
                    font_size=13,
                    provenance_id=it.id
                ))
                curr_y_l += 38.0

            # Right column
            curr_y_r = 180.0
            for it in right_col_items:
                cont_lr.components.append(ComponentGeometry(
                    component_id=f"cont_idx_{it.id}",
                    component_type="index_item",
                    x=945.0,
                    y=curr_y_r,
                    width=750.0,
                    height=34.0,
                    data=it,
                    font_size=13,
                    provenance_id=it.id
                ))
                curr_y_r += 38.0

            results.append(cont_lr)

        return results

    # -------------------------------------------------------------
    # 04_table_chart
    # -------------------------------------------------------------
    def _layout_04(self, slide: Slide, annotation: Dict[str, Any], background: str) -> List[LayoutResult]:
        lr = LayoutResult(
            slide_id=slide.slide_id,
            slide_index=slide.slide_index,
            template_id="04_table_chart",
            background=background,
            title=slide.title
        )

        data = slide.data.regions
        # Context note
        note_text, note_id = self._extract_text_and_id(data.get("context_note"), "Market Dynamics & Performance Overview", f"s{slide.slide_index+1}_context_note")
        c_reg = annotation["regions"]["context_note"]
        lr.components.append(ComponentGeometry(
            component_id="context_note",
            component_type="text",
            x=c_reg["x"],
            y=c_reg["y"],
            width=c_reg["width"],
            height=50.0,
            data=note_text,
            font_size=11,
            style={"bold": False, "color": Theme.TEXT_MUTED},
            provenance_id=note_id
        ))

        # Chart
        chart_data = data.get("chart")
        if isinstance(chart_data, ChartBlock):
            ch_reg = annotation["regions"]["chart"]
            ch_layout = ChartLayoutEngine.layout_chart(
                chart_type=chart_data.chart_type,
                categories=chart_data.categories,
                series_names=[s.name for s in chart_data.series],
                available_width=ch_reg["width"],
                available_height=ch_reg["height"],
                title=chart_data.title
            )
            lr.components.append(ComponentGeometry(
                component_id="chart",
                component_type="chart",
                x=ch_reg["x"],
                y=ch_reg["y"],
                width=ch_reg["width"],
                height=ch_reg["height"],
                data=(chart_data, ch_layout),
                provenance_id=chart_data.id
            ))

        # Right column: Section heading
        sec_heading, sh_id = self._extract_text_and_id(data.get("section_heading"), "Segment Analysis", f"s{slide.slide_index+1}_section_heading")
        sh_reg = annotation["regions"]["section_heading"]
        lr.components.append(ComponentGeometry(
            component_id="section_heading",
            component_type="text",
            x=sh_reg["x"],
            y=sh_reg["y"],
            width=sh_reg["width"],
            height=40.0,
            data=sec_heading,
            font_size=16,
            style={"bold": True, "color": Theme.PRIMARY_NAVY},
            provenance_id=sh_id
        ))

        # Narrative
        narrative, nar_id = self._extract_text_and_id(data.get("narrative"), "Detailed market metrics indicate sustained adoption across key sub-sectors.", f"s{slide.slide_index+1}_narrative")
        nar_reg = annotation["regions"]["narrative"]
        lr.components.append(ComponentGeometry(
            component_id="narrative",
            component_type="text",
            x=nar_reg["x"],
            y=nar_reg["y"],
            width=nar_reg["width"],
            height=60.0,
            data=narrative,
            font_size=11,
            style={"bold": False, "color": Theme.TEXT_DARK},
            provenance_id=nar_id
        ))

        # Table
        tbl_data = data.get("table")
        if isinstance(tbl_data, TableBlock):
            t_reg = annotation["regions"]["table"]
            rows_raw = [[c.value for c in r.cells] for r in tbl_data.rows]
            tbl_layout = TableLayoutEngine.layout_table(
                headers=tbl_data.headers,
                rows=rows_raw,
                available_width=t_reg["width"],
                available_height=t_reg["height"],
                preferred_font_size=10,
                minimum_font_size=8
            )
            lr.components.append(ComponentGeometry(
                component_id="table",
                component_type="table",
                x=t_reg["x"],
                y=t_reg["y"],
                width=t_reg["width"],
                height=tbl_layout.total_height,
                data=tbl_layout,
                provenance_id=tbl_data.id
            ))

        # Supporting insight
        insight_data = data.get("supporting_insight")
        if isinstance(insight_data, InsightBlock):
            ins_reg = annotation["regions"]["supporting_insight"]
            lr.components.append(ComponentGeometry(
                component_id="supporting_insight",
                component_type="insight",
                x=ins_reg["x"],
                y=ins_reg["y"],
                width=ins_reg["width"],
                height=ins_reg["height"],
                data=insight_data,
                provenance_id=insight_data.id
            ))

        return [lr]

    # -------------------------------------------------------------
    # 05_insight_information
    # -------------------------------------------------------------
    def _layout_05(self, slide: Slide, annotation: Dict[str, Any], background: str) -> List[LayoutResult]:
        t_text, t_id = self._extract_text_and_id(slide.data.regions.get("title"), slide.title or "Market Insights & Analysis", f"s{slide.slide_index+1}_title")
        tmpl_id = slide.template_id or "05_insight_information"
        lr = LayoutResult(
            slide_id=slide.slide_id,
            slide_index=slide.slide_index,
            template_id=tmpl_id,
            background=background,
            title=t_text
        )

        # Slide Title
        t_meas = fit_text_to_budget(lr.title, 1600.0, 90.0, 24, 20)
        lr.components.append(ComponentGeometry(
            component_id="slide_title",
            component_type="text",
            x=105.0,
            y=45.0,
            width=1600.0,
            height=t_meas["height"],
            data=lr.title,
            font_size=t_meas["font_size"],
            style={"bold": True, "color": Theme.PRIMARY_NAVY},
            provenance_id=t_id
        ))

        # Dynamic column start_y ensuring zero title overlap
        start_col_y = max(130.0, 45.0 + t_meas["height"] + 20.0)
        avail_col_h = 1010.0 - start_col_y

        # Collect blocks for left and right columns
        left_blocks = slide.data.left_column_blocks or []
        right_blocks = slide.data.right_column_blocks or []

        # If data is in regions dict
        if not left_blocks and not right_blocks:
            for k, v in slide.data.regions.items():
                if "left" in k.lower():
                    if isinstance(v, list):
                        left_blocks.extend(v)
                    else:
                        left_blocks.append(v)
                elif "right" in k.lower():
                    if isinstance(v, list):
                        right_blocks.extend(v)
                    else:
                        right_blocks.append(v)

        # Layout Left Column
        l_res = StackLayoutEngine.layout_vertical_stack(
            blocks=left_blocks,
            x=105.0,
            start_y=start_col_y,
            width=790.0,
            available_height=avail_col_h
        )
        for b in l_res.blocks:
            lr.components.append(ComponentGeometry(
                component_id=b.block_id,
                component_type=b.block_type,
                x=b.x,
                y=b.y,
                width=b.width,
                height=b.height,
                data=b.data,
                font_size=b.font_size,
                provenance_id=b.block_id
            ))

        # Layout Right Column
        r_res = StackLayoutEngine.layout_vertical_stack(
            blocks=right_blocks,
            x=945.0,
            start_y=start_col_y,
            width=790.0,
            available_height=avail_col_h
        )
        for b in r_res.blocks:
            lr.components.append(ComponentGeometry(
                component_id=b.block_id,
                component_type=b.block_type,
                x=b.x,
                y=b.y,
                width=b.width,
                height=b.height,
                data=b.data,
                font_size=b.font_size,
                provenance_id=b.block_id
            ))

        results = [lr]

        # Check overflow blocks -> continuation slide
        if l_res.overflow_blocks or r_res.overflow_blocks:
            lr.overflow_status = "SPLIT"
            cont_slide = Slide(
                slide_id=f"{slide.slide_id}_cont",
                template_id=tmpl_id,
                slide_index=slide.slide_index + 1,
                title=f"{lr.title} (Continued)",
                data=SlideData(
                    left_column_blocks=l_res.overflow_blocks,
                    right_column_blocks=r_res.overflow_blocks
                )
            )
            results.extend(self._layout_05(cont_slide, annotation, background))

        return results

    # -------------------------------------------------------------
    # 06_large_table
    # -------------------------------------------------------------
    def _layout_06(self, slide: Slide, annotation: Dict[str, Any], background: str) -> List[LayoutResult]:
        tbl_data = slide.data.regions.get("table", slide.data.regions.get("data"))
        if not isinstance(tbl_data, TableBlock):
            # Fallback if raw dict
            headers = slide.data.regions.get("headers", ["Col 1", "Col 2"])
            rows = slide.data.regions.get("rows", [["A", "B"]])
            tbl_data = TableBlock(id=f"{slide.slide_id}_tbl", headers=headers, rows=[])

        title_text, title_id = self._extract_text_and_id(slide.data.regions.get("table_title"), slide.title or "Comprehensive Data Table", f"s{slide.slide_index+1}_table_title")
        t_reg = annotation["regions"]["table"]

        rows_raw = [[c.value for c in r.cells] for r in tbl_data.rows] if tbl_data.rows else slide.data.regions.get("rows", [])
        tbl_layout = TableLayoutEngine.layout_table(
            headers=tbl_data.headers,
            rows=rows_raw,
            available_width=t_reg["width"],
            available_height=t_reg["height"],
            preferred_font_size=10,
            minimum_font_size=8,
            min_row_height=24.0
        )

        results = []
        curr_layout = tbl_layout
        part = 1

        while curr_layout:
            is_cont = (part > 1)
            s_title = title_text if not is_cont else f"{title_text} (Part {part})"
            s_id = slide.slide_id if not is_cont else f"{slide.slide_id}_part{part}"

            lr = LayoutResult(
                slide_id=s_id,
                slide_index=slide.slide_index + part - 1,
                template_id="06_large_table",
                background=background,
                title=s_title,
                overflow_status="CONTINUED" if is_cont else ("SPLIT" if curr_layout.continuation_table else "FIT")
            )

            # Table Title
            t_meas = fit_text_to_budget(s_title, 1700.0, 70.0, 22, 18)
            lr.components.append(ComponentGeometry(
                component_id="table_title",
                component_type="text",
                x=105.0,
                y=45.0,
                width=1700.0,
                height=t_meas["height"],
                data=s_title,
                font_size=t_meas["font_size"],
                style={"bold": True, "color": Theme.PRIMARY_NAVY},
                provenance_id=title_id
            ))

            # Table
            tbl_y = max(float(t_reg["y"]), 45.0 + t_meas["height"] + 15.0)
            lr.components.append(ComponentGeometry(
                component_id="table",
                component_type="table",
                x=t_reg["x"],
                y=tbl_y,
                width=t_reg["width"],
                height=curr_layout.total_height,
                data=curr_layout,
                provenance_id=tbl_data.id
            ))

            results.append(lr)
            curr_layout = curr_layout.continuation_table
            part += 1

        return results

    # -------------------------------------------------------------
    # 07_large_chart
    # -------------------------------------------------------------
    def _layout_07(self, slide: Slide, annotation: Dict[str, Any], background: str) -> List[LayoutResult]:
        chart_data = slide.data.regions.get("chart")
        title_text, title_id = self._extract_text_and_id(slide.data.regions.get("chart_title"), slide.title or "Dominant Market Trends", f"s{slide.slide_index+1}_chart_title")

        lr = LayoutResult(
            slide_id=slide.slide_id,
            slide_index=slide.slide_index,
            template_id="07_large_chart",
            background=background,
            title=title_text
        )

        # Title
        lr.components.append(ComponentGeometry(
            component_id="chart_title",
            component_type="text",
            x=105.0,
            y=50.0,
            width=1700.0,
            height=50.0,
            data=title_text,
            font_size=24,
            style={"bold": True, "color": Theme.PRIMARY_NAVY},
            provenance_id=title_id
        ))

        # Chart
        ch_reg = annotation["regions"]["chart"]
        if isinstance(chart_data, ChartBlock):
            ch_layout = ChartLayoutEngine.layout_chart(
                chart_type=chart_data.chart_type,
                categories=chart_data.categories,
                series_names=[s.name for s in chart_data.series],
                available_width=ch_reg["width"],
                available_height=ch_reg["height"],
                title=chart_data.title
            )
            lr.components.append(ComponentGeometry(
                component_id="chart",
                component_type="chart",
                x=ch_reg["x"],
                y=ch_reg["y"],
                width=ch_reg["width"],
                height=ch_reg["height"],
                data=(chart_data, ch_layout),
                provenance_id=chart_data.id
            ))

        return [lr]

    # -------------------------------------------------------------
    # 08_multi_table_dashboard_2col
    # -------------------------------------------------------------
    def _layout_08(self, slide: Slide, annotation: Dict[str, Any], background: str) -> List[LayoutResult]:
        # Multi-table dashboard uses 2-column dynamic stacking (similar to 05, with tables)
        return self._layout_05(slide, annotation, background)
