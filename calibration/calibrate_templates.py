"""
Template Calibration Pipeline (Phase 0.5)
Calibrates each of the 8 fundamental templates individually using realistic reference content:
1. Computes layout via TemplateRenderer -> LayoutResult
2. Emits native PowerPoint PPTX via PowerPointRenderer
3. Runs Layer A StructuralValidator on PPTX
4. Rasterizes slide to PNG via PowerPoint COM into assets/templates/mining_ugv/rendered/
5. Runs Layer B RenderedValidator on the rasterized PNG
6. Runs VisualRegressionValidator against assets/templates/mining_ugv/reference/
"""

import os
import json
from typing import Dict, Any, List
from renderer.template_renderer import TemplateRenderer
from renderer.powerpoint_renderer import PowerPointRenderer
from renderer.rasterizer import PowerPointRasterizer
from validators.structural_validator import StructuralValidator
from validators.rendered_validator import RenderedValidator
from validators.visual_regression import VisualRegressionValidator
from models.report_model import (
    Slide, SlideData, TextBlock, TableBlock, TableRow, TableCell,
    ChartBlock, ChartSeries, BulletListBlock, BulletItem, InsightBlock, TOCItem, IndexItem
)


def get_reference_content_for_template(template_id: str) -> Slide:
    """Provides realistic calibration content for a given template archetype."""
    if template_id == "01_cover_title_image":
        return Slide(
            slide_id="calib_01",
            template_id="01_cover_title_image",
            slide_index=0,
            title="Mining Underground Ground Vehicles (UGV) Market",
            data=SlideData(regions={
                "title": "Mining Underground Ground Vehicles (UGV) Market",
                "subtitle": "Global Market Size, Autonomous Technologies & Forecast 2026-2035",
                "metadata": "Strategic Industry Report | Antigravity Research | September 2026"
            })
        )

    elif template_id == "02_toc_image":
        toc_items = [
            TOCItem(id=f"toc_{i+1:02d}", number=f"{i+1:02d}", title=title)
            for i, title in enumerate([
                "Executive Summary & Industry Outlook",
                "Market Scope & Research Methodology",
                "Autonomous Navigation & Robotics Drivers",
                "Sub-surface Fleet Electrification",
                "Battery Electric vs Diesel Powertrain TCO",
                "Global Market Size & Forecast (2024-2035)",
                "Segment Analysis: Loaders & Haulers",
                "Regional Deep Dive: North America & APAC",
                "Competitive Landscape & OEM Benchmarking",
                "Tier-1 Component & LiDAR Sensor Providers",
                "Safety Regulations & Underground Standards",
                "Mine Modernization & Automation Case Studies",
                "Infrastructure Readiness: Fast Charging & 5G",
                "Key Vendor Strategic Profiles",
                "Emerging M&A and Strategic Partnerships",
                "Supply Chain Dynamics & Battery Raw Materials",
                "Technology Roadmap & Industry Predictions",
                "Conclusions, Recommendations & Next Steps"
            ])
        ]
        return Slide(
            slide_id="calib_02",
            template_id="02_toc_image",
            slide_index=1,
            title="Table of Contents",
            data=SlideData(regions={"items": toc_items})
        )

    elif template_id == "03_section_opener":
        subsections = [
            IndexItem(id=f"sub_2_{i+1}", number=f"2.{i+1}", title=title)
            for i, title in enumerate([
                "Autonomous Mining Vehicle Definition",
                "Research Methodology & Model Parameters",
                "Scope of Fleet Inclusions & Exclusions",
                "Geographic Granularity & Mine Types",
                "Primary Interviews & Industry Validation",
                "Secondary Data Sources & Fleet Registries",
                "Forecasting Models & Sensitivity Analysis",
                "Currency Conversion & Inflation Assumptions",
                "Key Performance Indicators (KPIs) Tracked",
                "Standard Operating Environment Classifications"
            ])
        ]
        return Slide(
            slide_id="calib_03",
            template_id="03_section_opener",
            slide_index=2,
            title="2. Research Scope & Methodology",
            data=SlideData(regions={
                "section_title": "2. Research Scope & Methodology",
                "index_list": subsections
            })
        )

    elif template_id == "04_table_chart":
        chart = ChartBlock(
            id="calib_ch_04",
            chart_type="bar",
            title="Autonomous UGV Fleet Adoption by Region (2024 vs 2030)",
            categories=["North America", "Europe", "Asia Pacific", "Latin America", "MEA"],
            series=[
                ChartSeries(name="2024 (Units)", values=[420, 310, 580, 240, 190]),
                ChartSeries(name="2030 (Units)", values=[1150, 890, 1680, 710, 540])
            ]
        )
        headers = ["Segment", "2024", "2030", "CAGR"]
        raw_rows = [
            ["LHD Loaders", "$1.85B", "$4.20B", "14.6%"],
            ["Haul Trucks", "$2.40B", "$5.90B", "16.1%"],
            ["Drill Rigs", "$0.95B", "$2.10B", "14.1%"],
            ["Utility UGVs", "$0.45B", "$1.15B", "16.9%"]
        ]
        rows = [
            TableRow(id=f"r_{r_i}", cells=[TableCell(id=f"c_{r_i}_{c_i}", value=val) for c_i, val in enumerate(row)])
            for r_i, row in enumerate(raw_rows)
        ]
        table = TableBlock(id="calib_tbl_04", headers=headers, rows=rows)
        insight = InsightBlock(
            id="calib_ins_04",
            title="Rapid Adoption in High-Labor Cost Markets",
            body="North American and Australian underground operations are aggressively converting to Level 4 automated fleets to counter severe skilled operator shortages."
        )
        return Slide(
            slide_id="calib_04",
            template_id="04_table_chart",
            slide_index=3,
            title="Regional Fleet Adoption & Market Sizing",
            data=SlideData(regions={
                "context_note": "Comparative growth rate across underground vehicle classifications (2024-2030)",
                "chart": chart,
                "section_heading": "Segment Growth Velocity",
                "narrative": "Underground haul trucks represent the largest revenue share, while utility UGVs exhibit the fastest CAGR due to compact teleoperation advancements.",
                "table": table,
                "supporting_insight": insight
            })
        )

    elif template_id == "05_insight_information":
        left_blocks = [
            TextBlock(id="b_05_l1", text="Powertrain Transition Dynamics", role="heading"),
            TextBlock(id="b_05_l2", text="Underground mining operators face escalating ventilation cooling and diesel particulate filter (DPF) maintenance costs. The shift toward battery electric vehicles (BEVs) reduces required airflow by up to 40% in deep extraction shafts.", role="body"),
            BulletListBlock(id="b_05_l3", items=[
                BulletItem(id="b_05_l3_1", text="Elimination of diesel emissions drastically lowers ventilation capital expenditure."),
                BulletItem(id="b_05_l3_2", text="Regenerative braking on decline ramps recovers up to 18% of battery capacity."),
                BulletItem(id="b_05_l3_3", text="Fast megawatt-charging stations enable turnaround times below 25 minutes.")
            ])
        ]
        right_blocks = [
            TextBlock(id="b_05_r1", text="Regulatory & Environmental Mandates", role="heading"),
            TextBlock(id="b_05_r2", text="Stringent workplace safety regulations across Tier-1 mining jurisdictions are accelerating the retirement of older mechanical drive equipment.", role="body"),
            InsightBlock(
                id="b_05_r3",
                title="TCO Breakeven Within 3.2 Years",
                body="Despite higher initial vehicle procurement costs, lower fuel expenses and reduced shaft ventilation requirements yield a compelling 3.2-year payback period for tier-1 operators."
            )
        ]
        return Slide(
            slide_id="calib_05",
            template_id="05_insight_information",
            slide_index=4,
            title="Electrification Drivers & Total Cost of Ownership",
            data=SlideData(
                left_column_blocks=left_blocks,
                right_column_blocks=right_blocks
            )
        )

    elif template_id == "06_large_table":
        headers = ["OEM Provider", "Country", "Model Series", "Payload (t)", "Drive Type", "Autonomy Level", "Battery (kWh)", "Deployments", "Status"]
        raw_data = [
            ["Sandvik Mining", "Sweden", "LH518B / Toro", "18.0", "Battery-Electric", "AutoMine Level 4", "354 kWh", "145 units", "Commercial"],
            ["Epiroc Group", "Sweden", "Scooptram ST14", "14.0", "Battery-Electric", "Mobilaris L3", "280 kWh", "120 units", "Commercial"],
            ["Caterpillar Inc", "USA", "R2900 XE", "18.5", "Diesel-Electric", "Cat MineStar L4", "Hybrid", "210 units", "Commercial"],
            ["Komatsu Mining", "Japan", "WX07 Hybrid", "7.0", "Hybrid Drive", "Autonomous Ready", "180 kWh", "85 units", "Commercial"],
            ["Normet Group", "Finland", "SmartDrive MF", "10.0", "Full Battery", "Tele-remote", "160 kWh", "60 units", "Commercial"],
            ["MacLean Engineering", "Canada", "EV Series", "12.0", "Battery-Electric", "Semi-Autonomous", "220 kWh", "75 units", "Commercial"],
            ["GIA Industri", "Sweden", "Kiruna Electric", "25.0", "Trolley / Battery", "Remote L2", "Trolley Feed", "40 units", "Commercial"],
            ["Fermel Mining", "South Africa", "Ferret UGV", "5.0", "Battery Electric", "L2 Pilot", "90 kWh", "30 units", "Pilot"],
            ["Mining3 Alliance", "Australia", "H-UGV Prototype", "15.0", "Hydrogen Hybrid", "Full L4", "Fuel Cell + 100kWh", "8 units", "R&D Prototype"],
            ["GHH Fahrzeuge", "Germany", "LF-10e", "10.0", "Tethered Electric", "Manual / Remote", "Direct Cable", "50 units", "Commercial"],
            ["Aard Mining", "South Africa", "Aardvark EV", "8.0", "Battery Electric", "Line-of-Sight", "110 kWh", "25 units", "Commercial"],
            ["Resemin SAC", "Peru", "Bolter Muki", "6.5", "Electro-Hydraulic", "Tele-operation", "75 kWh", "45 units", "Commercial"]
        ]
        rows = [
            TableRow(id=f"oem_r{r_i}", cells=[TableCell(id=f"oem_c{r_i}_{c_i}", value=val) for c_i, val in enumerate(row)])
            for r_i, row in enumerate(raw_data)
        ]
        table = TableBlock(id="calib_tbl_06", headers=headers, rows=rows)
        return Slide(
            slide_id="calib_06",
            template_id="06_large_table",
            slide_index=5,
            title="Global Mining UGV OEM Model Specifications & Autonomy Comparison",
            data=SlideData(regions={"table": table})
        )

    elif template_id == "07_large_chart":
        chart = ChartBlock(
            id="calib_ch_07",
            chart_type="line",
            title="Global Autonomous Mining UGV Market Revenue Forecast ($ Millions, 2024-2035)",
            categories=["2024", "2025", "2026", "2027", "2028", "2029", "2030", "2032", "2035"],
            series=[
                ChartSeries(name="Base Scenario", values=[4200, 4850, 5600, 6520, 7600, 8900, 10450, 14200, 21500]),
                ChartSeries(name="Accelerated Transition", values=[4200, 5100, 6200, 7550, 9200, 11200, 13700, 19500, 29800]),
                ChartSeries(name="Conservative Outlook", values=[4200, 4600, 5100, 5700, 6400, 7200, 8150, 10500, 15200])
            ]
        )
        return Slide(
            slide_id="calib_07",
            template_id="07_large_chart",
            slide_index=6,
            title="Global Market Revenue Trajectory Across Scenario Forecasts",
            data=SlideData(regions={"chart": chart})
        )

    elif template_id == "08_multi_table_dashboard_2col":
        tbl1 = TableBlock(
            id="dash_tbl_1",
            headers=["Battery Chem", "Cycle Life", "Cost/kWh"],
            rows=[
                TableRow(id="dt1_r1", cells=[TableCell(id="dt1_c1_1", value="LFP"), TableCell(id="dt1_c1_2", value="4,000"), TableCell(id="dt1_c1_3", value="$115")]),
                TableRow(id="dt1_r2", cells=[TableCell(id="dt1_c2_1", value="NMC 811"), TableCell(id="dt1_c2_2", value="2,200"), TableCell(id="dt1_c2_3", value="$145")]),
                TableRow(id="dt1_r3", cells=[TableCell(id="dt1_c3_1", value="Solid-State"), TableCell(id="dt1_c3_2", value="5,000+"), TableCell(id="dt1_c3_3", value="$210")])
            ]
        )
        tbl2 = TableBlock(
            id="dash_tbl_2",
            headers=["Sensor Type", "Range (m)", "Dust Penetration"],
            rows=[
                TableRow(id="dt2_r1", cells=[TableCell(id="dt2_c1_1", value="Solid-State LiDAR"), TableCell(id="dt2_c1_2", value="150m"), TableCell(id="dt2_c1_3", value="Moderate")]),
                TableRow(id="dt2_r2", cells=[TableCell(id="dt2_c2_1", value="77 GHz Radar"), TableCell(id="dt2_c2_2", value="250m"), TableCell(id="dt2_c2_3", value="High (Superior)")]),
                TableRow(id="dt2_r3", cells=[TableCell(id="dt2_c3_1", value="Thermal Vision"), TableCell(id="dt2_c3_2", value="80m"), TableCell(id="dt2_c3_3", value="High")])
            ]
        )
        left_blocks = [
            TextBlock(id="dash_l_h", text="Battery Chemistries in Deep Mining", role="heading"),
            tbl1,
            TextBlock(id="dash_l_p", text="LFP dominates heavy underground loaders due to superior thermal stability in confined shafts.", role="body")
        ]
        right_blocks = [
            TextBlock(id="dash_r_h", text="Perception & Sensor Stack Architecture", role="heading"),
            tbl2,
            InsightBlock(
                id="dash_r_ins",
                title="Radar-LiDAR Fusion Crucial",
                body="Zero-visibility blast smoke environments necessitate multi-modal radar-LiDAR sensor fusion."
            )
        ]
        return Slide(
            slide_id="calib_08",
            template_id="08_multi_table_dashboard_2col",
            slide_index=7,
            title="Subsystem Dashboard: Energy Storage & Autonomous Perception",
            data=SlideData(
                left_column_blocks=left_blocks,
                right_column_blocks=right_blocks
            )
        )

    raise ValueError(f"Unknown template_id: {template_id}")


def calibrate_all_templates(output_dir: str = "output/calibration") -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    rendered_dir = "assets/templates/mining_ugv/rendered"
    os.makedirs(rendered_dir, exist_ok=True)

    template_ids = [
        "01_cover_title_image",
        "02_toc_image",
        "03_section_opener",
        "04_table_chart",
        "05_insight_information",
        "06_large_table",
        "07_large_chart",
        "08_multi_table_dashboard_2col"
    ]

    t_renderer = TemplateRenderer()
    ppt_renderer = PowerPointRenderer()
    results = {}

    for t_id in template_ids:
        print(f"\n[CALIBRATION] Calibrating Template: {t_id}...")
        slide_content = get_reference_content_for_template(t_id)
        layout_results = t_renderer.render_slide_layout(slide_content)

        # 1. Generate PPTX
        prs, prov_map = ppt_renderer.create_presentation(layout_results)
        pptx_filename = f"{t_id}.pptx"
        pptx_path = os.path.join(output_dir, pptx_filename)
        prs.save(pptx_path)
        print(f"  -> Generated PPTX: {pptx_path}")

        # 2. Layer A: Structural Validation
        struct_res = StructuralValidator.validate_presentation(prs)
        print(f"  -> Structural Validation: {struct_res['status']} ({len(struct_res['errors'])} errors)")

        # 3. Slide Rasterization via PowerPoint COM
        raster_pngs = PowerPointRasterizer.rasterize_pptx(pptx_path, rendered_dir)
        png_path = raster_pngs[0] if raster_pngs else None
        
        rendered_res = {"status": "SKIPPED", "message": "Rasterization not performed"}
        if png_path and os.path.exists(png_path):
            # Rename to canonical template ID in rendered/
            target_png = os.path.join(rendered_dir, f"{t_id}.png")
            if os.path.exists(target_png):
                os.remove(target_png)
            os.rename(png_path, target_png)
            print(f"  -> Rasterized Slide PNG: {target_png}")

            # 4. Layer B: Rendered Validation
            rendered_res = RenderedValidator.validate_slide_image(target_png)
            print(f"  -> Rendered Validation: {rendered_res['status']}")

        # 5. Visual Regression check (returns SKIPPED if reference PNG not yet present)
        ref_path = f"assets/templates/mining_ugv/reference/{t_id}.png"
        reg_res = VisualRegressionValidator.compare_images(ref_path, target_png if png_path else "")
        print(f"  -> Visual Regression: {reg_res['status']} ({reg_res.get('message', 'Checked')})")

        results[t_id] = {
            "template_id": t_id,
            "pptx_path": pptx_path,
            "structural_validation": struct_res,
            "rendered_validation": rendered_res,
            "visual_regression": reg_res,
            "calibrated": (struct_res["status"] == "PASS")
        }

    return results


if __name__ == "__main__":
    results = calibrate_all_templates()
    print("\n==================================================")
    print("CALIBRATION SUMMARY:")
    all_ok = True
    for t_id, res in results.items():
        ok = res["calibrated"]
        all_ok = all_ok and ok
        status_str = "PASS" if ok else "FAIL"
        print(f"  [{status_str}] {t_id}")
    print("==================================================")
