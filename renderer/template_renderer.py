"""
Template Renderer
Executes layout algorithms for all 8 fundamental templates.
Emits decoupled LayoutResult objects and creates continuation slides when content overflows.
"""

import json
import os
from typing import List, Dict, Any, Optional
from layout.layout_result import LayoutResult, RegionGeometry, ComponentGeometry
from layout.text_measurement import measure_multiline_text, measure_single_line, fit_text_to_budget
from layout.table_layout import TableLayoutEngine, TableLayoutResult
from layout.chart_layout import ChartLayoutEngine, ChartLayoutResult
from layout.stack_layout import StackLayoutEngine
from layout.overflow_engine import OverflowEngine
from models.report_model import Report, Slide, SlideData, TextBlock, BulletListBlock, TableBlock, ChartBlock, InsightBlock, TOCItem, IndexItem, ImageBlock
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
            elif isinstance(it, TextBlock):
                items.append(TOCItem(
                    id=it.id,
                    number=str(getattr(it, "number", f"{idx+1:02d}")),
                    title=it.text
                ))
            elif isinstance(it, dict):
                items.append(TOCItem(
                    id=it.get("id", f"toc_item_{idx+1:02d}"),
                    number=str(it.get("number", f"{idx+1:02d}")),
                    title=str(it.get("title", f"Section {idx+1}"))
                ))
            else:
                items.append(TOCItem(
                    id=f"toc_item_{idx+1:02d}",
                    number=f"{idx+1:02d}",
                    title=str(it)
                ))

        # Check capacity & overflow
        chunks = self.overflow_engine.resolve_toc_overflow(items, column_height=875.0, max_items_per_slide=18)
        results = []

        title_text, title_id = self._extract_text_and_id(
            slide.data.regions.get("title"), "TABLE OF CONTENTS", f"s{slide.slide_index+1}_title"
        )

        for chunk_idx, chunk_items in enumerate(chunks):
            is_cont = chunk_idx > 0
            slide_id = f"{slide.slide_id}_cont{chunk_idx}" if is_cont else slide.slide_id
            lr = LayoutResult(
                slide_id=slide_id,
                slide_index=slide.slide_index + chunk_idx,
                template_id="02_toc_image",
                background=background,
                title=title_text if not is_cont else f"{title_text} (CONTINUED)",
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
                style={"bold": True, "color": Theme.PRIMARY_NAVY, "align": "center"},
                provenance_id=title_id if not is_cont else f"{title_id}_cont{chunk_idx}"
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
            elif isinstance(it, TextBlock):
                index_items.append(IndexItem(
                    id=it.id,
                    number=str(getattr(it, "number", f"{idx+1}")),
                    title=it.text
                ))
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
        t_meas = fit_text_to_budget(sec_title, t_reg["width"] * 0.90, 150.0, 32, 24)
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

        curr_y = max(float(idx_reg["y"]), t_reg["y"] + t_meas["height"] + 24.0)
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

        # If overflow items exist -> route to 05_insight_information (multi-column index list on bg_02)
        if overflow_items:
            lr.overflow_status = "SPLIT"
            chunk_size = 24  # Max 12 items per column on continuation slide
            num_chunks = (len(overflow_items) + chunk_size - 1) // chunk_size

            for chunk_idx in range(num_chunks):
                chunk = overflow_items[chunk_idx * chunk_size : (chunk_idx + 1) * chunk_size]
                part_title = f"{sec_title} (Continued Index)" if num_chunks == 1 else f"{sec_title} (Continued Index - Part {chunk_idx + 1})"
                cont_lr = LayoutResult(
                    slide_id=f"{slide.slide_id}_cont_05_{chunk_idx + 1}",
                    slide_index=slide.slide_index + chunk_idx + 1,
                    template_id="05_insight_information",
                    background="bg_02.png",
                    title=part_title,
                    overflow_status="CONTINUED"
                )

                # Slide Title
                t_meas = fit_text_to_budget(part_title, 1600.0, 70.0, 22, 16)
                cont_lr.components.append(ComponentGeometry(
                    component_id="slide_title",
                    component_type="text",
                    x=105.0,
                    y=45.0,
                    width=1600.0,
                    height=t_meas["height"],
                    data=part_title,
                    font_size=t_meas["font_size"],
                    style={"bold": True, "color": Theme.PRIMARY_NAVY},
                    provenance_id=f"{sec_title_id}_cont_title_{chunk_idx + 1}"
                ))

                # Distribute chunk items into 2 columns
                num_left = (len(chunk) + 1) // 2
                left_col_items = chunk[:num_left]
                right_col_items = chunk[num_left:]
                start_y = max(130.0, 45.0 + t_meas["height"] + 20.0)

                # Left column
                curr_y_l = start_y
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
                curr_y_r = start_y
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
        # Context note (left column, above chart)
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

        # Chart (left column)
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

        # ── Right column: measure heading FIRST, then cascade positions ──
        sec_heading, sh_id = self._extract_text_and_id(data.get("section_heading", data.get("heading")), "Segment Analysis", f"s{slide.slide_index+1}_section_heading")
        sh_reg = annotation["regions"]["section_heading"]
        heading_font = 22  # per project spec: headings = 22pt
        heading_width = sh_reg["width"]

        # Safe text width inside text box (accounting for margins, kerning, and padding)
        safe_heading_width = heading_width - 50.0
        chosen_heading_font = heading_font

        # Step down font size from 22 down to 13 if single-line width exceeds safe width
        for s in range(heading_font, 12, -1):
            sw, _ = measure_single_line(sec_heading, "arial", s)
            if sw <= safe_heading_width:
                chosen_heading_font = s
                break
        else:
            chosen_heading_font = 13

        # Check line count at chosen font
        meas = measure_multiline_text(sec_heading, "arial", chosen_heading_font, safe_heading_width, line_spacing=1.15)
        line_count = max(1, len(meas["lines"]))
        line_h = float(chosen_heading_font) * 2.0 * 1.2
        heading_actual_h = max(line_count * line_h + 8.0, 36.0)

        # Spacing between heading bottom and narrative top
        spacing = annotation.get("spacing", {})
        heading_to_narrative_gap = max(12, spacing.get("heading_to_narrative", 8))
        narrative_to_table_gap = spacing.get("narrative_to_table", 15)
        table_to_insight_gap = spacing.get("table_to_insight", 20)

        heading_y = sh_reg["y"]
        lr.components.append(ComponentGeometry(
            component_id="section_heading",
            component_type="text",
            x=sh_reg["x"],
            y=heading_y,
            width=heading_width,
            height=heading_actual_h,
            data=sec_heading,
            font_size=chosen_heading_font,
            style={"bold": True, "color": Theme.PRIMARY_NAVY},
            provenance_id=sh_id
        ))

        # ── Narrative: position dynamically below heading ──
        narrative, nar_id = self._extract_text_and_id(data.get("narrative"), "Detailed market metrics indicate sustained adoption across key sub-sectors.", f"s{slide.slide_index+1}_narrative")
        nar_reg = annotation["regions"]["narrative"]
        narrative_y = heading_y + heading_actual_h + heading_to_narrative_gap
        # Measure actual narrative height: take limited space rather than maximum space
        nar_meas = measure_multiline_text(narrative, "arial", 10, nar_reg["width"] - 20.0, line_spacing=1.15)
        nar_line_count = max(1, len(nar_meas["lines"]))
        narrative_height = max(24.0, min(float(nar_reg["height"]), nar_line_count * 24.0 + 8.0))
        lr.components.append(ComponentGeometry(
            component_id="narrative",
            component_type="text",
            x=nar_reg["x"],
            y=narrative_y,
            width=nar_reg["width"],
            height=narrative_height,
            data=narrative,
            font_size=10,  # per project spec: content = 10pt
            style={"bold": False, "color": Theme.TEXT_DARK},
            provenance_id=nar_id
        ))

        # ── Table: position dynamically below narrative ──
        tbl_data = data.get("table")
        table_y = narrative_y + narrative_height + narrative_to_table_gap
        table_bottom = table_y

        # Check insight existence and reserve
        insight_data = data.get("supporting_insight", data.get("insight"))
        has_insight = isinstance(insight_data, InsightBlock) or (isinstance(insight_data, dict) and bool(insight_data))
        ins_reg = annotation["regions"].get("supporting_insight", {})
        insight_h = float(ins_reg.get("height", 130.0)) if has_insight else 0.0
        insight_reserve = (insight_h + table_to_insight_gap) if has_insight else 0.0

        safe_reg = annotation.get("safe_area", {})
        canvas_bottom = float(safe_reg.get("y", 48)) + float(safe_reg.get("height", 984))
        if canvas_bottom <= 0:
            canvas_bottom = 1032.0

        table_height_budget = max(100.0, canvas_bottom - table_y - insight_reserve)

        if isinstance(tbl_data, TableBlock) or (isinstance(tbl_data, dict) and "headers" in tbl_data):
            t_reg = annotation["regions"]["table"]
            if isinstance(tbl_data, TableBlock):
                headers = tbl_data.headers
                rows_raw = [[c.value for c in r.cells] for r in tbl_data.rows]
                tbl_prov_id = tbl_data.id
            else:
                headers = tbl_data.get("headers", [])
                rows_in = tbl_data.get("rows", [])
                rows_raw = []
                for r in rows_in:
                    if isinstance(r, dict):
                        cells = r.get("cells", [])
                        rows_raw.append([c.get("value", "") if isinstance(c, dict) else str(c) for c in cells])
                    elif isinstance(r, list):
                        rows_raw.append([str(c) for c in r])
                tbl_prov_id = tbl_data.get("id", f"s{slide.slide_index+1}_table")

            # Determine table font size based on row count and budget
            num_rows = len(rows_raw)
            if num_rows >= 8:
                pref_font = 8
                min_font = 7
                min_row_h = 28.0
            elif num_rows >= 6:
                pref_font = 9
                min_font = 7
                min_row_h = 30.0
            else:
                pref_font = 10
                min_font = 8
                min_row_h = 32.0

            tbl_layout = TableLayoutEngine.layout_table(
                headers=headers,
                rows=rows_raw,
                available_width=t_reg["width"],
                available_height=table_height_budget,
                preferred_font_size=pref_font,
                minimum_font_size=min_font,
                min_row_height=min_row_h
            )
            lr.components.append(ComponentGeometry(
                component_id="table",
                component_type="table",
                x=t_reg["x"],
                y=table_y,
                width=t_reg["width"],
                height=tbl_layout.total_height,
                data=tbl_layout,
                provenance_id=tbl_prov_id
            ))
            table_bottom = table_y + tbl_layout.total_height

        # ── Supporting insight: position dynamically below table ──
        if has_insight:
            insight_y = table_bottom + table_to_insight_gap
            actual_insight_h = min(insight_h, max(50.0, canvas_bottom - insight_y))
            # Only add insight if it fits within safe area
            if insight_y + 40.0 <= canvas_bottom:
                if isinstance(insight_data, dict):
                    insight_obj = InsightBlock(
                        id=insight_data.get("id", f"s{slide.slide_index+1}_ins"),
                        title=insight_data.get("title", "KEY INSIGHT"),
                        body=insight_data.get("body", "")
                    )
                else:
                    insight_obj = insight_data

                lr.components.append(ComponentGeometry(
                    component_id="supporting_insight",
                    component_type="insight",
                    x=ins_reg.get("x", 960),
                    y=insight_y,
                    width=ins_reg.get("width", 730),
                    height=actual_insight_h,
                    data=insight_obj,
                    provenance_id=getattr(insight_obj, "id", None)
                ))

        return [lr]

    # -------------------------------------------------------------
    # 05_insight_information
    # -------------------------------------------------------------
    def _layout_05(self, slide: Slide, annotation: Dict[str, Any], background: str, depth: int = 0) -> List[LayoutResult]:
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
        if (l_res.overflow_blocks or r_res.overflow_blocks) and depth < 5:
            lr.overflow_status = "SPLIT"
            cont_slide = Slide(
                slide_id=f"{slide.slide_id}_cont{depth+1}",
                template_id=tmpl_id,
                slide_index=slide.slide_index + 1,
                title=f"{lr.title} (Continued)",
                data=SlideData(
                    left_column_blocks=l_res.overflow_blocks,
                    right_column_blocks=r_res.overflow_blocks
                )
            )
            results.extend(self._layout_05(cont_slide, annotation, background, depth=depth + 1))

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

        title_text, title_id = self._extract_text_and_id(slide.data.regions.get("table_title", slide.data.regions.get("title")), slide.title or "Comprehensive Data Table", f"s{slide.slide_index+1}_table_title")
        t_reg = annotation["regions"]["table"]

        t_meas = fit_text_to_budget(title_text, 1700.0, 70.0, 22, 18)
        tbl_y = max(float(t_reg["y"]), 45.0 + t_meas["height"] + 15.0)
        avail_h = 990.0 - tbl_y

        rows_raw = [[c.value for c in r.cells] for r in tbl_data.rows] if tbl_data.rows else slide.data.regions.get("rows", [])
        tbl_layout = TableLayoutEngine.layout_table(
            headers=tbl_data.headers,
            rows=rows_raw,
            available_width=t_reg["width"],
            available_height=avail_h,
            preferred_font_size=10,
            minimum_font_size=8,
            min_row_height=33.0
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
        title_text, title_id = self._extract_text_and_id(slide.data.regions.get("chart_title", slide.data.regions.get("title")), slide.title or "Dominant Market Trends", f"s{slide.slide_index+1}_chart_title")

        lr = LayoutResult(
            slide_id=slide.slide_id,
            slide_index=slide.slide_index,
            template_id="07_large_chart",
            background=background,
            title=title_text
        )

        # Title: step down font size if needed to fit single line
        t_meas = fit_text_to_budget(title_text, 1700.0, 50.0, 22, 14)
        t_h = max(t_meas["height"], 40.0)
        lr.components.append(ComponentGeometry(
            component_id="chart_title",
            component_type="text",
            x=105.0,
            y=50.0,
            width=1700.0,
            height=t_h,
            data=title_text,
            font_size=t_meas["font_size"],
            style={"bold": True, "color": Theme.PRIMARY_NAVY},
            provenance_id=title_id
        ))

        # Chart: position dynamically below title
        ch_reg = annotation["regions"]["chart"]
        chart_y = max(float(ch_reg["y"]), 50.0 + t_h + 20.0)
        chart_h = min(float(ch_reg["height"]), 1020.0 - chart_y)
        if isinstance(chart_data, ChartBlock):
            ch_layout = ChartLayoutEngine.layout_chart(
                chart_type=chart_data.chart_type,
                categories=chart_data.categories,
                series_names=[s.name for s in chart_data.series],
                available_width=ch_reg["width"],
                available_height=chart_h,
                title=chart_data.title
            )
            lr.components.append(ComponentGeometry(
                component_id="chart",
                component_type="chart",
                x=ch_reg["x"],
                y=chart_y,
                width=ch_reg["width"],
                height=chart_h,
                data=(chart_data, ch_layout),
                provenance_id=chart_data.id
            ))

        return [lr]

    # -------------------------------------------------------------
    # 08_multi_table_dashboard_2col
    # -------------------------------------------------------------
    def _layout_08(self, slide: Slide, annotation: Dict[str, Any], background: str) -> List[LayoutResult]:
        # Multi-table dashboard: check capacity before deciding layout
        t_text, t_id = self._extract_text_and_id(slide.data.regions.get("title"), slide.title or "Multi-Table Dashboard", f"s{slide.slide_index+1}_title")
        t_meas = fit_text_to_budget(t_text, 1600.0, 90.0, 22, 16)
        start_col_y = max(130.0, 45.0 + t_meas["height"] + 20.0)
        avail_col_h = 1010.0 - start_col_y

        left_blocks = slide.data.left_column_blocks or []
        right_blocks = slide.data.right_column_blocks or []
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

        # Simulation layout: check if both columns comfortably fit
        l_res = StackLayoutEngine.layout_vertical_stack(left_blocks, x=105.0, start_y=start_col_y, width=790.0, available_height=avail_col_h)
        r_res = StackLayoutEngine.layout_vertical_stack(right_blocks, x=945.0, start_y=start_col_y, width=790.0, available_height=avail_col_h)

        # If either column overflows the space budget: show ONE table at a time on separate slides
        if l_res.overflow_blocks or r_res.overflow_blocks:
            results = []
            cols = [("Left", left_blocks, 1), ("Right", right_blocks, 2)]
            for col_name, blocks, col_idx in cols:
                if not blocks:
                    continue
                t_title = f"{t_text} - Part {col_idx}"
                tbl_block = None
                for b in blocks:
                    if isinstance(b, TableBlock) or (isinstance(b, dict) and (b.get("type") == "table" or "headers" in b)):
                        tbl_block = b
                    elif isinstance(b, TextBlock) and b.role == "heading":
                        t_title = b.text
                    elif isinstance(b, dict) and b.get("role") == "heading":
                        t_title = b.get("text", t_title)

                if tbl_block:
                    sub_slide = Slide(
                        slide_id=f"{slide.slide_id}_tbl_{col_idx}",
                        template_id="06_large_table",
                        slide_index=slide.slide_index + len(results),
                        title=t_title,
                        data=SlideData(regions={
                            "title": t_title,
                            "table": tbl_block,
                            "table_title": t_title
                        })
                    )
                    ann_06 = self.get_annotation("06_large_table")
                    results.extend(self._layout_06(sub_slide, ann_06, background))
                else:
                    sub_slide = Slide(
                        slide_id=f"{slide.slide_id}_info_{col_idx}",
                        template_id="05_insight_information",
                        slide_index=slide.slide_index + len(results),
                        title=t_title,
                        data=SlideData(regions={"left_column": blocks, "title": t_title})
                    )
                    ann_05 = self.get_annotation("05_insight_information")
                    results.extend(self._layout_05(sub_slide, ann_05, background))
            return results

        # If both fit cleanly on one slide, render standard 2-column layout
        return self._layout_05(slide, annotation, background)
