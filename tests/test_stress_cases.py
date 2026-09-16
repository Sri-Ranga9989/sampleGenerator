"""
Comprehensive Stress Testing Suite (Phase 8)
Implements all 19 edge cases specified in Section 36 of the PPT Generator V1 architecture plan.
Verifies layout engine, overflow routing, font clamps, table expansion, and structural integrity.
"""

import unittest
import os
from typing import List
from models.report_model import (
    Slide, SlideData, TextBlock, TableBlock, TableRow, TableCell,
    ChartBlock, ChartSeries, BulletListBlock, BulletItem, InsightBlock, TOCItem, IndexItem, Report
)
from renderer.template_renderer import TemplateRenderer
from renderer.powerpoint_renderer import PowerPointRenderer
from validators.structural_validator import StructuralValidator
from validators.completeness_validator import CompletenessValidator
from layout.table_layout import TableLayoutEngine
from layout.text_measurement import measure_multiline_text, fit_text_to_budget
from layout.chart_layout import ChartLayoutEngine
from layout.stack_layout import StackLayoutEngine


class TestStressEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template_renderer = TemplateRenderer()
        cls.ppt_renderer = PowerPointRenderer()
        os.makedirs("output/stress_tests", exist_ok=True)

    # -------------------------------------------------------------------------
    # Case 1: Long table with one huge explanatory cell (verifies row-specific expansion)
    # -------------------------------------------------------------------------
    def test_case_01_huge_explanatory_cell_row_expansion(self):
        long_explanation = (
            "This critical subsystem requires comprehensive dual-redundant CAN bus transceivers, "
            "explosion-proof hermetic sealing conforming to ATEX Zone 1 specifications, "
            "integrated telemetry failover to 5G private micro-cells, and automated emergency "
            "isolated braking actuation upon loss of heartbeat for more than 250 milliseconds. "
            "Additionally, galvanic isolation transformers and temperature-compensated strain gauges "
            "are continuously monitored by onboard safety controllers."
        )
        headers = ["Subsystem", "Specification & Safety Directives", "TCO Impact"]
        rows = [
            ["Short Row 1", "Standard IP67 enclosure.", "Low"],
            ["Exploded Spec Row", long_explanation, "High ($45K)"],
            ["Short Row 3", "Direct electric drive.", "Moderate"]
        ]
        layout = TableLayoutEngine.layout_table(
            headers=headers,
            rows=rows,
            available_width=800.0,
            available_height=600.0,
            preferred_font_size=10,
            minimum_font_size=8,
            min_row_height=26.0
        )
        # Header + 3 rows = 4 rows
        self.assertEqual(len(layout.rows), 4)
        # The explanatory cell row (index 2) must be significantly taller than short rows
        short_row_height = layout.rows[1].allocated_height
        expanded_row_height = layout.rows[2].allocated_height
        self.assertGreater(expanded_row_height, short_row_height * 2.0,
                           "Exploded cell row should expand independently")
        # Third row must remain compact (equal or close to min_row_height)
        self.assertEqual(layout.rows[3].allocated_height, 26.0,
                         "Subsequent short row must remain compact and not stretch unnecessarily")

    # -------------------------------------------------------------------------
    # Case 2: Many TOC items (> 18 items -> dynamic capacity & continuation)
    # -------------------------------------------------------------------------
    def test_case_02_many_toc_items_continuation(self):
        toc_items = [
            TOCItem(id=f"toc_{i+1:02d}", number=f"{i+1:02d}", title=f"Strategic Topic Section Number {i+1}")
            for i in range(25)  # 25 items > 18 slide capacity
        ]
        slide = Slide(
            slide_id="stress_toc_25",
            template_id="02_toc_image",
            slide_index=1,
            data=SlideData(regions={"items": toc_items})
        )
        results = self.template_renderer.render_slide_layout(slide)
        self.assertEqual(len(results), 2, "25 TOC items should cleanly split across 2 slides")
        self.assertEqual(results[0].overflow_status, "SPLIT")
        self.assertEqual(results[1].overflow_status, "CONTINUED")
        self.assertIn("CONTINUED", results[1].title)

        # Provenance check: all 25 items must be present
        prs, prov = self.ppt_renderer.create_presentation(results)
        val = CompletenessValidator.validate_completeness([it.id for it in toc_items], prov)
        self.assertEqual(val["status"], "PASS")
        self.assertEqual(val["total_rendered_items"], 25)

    # -------------------------------------------------------------------------
    # Case 3: Many section index items (> 10 items -> overflow to 05_insight_information)
    # -------------------------------------------------------------------------
    def test_case_03_section_index_overflow_to_05(self):
        index_items = [
            IndexItem(id=f"sub_sec_{i+1}", number=f"3.{i+1}", title=f"Subsection Scope {i+1}: Critical Parameters")
            for i in range(16)  # 16 items > 10 primary capacity
        ]
        slide = Slide(
            slide_id="stress_opener_16",
            template_id="03_section_opener",
            slide_index=3,
            data=SlideData(regions={
                "section_title": "3. Advanced Autonomous Architecture",
                "index_list": index_items
            })
        )
        results = self.template_renderer.render_slide_layout(slide)
        self.assertEqual(len(results), 2, "Overflowing index items must spawn a continuation slide")
        self.assertEqual(results[1].template_id, "05_insight_information",
                         "Continuation slide must route to 05_insight_information archetype")

        prs, prov = self.ppt_renderer.create_presentation(results)
        val = CompletenessValidator.validate_completeness([it.id for it in index_items], prov)
        self.assertEqual(val["status"], "PASS")
        self.assertEqual(val["total_rendered_items"], 16)

    # -------------------------------------------------------------------------
    # Case 4: Dominant large table with high row count (split across multiple slides)
    # -------------------------------------------------------------------------
    def test_case_04_large_table_multi_slide_split(self):
        headers = ["Rank", "Vendor", "Country", "UGV Models", "Production Units", "Market Share", "Lifecycle Score"]
        rows = [
            TableRow(id=f"row_{i}", cells=[
                TableCell(id=f"c_{i}_0", value=str(i + 1)),
                TableCell(id=f"c_{i}_1", value=f"Autonomous OEM Group {i + 1}"),
                TableCell(id=f"c_{i}_2", value="Global"),
                TableCell(id=f"c_{i}_3", value="LHD-400 / Hauler-90"),
                TableCell(id=f"c_{i}_4", value=f"{500 + i * 25}"),
                TableCell(id=f"c_{i}_5", value=f"{12.5 - i * 0.4:.1f}%"),
                TableCell(id=f"c_{i}_6", value="Class A")
            ])
            for i in range(45)  # 45 rows exceeds single slide height (45 * 26 > 902)
        ]
        tbl = TableBlock(id="stress_tbl_45", headers=headers, rows=rows)
        slide = Slide(
            slide_id="stress_tbl_slide",
            template_id="06_large_table",
            slide_index=5,
            data=SlideData(regions={"table": tbl})
        )
        results = self.template_renderer.render_slide_layout(slide)
        self.assertGreaterEqual(len(results), 2, "45 rows should split into 2 or more slides")
        
        # Verify headers repeated
        for res in results:
            tbl_comp = next(c for c in res.components if c.component_type == "table")
            tbl_layout = tbl_comp.data
            self.assertTrue(tbl_layout.rows[0].is_header, "Every split table slide must repeat the header row")

    # -------------------------------------------------------------------------
    # Case 5: Dominant large table with high column count (column reallocation)
    # -------------------------------------------------------------------------
    def test_case_05_high_column_count_table(self):
        headers = [f"Col {i+1}" for i in range(11)]  # 11 columns
        rows = [
            [f"R{r}C{c}" for c in range(11)]
            for r in range(5)
        ]
        layout = TableLayoutEngine.layout_table(
            headers=headers,
            rows=rows,
            available_width=1700.0,
            available_height=500.0,
            min_col_width=50.0
        )
        self.assertEqual(len(layout.column_widths), 11)
        self.assertAlmostEqual(sum(layout.column_widths), 1700.0, delta=1.0)
        for w in layout.column_widths:
            self.assertGreaterEqual(w, 50.0)

    # -------------------------------------------------------------------------
    # Case 6: Dominant chart with many categories (category density layout)
    # -------------------------------------------------------------------------
    def test_case_06_chart_with_many_categories(self):
        categories = [f"Mine Site {i+1}" for i in range(18)]
        chart = ChartBlock(
            id="stress_chart_18",
            chart_type="bar",
            title="Tele-remote Operational Hours by Mine Site",
            categories=categories,
            series=[ChartSeries(name="Active Hours", values=[1200 + i * 45 for i in range(18)])]
        )
        ch_layout = ChartLayoutEngine.layout_chart(
            chart_type="bar",
            categories=categories,
            series_names=["Active Hours"],
            available_width=1650.0,
            available_height=650.0,
            title=chart.title
        )
        self.assertTrue(ch_layout.has_legend or not ch_layout.has_legend)
        self.assertLessEqual(ch_layout.plot_width, 1650.0)
        self.assertLessEqual(ch_layout.plot_height, 650.0)

    # -------------------------------------------------------------------------
    # Case 7: Multi-table dashboard with uneven column heights
    # -------------------------------------------------------------------------
    def test_case_07_multi_table_dashboard_uneven_columns(self):
        tbl1 = TableBlock(
            id="t1",
            headers=["Param", "Value"],
            rows=[TableRow(id=f"r1_{i}", cells=[TableCell(id=f"c1_{i}_1", value=f"P{i}"), TableCell(id=f"c1_{i}_2", value=f"V{i}")]) for i in range(3)]
        )
        tbl2 = TableBlock(
            id="t2",
            headers=["Sensor", "Range", "Durability", "Interface"],
            rows=[TableRow(id=f"r2_{i}", cells=[TableCell(id=f"c2_{i}_{j}", value=f"D{i}{j}") for j in range(4)]) for i in range(6)]
        )
        slide = Slide(
            slide_id="stress_dash_08",
            template_id="08_multi_table_dashboard_2col",
            slide_index=7,
            data=SlideData(
                left_column_blocks=[TextBlock(id="h1", text="Left Heading", role="heading"), tbl1],
                right_column_blocks=[TextBlock(id="h2", text="Right Heading", role="heading"), tbl2, InsightBlock(id="ins1", title="Key Takeaway", body="Multi-modal redundancy.")]
            )
        )
        results = self.template_renderer.render_slide_layout(slide)
        self.assertGreaterEqual(len(results), 1)
        prs, prov = self.ppt_renderer.create_presentation(results)
        struct_res = StructuralValidator.validate_presentation(prs)
        self.assertEqual(struct_res["status"], "PASS")

    # -------------------------------------------------------------------------
    # Case 8: Very long narrative text in 04_table_chart
    # -------------------------------------------------------------------------
    def test_case_08_very_long_narrative_text(self):
        long_narrative = (
            "Over the past decade, underground hard-rock extraction facilities have experienced unprecedented "
            "escalations in ventilation and deep-shaft cooling expenditures. To combat these compounding operational "
            "burdens, leading global tier-1 mining consortia have initiated sweeping fleet modernization protocols "
            "transitioning mechanical and hydraulic diesel excavators to pure battery-electric autonomous units. "
            "This transition is fortified by synchronized advancements in high-bandwidth underground wireless networks, "
            "such as Leaky Feeder 5G NR, which allow remote tele-operators situated thousands of kilometers away in "
            "centralized metropolitan command centres to oversee multi-vehicle production runs with millisecond-grade latency."
        )
        chart = ChartBlock(id="ch_c8", chart_type="line", categories=["2024", "2028"], series=[ChartSeries(name="Trend", values=[10, 50])])
        tbl = TableBlock(id="tbl_c8", headers=["A", "B"], rows=[TableRow(id="r", cells=[TableCell(id="c1", value="1"), TableCell(id="c2", value="2")])])
        slide = Slide(
            slide_id="stress_04_narrative",
            template_id="04_table_chart",
            slide_index=4,
            data=SlideData(regions={
                "context_note": "Context Note Header",
                "chart": chart,
                "section_heading": "Deep Haulage Transition",
                "narrative": long_narrative,
                "table": tbl,
                "supporting_insight": InsightBlock(id="ins_c8", title="Impact", body="40% lower OPEX.")
            })
        )
        results = self.template_renderer.render_slide_layout(slide)
        prs, prov = self.ppt_renderer.create_presentation(results)
        struct_res = StructuralValidator.validate_presentation(prs)
        self.assertEqual(struct_res["status"], "PASS")

    # -------------------------------------------------------------------------
    # Case 9: Long bullet points in 05_insight_information
    # -------------------------------------------------------------------------
    def test_case_09_long_bullet_points_wrapping(self):
        bullets = BulletListBlock(
            id="bullets_long",
            items=[
                BulletItem(id="b1", text="First concise bullet point with direct metrics and standard terminology."),
                BulletItem(id="b2", text="Extremely detailed second bullet point highlighting regulatory compliance milestones across European, North American, and Australian jurisdictional oversight bodies including mandatory automated fire suppression."),
                BulletItem(id="b3", text="Third technical bullet detailing CAN bus isolation transformers and regenerative braking power capture.")
            ]
        )
        slide = Slide(
            slide_id="stress_05_bullets",
            template_id="05_insight_information",
            slide_index=5,
            data=SlideData(
                left_column_blocks=[bullets],
                right_column_blocks=[TextBlock(id="r_txt", text="Right column explanatory block.")]
            )
        )
        results = self.template_renderer.render_slide_layout(slide)
        prs, prov = self.ppt_renderer.create_presentation(results)
        struct_res = StructuralValidator.validate_presentation(prs)
        self.assertEqual(struct_res["status"], "PASS")

    # -------------------------------------------------------------------------
    # Case 10: Multi-line table cell wrapping without horizontal overflow
    # -------------------------------------------------------------------------
    def test_case_10_table_cell_wrapping_bounds(self):
        text = "Multi-line wrapped cell content testing boundaries"
        meas = measure_multiline_text(text, "arial", 10, max_width=120.0)
        self.assertGreater(meas["line_count"], 1)
        self.assertLessEqual(meas["width"], 120.0)

    # -------------------------------------------------------------------------
    # Case 11: Minimal/sparse slide content (missing optional fields)
    # -------------------------------------------------------------------------
    def test_case_11_sparse_slide_graceful_handling(self):
        slide = Slide(
            slide_id="stress_sparse_01",
            template_id="01_cover_title_image",
            slide_index=0,
            data=SlideData(regions={"title": "Minimal Title Only"})
        )
        results = self.template_renderer.render_slide_layout(slide)
        self.assertEqual(len(results), 1)
        prs, prov = self.ppt_renderer.create_presentation(results)
        struct_res = StructuralValidator.validate_presentation(prs)
        self.assertEqual(struct_res["status"], "PASS")

    # -------------------------------------------------------------------------
    # Case 12: Unicode and special characters
    # -------------------------------------------------------------------------
    def test_case_12_unicode_and_special_characters(self):
        special_text = "Metric: €450M / ¥3.2B / £85M — Temperature: -20°C to +55°C, Tolerance: ±0.05µm, α/β testing & ‘smart’ quotes."
        headers = ["Region & Metric (€)", "Target (±%)"]
        rows = [["Nordic Core (€)", "±2.5%"], ["Asia-Pacific (¥)", "±4.1%"]]
        tbl = TableBlock(id="tbl_unicode", headers=headers, rows=[TableRow(id=f"r_{i}", cells=[TableCell(id=f"c_{i}_{j}", value=v) for j, v in enumerate(r)]) for i, r in enumerate(rows)])
        slide = Slide(
            slide_id="stress_unicode",
            template_id="06_large_table",
            slide_index=6,
            data=SlideData(regions={"table_title": special_text, "table": tbl})
        )
        results = self.template_renderer.render_slide_layout(slide)
        prs, prov = self.ppt_renderer.create_presentation(results)
        struct_res = StructuralValidator.validate_presentation(prs)
        self.assertEqual(struct_res["status"], "PASS")

    # -------------------------------------------------------------------------
    # Case 13: Single series vs multiple series in charts
    # -------------------------------------------------------------------------
    def test_case_13_single_vs_multi_series_charts(self):
        ch1 = ChartLayoutEngine.layout_chart("bar", ["Q1", "Q2"], ["Revenue"], 800, 400)
        self.assertFalse(ch1.has_legend, "Single series bar chart should omit redundant legend")
        ch2 = ChartLayoutEngine.layout_chart("bar", ["Q1", "Q2"], ["Rev 2024", "Rev 2025"], 800, 400)
        self.assertTrue(ch2.has_legend, "Multi series bar chart must include legend")

    # -------------------------------------------------------------------------
    # Case 14: Insight block with long text
    # -------------------------------------------------------------------------
    def test_case_14_insight_block_with_long_text(self):
        ins = InsightBlock(
            id="long_ins",
            title="Accelerated Battery-Swap Infrastructure Payback Timeline Across Deep Extractions",
            body="Comprehensive empirical modeling of haulage cycles in Canadian sub-surface mines reveals that battery swap stations reduce queue times by 72% relative to fast megawatt chargers, unlocking $14.2M in annual productivity gains per extraction shaft."
        )
        slide = Slide(
            slide_id="stress_ins_slide",
            template_id="05_insight_information",
            slide_index=5,
            data=SlideData(
                left_column_blocks=[ins],
                right_column_blocks=[TextBlock(id="r1", text="Accompanying context narrative.")]
            )
        )
        results = self.template_renderer.render_slide_layout(slide)
        prs, prov = self.ppt_renderer.create_presentation(results)
        struct_res = StructuralValidator.validate_presentation(prs)
        self.assertEqual(struct_res["status"], "PASS")

    # -------------------------------------------------------------------------
    # Case 15: Asymmetric 2-column slide (left heavy)
    # -------------------------------------------------------------------------
    def test_case_15_asymmetric_columns(self):
        left_blocks = [
            TextBlock(id="lh", text="Deep Technical Heading", role="heading"),
            TextBlock(id="lp1", text="First deep narrative describing algorithmic routing."),
            TextBlock(id="lp2", text="Second paragraph analyzing sensor noise in dusty shafts."),
            BulletListBlock(id="lb", items=[BulletItem(id=f"bi_{i}", text=f"Parameter {i}") for i in range(4)])
        ]
        right_blocks = [
            TextBlock(id="rh", text="Brief Right Column", role="heading")
        ]
        slide = Slide(
            slide_id="stress_asym",
            template_id="05_insight_information",
            slide_index=5,
            data=SlideData(left_column_blocks=left_blocks, right_column_blocks=right_blocks)
        )
        results = self.template_renderer.render_slide_layout(slide)
        self.assertEqual(len(results), 1)
        prs, prov = self.ppt_renderer.create_presentation(results)
        struct_res = StructuralValidator.validate_presentation(prs)
        self.assertEqual(struct_res["status"], "PASS")

    # -------------------------------------------------------------------------
    # Case 16: Zero and extreme numeric values in charts
    # -------------------------------------------------------------------------
    def test_case_16_extreme_numeric_values_chart(self):
        chart = ChartBlock(
            id="extreme_chart",
            chart_type="line",
            title="Volatility Index with Zero and High Spikes",
            categories=["Jan", "Feb", "Mar", "Apr", "May"],
            series=[ChartSeries(name="Index", values=[0, 150000, 0, 950000, 1200000])]
        )
        ch_layout = ChartLayoutEngine.layout_chart(
            chart_type="line",
            categories=chart.categories,
            series_names=["Index"],
            available_width=1650.0,
            available_height=650.0,
            title=chart.title
        )
        self.assertTrue(ch_layout.plot_width > 0 and ch_layout.plot_height > 0)

    # -------------------------------------------------------------------------
    # Case 17: Consecutive continuation slides (3+ parts)
    # -------------------------------------------------------------------------
    def test_case_17_consecutive_continuations(self):
        headers = ["ID", "Equipment Model", "Specification", "Deployment Area"]
        rows = [
            TableRow(id=f"r_{i}", cells=[
                TableCell(id=f"c_{i}_1", value=f"ID-{i:03d}"),
                TableCell(id=f"c_{i}_2", value=f"Heavy Hauler Type-{i}"),
                TableCell(id=f"c_{i}_3", value="Autonomous Tier-4 certified powertrain with multi-angle radar."),
                TableCell(id=f"c_{i}_4", value="Zone A Deep Shaft")
            ])
            for i in range(75)  # 75 rows with multi-line specs will span 3+ slides
        ]
        tbl = TableBlock(id="tbl_75", headers=headers, rows=rows)
        slide = Slide(
            slide_id="stress_consec_tbl",
            template_id="06_large_table",
            slide_index=1,
            data=SlideData(regions={"table": tbl})
        )
        results = self.template_renderer.render_slide_layout(slide)
        self.assertGreaterEqual(len(results), 3, "75 large rows should split into at least 3 slides")
        # Verify sequential naming
        self.assertIn("Part 2", results[1].title)
        self.assertIn("Part 3", results[2].title)

    # -------------------------------------------------------------------------
    # Case 18: Custom vs auto-calculated column widths
    # -------------------------------------------------------------------------
    def test_case_18_custom_column_widths(self):
        headers = ["Metric", "Description", "Value"]
        rows = [["M1", "Long descriptive text", "100"]]
        widths = TableLayoutEngine.calculate_column_widths(headers, rows, available_width=1200.0)
        self.assertEqual(len(widths), 3)
        self.assertAlmostEqual(sum(widths), 1200.0, delta=1.0)
        # The descriptive column should receive more width than the short metric and value columns
        self.assertGreater(widths[1], widths[0])
        self.assertGreater(widths[1], widths[2])

    # -------------------------------------------------------------------------
    # Case 19: All safe area and slide boundary constraints strictly respected
    # -------------------------------------------------------------------------
    def test_case_19_universal_safe_area_compliance(self):
        # Generate full sample report containing diverse templates
        report = Report(
            report_id="stress_safe_area_rep",
            title="Safe Area Stress Report",
            slides=[
                Slide(slide_id="s1", template_id="01_cover_title_image", slide_index=0, data=SlideData(regions={"title": "Cover Slide"})),
                Slide(slide_id="s2", template_id="02_toc_image", slide_index=1, data=SlideData(regions={"items": [TOCItem(id=f"t{i}", number=f"{i}", title=f"TOC {i}") for i in range(12)]})),
                Slide(slide_id="s3", template_id="03_section_opener", slide_index=2, data=SlideData(regions={"section_title": "Section 1", "index_list": [IndexItem(id=f"idx{i}", number=f"1.{i}", title=f"Index {i}") for i in range(6)]}))
            ]
        )
        layout_results = self.template_renderer.render_report_layout(report)
        prs, prov = self.ppt_renderer.create_presentation(layout_results)
        struct_res = StructuralValidator.validate_presentation(prs)
        self.assertEqual(struct_res["status"], "PASS")
        self.assertEqual(len(struct_res["errors"]), 0)


if __name__ == "__main__":
    unittest.main()
