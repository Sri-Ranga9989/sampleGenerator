"""
build_full_email_report_json.py
Parses the entire source_email.html and generates a complete, canonical report JSON manifest
(examples/mining_ugv_full_email_report.json) containing ALL 42 data tables and intelligence sections.
"""

import json
from bs4 import BeautifulSoup
from typing import List, Dict, Any


def extract_table(table_tag) -> List[List[str]]:
    rows = table_tag.find_all("tr")
    grid = []
    for r in rows:
        cells = [c.get_text(strip=True).replace("\xa0", " ") for c in r.find_all(["th", "td"])]
        if any(cells):
            grid.append(cells)
    return grid


def make_table_block(block_id: str, grid: List[List[str]]) -> Dict[str, Any]:
    if not grid:
        return {"type": "table", "id": block_id, "headers": [], "rows": []}
    headers = grid[0]
    rows = []
    for r_idx, row in enumerate(grid[1:]):
        # Pad row if shorter than headers
        padded_row = row + [""] * max(0, len(headers) - len(row))
        rows.append({
            "id": f"{block_id}_r{r_idx+1}",
            "cells": [
                {"id": f"{block_id}_c{r_idx+1}_{c_idx+1}", "value": val}
                for c_idx, val in enumerate(padded_row[:len(headers)])
            ]
        })
    return {
        "type": "table",
        "id": block_id,
        "headers": headers,
        "rows": rows
    }


def build_full_report():
    print("Loading source_email.html...")
    with open("source_email.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    all_tables = soup.find_all("table")
    print(f"Total HTML tables extracted: {len(all_tables)}")

    # Data tables start at index 4 (0 to 3 are outer email wrappers)
    # T4 to T45 are the 42 content tables
    T = {}
    for idx in range(4, len(all_tables)):
        T[idx] = extract_table(all_tables[idx])

    slides: List[Dict[str, Any]] = []

    # =============================================================
    # SLIDE 1: Cover Title (01_cover_title_image)
    # =============================================================
    slides.append({
        "template_id": "01_cover_title_image",
        "slide_index": len(slides),
        "data": {
            "title": {
                "type": "text",
                "id": "cov_title",
                "value": "Mining Underground Ground Vehicles (UGV) Market"
            },
            "subtitle": {
                "type": "text",
                "id": "cov_sub",
                "value": "Comprehensive Market Intelligence, Commercial Sizing, Fleet Economics & 2030 Roadmap"
            },
            "metadata": {
                "type": "text",
                "id": "cov_meta",
                "value": "Enterprise Intelligence Deck | 42 Verified Data Grids | September 2026"
            }
        }
    })

    # =============================================================
    # SLIDE 2: Table of Contents (02_toc_image) - 18 sections
    # =============================================================
    toc_titles = [
        "Executive Summary & Strategic Findings",
        "Market Scope, Definitions & Taxonomy",
        "Historical Market Sizing (2020-2030F)",
        "Market Structure & Core Segmentation",
        "Installed Base & Replacement Cycles",
        "Technology, Sensor Fusion & SLAM",
        "Application & End-User Intelligence",
        "Buyer Decision-Making Intelligence",
        "Customer Requirements & Specifications",
        "Voice of Customer & Pain Points",
        "Pricing, Transaction & Negotiation",
        "Purchase Intent & Budget Allocation",
        "Technology Adoption & Trial Pipeline",
        "Regional Intelligence: Europe & Germany",
        "Value Chain & Ecosystem Analysis",
        "Customer-Validated White-Space Matrix",
        "Company Benchmarking: Komatsu Ltd.",
        "Strategic Recommendations & 2030 Roadmap"
    ]
    slides.append({
        "template_id": "02_toc_image",
        "slide_index": len(slides),
        "data": {
            "title": {"type": "text", "id": "toc_heading", "value": "TABLE OF CONTENTS"},
            "items": [
                {"id": f"toc_item_{i+1:02d}", "number": f"{i+1:02d}", "title": t}
                for i, t in enumerate(toc_titles)
            ]
        }
    })

    # =============================================================
    # SECTION 1: Executive Summary & Strategic Findings
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "1. Executive Summary & Strategic Findings",
            "index_list": [
                {"id": "sub_1_1", "number": "1.1", "title": "Market Snapshot & Growth Trajectory"},
                {"id": "sub_1_2", "number": "1.2", "title": "Demand & Near-Term Purchase Pipeline"},
                {"id": "sub_1_3", "number": "1.3", "title": "Application Demand & Fleet Economics"},
                {"id": "sub_1_4", "number": "1.4", "title": "Customer Economics & Fleet CAPEX"},
                {"id": "sub_1_5", "number": "1.5", "title": "Critical Buyer Specifications & Thresholds"},
                {"id": "sub_1_6", "number": "1.6", "title": "Core Technology Adoption Dynamics"},
                {"id": "sub_1_7", "number": "1.7", "title": "Purchase Decision Factors & Governance"},
                {"id": "sub_1_8", "number": "1.8", "title": "Operational Constraints & Deployment Friction"}
            ]
        }
    })

    # Slide 4: Table 1.1 + Chart
    slides.append({
        "template_id": "04_table_chart",
        "slide_index": len(slides),
        "data": {
            "context_note": "Comprehensive market valuation and fleet growth across forecast horizons (2025-2030F)",
            "chart": {
                "type": "chart",
                "id": "ch_exec_1_1",
                "chart_type": "column_clustered",
                "title": "Mining UGV Market Value ($M) & Annual Deployments (Units)",
                "categories": ["2025", "2026E", "2030F"],
                "series": [
                    {"name": "Market Value Midpoint ($M)", "values": [220.0, 270.0, 650.0]},
                    {"name": "Deployments Midpoint (Units)", "values": [1350.0, 1750.0, 4500.0]}
                ]
            },
            "heading": "Market Acceleration & Underground Share",
            "narrative": "Underground operations account for 60-72% of total UGV demand, expanding at an 18-23% CAGR. Market value is projected to reach $520-780M by 2030 as operators transition from single-vehicle trials to multi-unit fleet production.",
            "table": make_table_block("tbl_1_1", T[4]),
            "insight": {
                "type": "insight",
                "id": "ins_exec_1_1",
                "title": "KEY INSIGHT: Worker Safety Driving CAPEX Budgets",
                "body": "Worker exposure reduction ranks as the #1 purchase trigger (18-24% weighting), far exceeding initial equipment price (4-7%), compelling rapid fleet automation in hazardous stopes."
            }
        }
    })

    # Slide 5: Strategic Synthesis (05_insight_information)
    slides.append({
        "template_id": "05_insight_information",
        "slide_index": len(slides),
        "data": {
            "title": "Strategic Market Findings & Structural Buyer Dynamics",
            "left_column": [
                {"type": "text", "id": "t_exec_left_h", "role": "heading", "text": "Key Commercial Transition Vectors"},
                {"type": "text", "id": "t_exec_left_p", "role": "paragraph", "text": "Underground mining represents the primary near-term commercial market. While inspection and mapping are the dominant initial entry points, safety, hazardous-area intervention, and production-support systems are expanding at the fastest CAGR."},
                {
                    "type": "bullet_list",
                    "id": "bl_exec_left",
                    "items": [
                        {"id": "b_el_1", "text": "Pilot conversion is the principal bottleneck: 35-55% of mine pilots convert to commercial contracts.", "level": 0},
                        {"id": "b_el_2", "text": "Retrofit autonomy kits offer a faster, lower-CAPEX route than complete machinery replacement.", "level": 0},
                        {"id": "b_el_3", "text": "Multi-unit fleet deployments (10-50+ units) trigger massive operational economies of scale.", "level": 0}
                    ]
                }
            ],
            "right_column": [
                {"type": "text", "id": "t_exec_right_h", "role": "heading", "text": "Value Shift: Hardware to Software & AI"},
                {"type": "text", "id": "t_exec_right_p", "role": "paragraph", "text": "Technology differentiation is decisively shifting away from vehicle chassis mechanics toward GNSS-denied autonomy, multi-sensor fusion, edge AI inference, and deep integration with mine management systems."},
                {
                    "type": "insight",
                    "id": "ins_exec_right",
                    "title": "KEY INSIGHT: Expanded Revenue Beyond Hardware",
                    "body": "Software licenses, sensor payloads, communications infrastructure, and centralized fleet management software expand total deployment revenue by 30-50% over bare vehicle hardware."
                }
            ]
        }
    })

    # Slide 6: Demand Pipeline & Customer Economics (Tables 1.2 & 1.4 Dashboard)
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Near-Term Demand Pipeline & Customer Fleet Economics (2026E)",
            "left_column": [
                {"type": "text", "id": "h_1_2", "role": "heading", "text": "Table 1.2: Demand & Purchase Pipeline Indicators"},
                make_table_block("tbl_1_2", T[5]),
                {
                    "type": "insight",
                    "id": "ins_1_2",
                    "title": "Pipeline Velocity Indicator",
                    "body": "Active trial-to-contract conversion velocity has increased by 14% year-over-year as tier-1 miners standardize automated safety protocols."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_1_4", "role": "heading", "text": "Table 1.4: Commercial Economics & Fleet Metrics"},
                make_table_block("tbl_1_4", T[7]),
                {
                    "type": "text",
                    "id": "p_1_4",
                    "role": "paragraph",
                    "text": "Average initial deal sizes range from $180K to $850K for pilot batches, scaling to $2.5M-$8.0M for full-stope production fleets."
                }
            ]
        }
    })

    # Slide 7: Buyer Requirements & Technology Adoption (Tables 1.5 & 1.6 Dashboard)
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Buyer Requirement Thresholds & Technology Adoption Targets",
            "left_column": [
                {"type": "text", "id": "h_1_5", "role": "heading", "text": "Table 1.5: Core Buyer Requirements (Current vs 2030)"},
                make_table_block("tbl_1_5", T[8]),
                {
                    "type": "bullet_list",
                    "id": "bl_1_5",
                    "items": [
                        {"id": "b_1_5_1", "text": "Battery swap times must drop under 10 minutes to maintain 24/7 haulage cycles.", "level": 0},
                        {"id": "b_1_5_2", "text": "Mean time between failures (MTBF) exceeding 500 operating hours is now mandatory.", "level": 0}
                    ]
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_1_6", "role": "heading", "text": "Table 1.6: Subsystem Technology Adoption Trajectory"},
                make_table_block("tbl_1_6", T[9]),
                {
                    "type": "insight",
                    "id": "ins_1_6",
                    "title": "SLAM & Sensor Fusion Dominance",
                    "body": "LiDAR-inertial SLAM adoption is expanding at >40% CAGR as sub-surface GNSS denial mandates self-contained positioning."
                }
            ]
        }
    })

    # Slide 8: Decision Factors & Operational Constraints (Tables 1.7 & 1.8 Dashboard)
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Purchase Decision Weightings & Deployment Constraint Analysis",
            "left_column": [
                {"type": "text", "id": "h_1_7", "role": "heading", "text": "Table 1.7: Purchase Decision Weighting Matrix"},
                make_table_block("tbl_1_7", T[10]),
                {
                    "type": "insight",
                    "id": "ins_1_7",
                    "title": "Safety Over Capital Expenditure",
                    "body": "Life-safety compliance and regulatory risk mitigation drive 3.5x higher purchasing influence than upfront hardware price."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_1_8", "role": "heading", "text": "Table 1.8: Sub-Surface Deployment Constraints"},
                make_table_block("tbl_1_8", T[11]),
                {
                    "type": "text",
                    "id": "p_1_8",
                    "role": "paragraph",
                    "text": "Harsh environmental conditions (dust, mud, humidity, corrosive brine) represent the primary source of early pilot failures."
                }
            ]
        }
    })

    # =============================================================
    # SECTION 3: Historical Development & Market Sizing (2020-2030F)
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "3. Historical Development & Market Sizing (2020-2030F)",
            "index_list": [
                {"id": "sub_3_1", "number": "3.1", "title": "Multi-Year Market Sizing & Fleet Growth (2020-2027F)"},
                {"id": "sub_3_2", "number": "3.2", "title": "Annual Deployment Velocity & ASP Development"},
                {"id": "sub_3_3", "number": "3.3", "title": "Market Structure, Demand & Growth Indicator Benchmarks"}
            ]
        }
    })

    # Slide 10: Table 3.1 Large Table
    slides.append({
        "template_id": "06_large_table",
        "slide_index": len(slides),
        "data": {
            "title": "Table 3.1: Historical Market Development & Fleet Sizing (2020-2027F)",
            "table": make_table_block("tbl_3_1", T[12])
        }
    })

    # Slide 11: Large Chart
    slides.append({
        "template_id": "07_large_chart",
        "slide_index": len(slides),
        "data": {
            "title": "Mining UGV Market Trajectory & Fleet Installed Base (2020-2027F)",
            "chart": {
                "type": "chart",
                "id": "ch_hist_3_1",
                "chart_type": "line",
                "title": "Global Active Installed Fleet (Units) vs Market Value ($M)",
                "categories": ["2020", "2021", "2022", "2023", "2024", "2025", "2026E", "2027F"],
                "series": [
                    {"name": "Installed Base (Units)", "values": [850.0, 1200.0, 1850.0, 2600.0, 3700.0, 5000.0, 6800.0, 9200.0]},
                    {"name": "Market Value ($M)", "values": [35.0, 52.0, 80.0, 115.0, 165.0, 220.0, 290.0, 395.0]}
                ]
            }
        }
    })

    # Slide 12: Table 3.2 Large Table
    slides.append({
        "template_id": "06_large_table",
        "slide_index": len(slides),
        "data": {
            "title": "Table 3.2: Historical Market Structure, Demand & Growth Indicators",
            "table": make_table_block("tbl_3_2", T[13])
        }
    })

    # =============================================================
    # SECTION 4: Market Structure & Core Segmentation Analysis
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "4. Market Structure & Core Segmentation Analysis",
            "index_list": [
                {"id": "sub_4_1", "number": "4.1", "title": "Comprehensive Segmentation Master Grid (2025)"},
                {"id": "sub_4_2", "number": "4.2", "title": "Analysis by Vehicle Type, Autonomy Level & Payload"},
                {"id": "sub_4_3", "number": "4.3", "title": "Propulsion Architecture, Power Sources & ASP Benchmarks"}
            ]
        }
    })

    # Slide 14: Table 4.1 Master Table
    slides.append({
        "template_id": "06_large_table",
        "slide_index": len(slides),
        "data": {
            "title": "Table 4.1: Mining UGV Market Structure & Core Segmentation (2025)",
            "table": make_table_block("tbl_4_1", T[14])
        }
    })

    # =============================================================
    # SECTION 8: Application & End-User Intelligence
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "8. Application & End-User Intelligence",
            "index_list": [
                {"id": "sub_8_1", "number": "8.1", "title": "Mining UGV Application Intelligence & Commercial ASPs"},
                {"id": "sub_8_2", "number": "8.2", "title": "End-User Profiles, Fleet Sizing & Operational Economics"},
                {"id": "sub_8_3", "number": "8.3", "title": "Mission Profiles: Inspection, Mapping, Haulage & Rescue"}
            ]
        }
    })

    # Slide 16: Table 8.1 + Chart
    slides.append({
        "template_id": "04_table_chart",
        "slide_index": len(slides),
        "data": {
            "context_note": "Relative share and growth velocity across primary underground UGV operational missions",
            "chart": {
                "type": "chart",
                "id": "ch_app_8_1",
                "chart_type": "column_clustered",
                "title": "Application Market Share Comparison (2025 vs 2030F)",
                "categories": ["Mine Insp.", "3D Mapping", "Safety Ops", "Infrastructure", "Env Monitor", "Material Haul"],
                "series": [
                    {"name": "2025 Share (%)", "values": [22.5, 17.5, 14.5, 12.5, 10.0, 10.0]},
                    {"name": "2030F Share (%)", "values": [20.0, 14.0, 17.0, 15.0, 12.0, 12.5]}
                ]
            },
            "heading": "High-Velocity Operational Use Cases",
            "narrative": "Mine inspection and mapping represent the primary volume base, but hazardous-area safety inspection and material transport are expanding fastest (21-29% CAGR), driven by direct human hazard removal.",
            "table": make_table_block("tbl_8_1", T[15]),
            "insight": {
                "type": "insight",
                "id": "ins_app_8_1",
                "title": "KEY INSIGHT: Autonomous Sampling Expansion",
                "body": "Specialized sampling and explosive-zone inspection UGVs show the highest growth rate at 25-32% CAGR, as mines enforce total non-entry in blast clearance zones."
            }
        }
    })

    # Slide 17: Table 8.2 & Table 8.3 Dashboard
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "End-User Segmentation, Fleet Deployment & Operating Economics",
            "left_column": [
                {"type": "text", "id": "h_8_2", "role": "heading", "text": "Table 8.2: End-User Intelligence & Market Share"},
                make_table_block("tbl_8_2", T[16]),
                {
                    "type": "insight",
                    "id": "ins_8_2",
                    "title": "Tier-1 Mining Houses Drive Volume",
                    "body": "Top 10 mining multinationals account for 58% of cumulative capital expenditure on underground autonomous fleets."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_8_3", "role": "heading", "text": "Table 8.3: End-User Metric Benchmarks"},
                make_table_block("tbl_8_3", T[17]),
                {
                    "type": "bullet_list",
                    "id": "bl_8_3",
                    "items": [
                        {"id": "b_8_3_1", "text": "Contract mining contractors achieve 28% faster payback through multi-site machine sharing.", "level": 0},
                        {"id": "b_8_3_2", "text": "Leasing and RaaS models represent 35% of all new fleet additions in mid-tier mines.", "level": 0}
                    ]
                }
            ]
        }
    })

    # =============================================================
    # SECTION 11: Customer Requirements & Specifications
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "11. Customer Requirements & Specifications",
            "index_list": [
                {"id": "sub_11_1", "number": "11.1", "title": "Technical Specifications by UGV Class (2025-2030)"},
                {"id": "sub_11_2", "number": "11.2", "title": "Buyer Requirement Thresholds & Commercial Trade-Offs"},
                {"id": "sub_11_3", "number": "11.3", "title": "Environmental Sealing, Battery Runtime & Payload Benchmarks"}
            ]
        }
    })

    # Slide 19: Table 11.1 Large Table
    slides.append({
        "template_id": "06_large_table",
        "slide_index": len(slides),
        "data": {
            "title": "Table 11.1: Customer Technical Requirements by UGV Class (2025-2030)",
            "table": make_table_block("tbl_11_1", T[18])
        }
    })

    # Slide 20: Table 11.2 Large Table
    slides.append({
        "template_id": "06_large_table",
        "slide_index": len(slides),
        "data": {
            "title": "Table 11.2: Customer-Validated Requirements & Specification Thresholds",
            "table": make_table_block("tbl_11_2", T[19])
        }
    })

    # =============================================================
    # SECTION 14: Supplier Selection & Incumbency Intelligence
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "14. Supplier Selection & Incumbency Intelligence",
            "index_list": [
                {"id": "sub_14_1", "number": "14.1", "title": "Supplier Selection Criteria & Incumbency Lock-in"},
                {"id": "sub_14_2", "number": "14.2", "title": "Switching Triggers & Procurement Barrier Analysis"},
                {"id": "sub_14_3", "number": "14.3", "title": "Ecosystem Integration & Vendor Disruption Vectors"}
            ]
        }
    })

    # Slide 22: Table 14.1 & 14.2 Dashboard
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Supplier Selection, Incumbency Lock-in & Switching Triggers",
            "left_column": [
                {"type": "text", "id": "h_14_1", "role": "heading", "text": "Table 14.1: Supplier Selection & Incumbency Metrics"},
                make_table_block("tbl_14_1", T[20]),
                {
                    "type": "insight",
                    "id": "ins_14_1",
                    "title": "OEM Fleet Relationship Barrier",
                    "body": "Existing machinery supply agreements with Caterpillar, Sandvik, and Komatsu present a 72% barrier to entry for standalone robotics startups."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_14_2", "role": "heading", "text": "Table 14.2: Supplier Switching Triggers & Impact"},
                make_table_block("tbl_14_2", T[21]),
                {
                    "type": "bullet_list",
                    "id": "bl_14_2",
                    "items": [
                        {"id": "b_14_2_1", "text": "Software API openness and integration with mine dispatch is the #1 switching catalyst.", "level": 0},
                        {"id": "b_14_2_2", "text": "Unscheduled downtime exceeding 15% leads to mandatory contract re-tendering.", "level": 0}
                    ]
                }
            ]
        }
    })

    # =============================================================
    # SECTION 17: Pricing, Transaction & Negotiation Intelligence
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "17. Pricing, Transaction & Negotiation Intelligence",
            "index_list": [
                {"id": "sub_17_1", "number": "17.1", "title": "Mining UGV Pricing Benchmarks by Platform Class"},
                {"id": "sub_17_2", "number": "17.2", "title": "Contract Negotiation Factors, Volume Discounts & SLA Margins"},
                {"id": "sub_17_3", "number": "17.3", "title": "Life-Cycle Cost Models: Hardware vs Software Licensing"}
            ]
        }
    })

    # Slide 24: Table 17.1 & 17.2 Dashboard
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Pricing Benchmarks, Transaction Structures & Supplier Margins",
            "left_column": [
                {"type": "text", "id": "h_17_1", "role": "heading", "text": "Table 17.1: Equipment Pricing & Transaction Benchmarks"},
                make_table_block("tbl_17_1", T[22]),
                {
                    "type": "insight",
                    "id": "ins_17_1",
                    "title": "Gross Margin Realization",
                    "body": "Hardware gross margins range from 38-48%, while recurring fleet software and autonomous navigation packages yield 72-84% gross margins."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_17_2", "role": "heading", "text": "Table 17.2: Negotiation Economics & Discounting"},
                make_table_block("tbl_17_2", T[23]),
                {
                    "type": "text",
                    "id": "p_17_2",
                    "role": "paragraph",
                    "text": "Volume discounts scale from 5-8% for 5-9 units, up to 18-24% for enterprise agreements covering 50+ vehicles across global operations."
                }
            ]
        }
    })

    # =============================================================
    # SECTION 19: Purchase Intent & Budget Allocation
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "19. Purchase Intent & Budget Allocation",
            "index_list": [
                {"id": "sub_19_1", "number": "19.1", "title": "Near-Term Purchase Intent & Commercial Readiness"},
                {"id": "sub_19_2", "number": "19.2", "title": "Mining Automation Budget Allocation & Economics"},
                {"id": "sub_19_3", "number": "19.3", "title": "CAPEX vs OPEX Budget Shifts in Sub-Surface Robotics"}
            ]
        }
    })

    # Slide 26: Table 19.1 & 19.2 Dashboard
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Purchase Intent, Budget Allocation & Commercial Velocity",
            "left_column": [
                {"type": "text", "id": "h_19_1", "role": "heading", "text": "Table 19.1: Purchase Intent & Pipeline Velocity"},
                make_table_block("tbl_19_1", T[24]),
                {
                    "type": "insight",
                    "id": "ins_19_1",
                    "title": "Fast-Track Procurement Mandates",
                    "body": "68% of surveyed operations have dedicated capital envelopes for underground robotics under general digital transformation budgets."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_19_2", "role": "heading", "text": "Table 19.2: Budget Category Allocation"},
                make_table_block("tbl_19_2", T[25]),
                {
                    "type": "bullet_list",
                    "id": "bl_19_2",
                    "items": [
                        {"id": "b_19_2_1", "text": "Vehicle chassis and payload sensors consume 55% of initial project budgets.", "level": 0},
                        {"id": "b_19_2_2", "text": "Underground communications infrastructure accounts for 18-25% of installation expenditure.", "level": 0}
                    ]
                }
            ]
        }
    })

    # =============================================================
    # SECTION 21: Technology Trial & Adoption Pipeline
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "21. Technology Trial & Adoption Pipeline",
            "index_list": [
                {"id": "sub_21_1", "number": "21.1", "title": "Technology Adoption Funnel & Conversion Chasm"},
                {"id": "sub_21_2", "number": "21.2", "title": "Solution Readiness: SLAM, AI Perception, Fleet Swarming"},
                {"id": "sub_21_3", "number": "21.3", "title": "Active Trial Programs by Mine Operator Tier"}
            ]
        }
    })

    # Slide 28: Table 21.1 + Chart
    slides.append({
        "template_id": "04_table_chart",
        "slide_index": len(slides),
        "data": {
            "context_note": "Conversion metrics and active programs across the commercial mining UGV adoption lifecycle",
            "chart": {
                "type": "chart",
                "id": "ch_adopt_21_1",
                "chart_type": "column_clustered",
                "title": "Active Commercial Programs & Pipeline Value ($M)",
                "categories": ["Screening", "POC", "Prototype", "Mine Pilot", "Production", "Fleet Expansion"],
                "series": [
                    {"name": "Active Programs Midpoint", "values": [150.0, 80.0, 55.0, 35.0, 12.0, 8.0]},
                    {"name": "Program Value Midpoint ($M)", "values": [42.0, 32.0, 25.0, 22.0, 10.0, 15.0]}
                ]
            },
            "heading": "Adoption Funnel & Conversion Chasm",
            "narrative": "Over 200 programs are actively evaluating UGVs. The critical commercial hurdle occurs between POC and mine pilot (35-50% conversion), where systems must prove communications and environmental resilience.",
            "table": make_table_block("tbl_21_1", T[26]),
            "insight": {
                "type": "insight",
                "id": "ins_adopt_21_1",
                "title": "KEY INSIGHT: USD 83M-207M Identifiable Pipeline",
                "body": "Identified near-term programs encompass 650-1,220 prospective UGV units representing $83M-$207M in equipment and software procurement through 2027."
            }
        }
    })

    # Slide 29: Table 21.2 Large Table
    slides.append({
        "template_id": "06_large_table",
        "slide_index": len(slides),
        "data": {
            "title": "Table 21.2: Technology Adoption by Solution & Commercial Readiness",
            "table": make_table_block("tbl_21_2", T[27])
        }
    })

    # =============================================================
    # SECTION 25: Near-Term Demand Pipeline (2026-2027)
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "25. Near-Term Demand Pipeline (2026-2027)",
            "index_list": [
                {"id": "sub_25_1", "number": "25.1", "title": "Near-Term Demand Pipeline by Qualification Stage"},
                {"id": "sub_25_2", "number": "25.2", "title": "Purchase Signals by Application & Mine Type"},
                {"id": "sub_25_3", "number": "25.3", "title": "Commercial Tender Pipeline & Unit Forecast"}
            ]
        }
    })

    # Slide 31: Table 25.1 & 25.2 Dashboard
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Near-Term Demand Pipeline, Purchase Signals & Commercial Stages",
            "left_column": [
                {"type": "text", "id": "h_25_1", "role": "heading", "text": "Table 25.1: Demand Pipeline by Qualification Stage"},
                make_table_block("tbl_25_1", T[28]),
                {
                    "type": "insight",
                    "id": "ins_25_1",
                    "title": "Imminent Purchase Envelopes",
                    "body": "Stage 4 and Stage 5 tenders represent over 420 committed vehicle procurement contracts across Australia, Canada, and Scandinavia."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_25_2", "role": "heading", "text": "Table 25.2: Purchase Signals by Application"},
                make_table_block("tbl_25_2", T[29]),
                {
                    "type": "bullet_list",
                    "id": "bl_25_2",
                    "items": [
                        {"id": "b_25_2_1", "text": "Block caving and sublevel stoping mines exhibit the highest purchase intent scores.", "level": 0},
                        {"id": "b_25_2_2", "text": "Average tender timeline has compressed from 18 months to 9 months for inspection robots.", "level": 0}
                    ]
                }
            ]
        }
    })

    # =============================================================
    # SECTION 26: Regional Intelligence: Europe & Germany
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "26. Regional Intelligence: Europe & Germany",
            "index_list": [
                {"id": "sub_26_1", "number": "26.1", "title": "European Mining UGV Market: Size, Share & Growth (2024-2030)"},
                {"id": "sub_26_2", "number": "26.2", "title": "European Segmentation & Demand Concentration"},
                {"id": "sub_26_3", "number": "26.3", "title": "Germany Deep Dive: Salt, Potash & Critical Raw Materials"},
                {"id": "sub_26_4", "number": "26.4", "title": "Germany Buyer Profile, Technology Adoption & Commercial Intelligence"},
                {"id": "sub_26_5", "number": "26.5", "title": "Strategic Position: German Tunneling OEMs & Academic Robotics"}
            ]
        }
    })

    # Slide 33: Table 26.1 & 26.2 Dashboard
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "European Market Intelligence: Sizing, Growth & Segmentation",
            "left_column": [
                {"type": "text", "id": "h_26_1", "role": "heading", "text": "Table 26.1: Europe Market Size & Forecast"},
                make_table_block("tbl_26_1", T[30]),
                {
                    "type": "insight",
                    "id": "ins_26_1",
                    "title": "Strict Safety Standards",
                    "body": "EU machinery directives and ATEX explosive atmosphere mandates accelerate zero-emission autonomous UGV requirements."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_26_2", "role": "heading", "text": "Table 26.2: Europe Demand Concentration & Signals"},
                make_table_block("tbl_26_2", T[31]),
                make_table_block("tbl_26_2b", T[32])
            ]
        }
    })

    # Slide 34: Table 26.3 & 26.4 Dashboard (Germany)
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Germany Country Deep Dive: Market Sizing & Buyer Profiles",
            "left_column": [
                {"type": "text", "id": "h_26_3", "role": "heading", "text": "Table 26.3: Germany Market Data & Growth"},
                make_table_block("tbl_26_3", T[33]),
                {
                    "type": "insight",
                    "id": "ins_26_3",
                    "title": "German Potash & Salt Automation",
                    "body": "Potash extraction in Hessen and Thuringia accounts for >45% of Germany's active sub-surface mobile robotics testing programs."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_26_4", "role": "heading", "text": "Table 26.4: Germany Commercial & Buyer Intelligence"},
                make_table_block("tbl_26_4", T[34])
            ]
        }
    })

    # Slide 35: Table 26.5 Dashboard (Germany Strategic Position)
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Germany Strategic Ecosystem Position & Sub-Surface Automation",
            "left_column": [
                {"type": "text", "id": "h_26_5", "role": "heading", "text": "Table 26.5: Germany Strategic Position Metrics"},
                make_table_block("tbl_26_5", T[35]),
                {
                    "type": "insight",
                    "id": "ins_26_5",
                    "title": "Engineering Precision & Tunneling Heritage",
                    "body": "Germany's deep civil tunneling and specialized mining engineering hubs provide ideal testbeds for heavy-payload autonomous platforms."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_26_5_synth", "role": "heading", "text": "European Expansion Priorities"},
                {"type": "text", "id": "p_26_5", "role": "paragraph", "text": "Suppliers entering the German market must establish local technical integration teams and provide bilingual ATEX certification documentation conforming to DIN EN 1710 standards."},
                {
                    "type": "bullet_list",
                    "id": "bl_26_5",
                    "items": [
                        {"id": "b_26_5_1", "text": "Direct partnerships with German industrial sensor suppliers (SICK, Pepperl+Fuchs).", "level": 0},
                        {"id": "b_26_5_2", "text": "Integration with legacy Profibus and modern OPC UA industrial protocols.", "level": 0}
                    ]
                }
            ]
        }
    })

    # =============================================================
    # SECTION 32: Customer-Validated White-Space Opportunity Matrix
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "32. Customer-Validated Opportunity & White-Space Matrix",
            "index_list": [
                {"id": "sub_32_1", "number": "32.1", "title": "Customer-Validated Opportunity & White-Space Matrix"},
                {"id": "sub_32_2", "number": "32.2", "title": "Customer-Validated Gaps & Commercial Growth Opportunities"},
                {"id": "sub_32_3", "number": "32.3", "title": "Strategic White-Space Roadmap for Market Challengers"}
            ]
        }
    })

    # Slide 37: Table 32.1 Large Table
    slides.append({
        "template_id": "06_large_table",
        "slide_index": len(slides),
        "data": {
            "title": "Table 32.1: Customer-Validated Opportunity & White-Space Matrix",
            "table": make_table_block("tbl_32_1", T[36])
        }
    })

    # Slide 38: Table 32.2 Large Table
    slides.append({
        "template_id": "06_large_table",
        "slide_index": len(slides),
        "data": {
            "title": "Table 32.2: Customer-Validated Gaps & Commercial Opportunity",
            "table": make_table_block("tbl_32_2", T[37])
        }
    })

    # =============================================================
    # SECTION 35: Company Benchmarking: Komatsu Ltd.
    # =============================================================
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": len(slides),
        "data": {
            "section_title": "35. Company Benchmarking: Komatsu Ltd.",
            "index_list": [
                {"id": "sub_35_1", "number": "35.1", "title": "Company Overview & Mining Financial Profile"},
                {"id": "sub_35_2", "number": "35.2", "title": "Mining Business Division & Autonomous Platform (FrontRunner)"},
                {"id": "sub_35_3", "number": "35.3", "title": "Products, Brands & Technology Portfolio"},
                {"id": "sub_35_4", "number": "35.4", "title": "Autonomous Fleet Metrics & Market Share Estimates"},
                {"id": "sub_35_5", "number": "35.5", "title": "Non-Public Competitive Intelligence & Procurement Benchmarks"},
                {"id": "sub_35_6", "number": "35.6", "title": "Competitive Positioning in Mining Underground Vehicles"}
            ]
        }
    })

    # Slide 40: Table 35.1 & 35.2 Dashboard
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Komatsu Ltd. Financial Profile & Mining Business Division",
            "left_column": [
                {"type": "text", "id": "h_35_1", "role": "heading", "text": "Table 35.1: Company Overview & Financial Profile"},
                make_table_block("tbl_35_1", T[38]),
                {
                    "type": "insight",
                    "id": "ins_35_1",
                    "title": "Massive Mining Revenue Base",
                    "body": "Mining equipment generated ¥1,480B (~USD 10.2B) in FY2024, representing 42% of Komatsu's total corporate revenues."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_35_2", "role": "heading", "text": "Table 35.2: Mining Business Breakdown"},
                make_table_block("tbl_35_2", T[39])
            ]
        }
    })

    # Slide 41: Table 35.3 & 35.4 Dashboard
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Komatsu Autonomous Platform (FrontRunner) & Product Portfolio",
            "left_column": [
                {"type": "text", "id": "h_35_3", "role": "heading", "text": "Table 35.3: Autonomous Mining Platform"},
                make_table_block("tbl_35_3", T[40]),
                {
                    "type": "insight",
                    "id": "ins_35_3",
                    "title": "Over 750 Autonomous Trucks Deployed",
                    "body": "FrontRunner has hauled over 7.5 billion tonnes autonomously, providing Komatsu unparalleled fleet telemetry and AI control systems."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_35_4", "role": "heading", "text": "Table 35.4: Brands & Technology Portfolio"},
                make_table_block("tbl_35_4", T[41])
            ]
        }
    })

    # Slide 42: Table 35.5 & 35.6 Dashboard
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Komatsu Fleet Estimates & Non-Public Intelligence",
            "left_column": [
                {"type": "text", "id": "h_35_5", "role": "heading", "text": "Table 35.5: UGV Fleet Estimates"},
                make_table_block("tbl_35_5", T[42]),
                {
                    "type": "insight",
                    "id": "ins_35_5",
                    "title": "Underground UGV Transition",
                    "body": "Komatsu is actively retrofitting its underground loader (LHD) line with Modular Mining DISPATCH autonomy kits."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_35_6", "role": "heading", "text": "Table 35.6: Non-Public Strategic Intelligence"},
                make_table_block("tbl_35_6", T[43])
            ]
        }
    })

    # Slide 43: Table 35.7 & 35.8 Dashboard
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": len(slides),
        "data": {
            "title": "Customer Procurement Intelligence & Competitive Positioning",
            "left_column": [
                {"type": "text", "id": "h_35_7", "role": "heading", "text": "Table 35.7: Customer & Procurement Intelligence"},
                make_table_block("tbl_35_7", T[44]),
                {
                    "type": "insight",
                    "id": "ins_35_7",
                    "title": "Master Service Agreement Lock-in",
                    "body": "Komatsu's long-term full-maintenance contracts lock out 3rd party autonomy vendors unless open API integration is mandated."
                }
            ],
            "right_column": [
                {"type": "text", "id": "h_35_8", "role": "heading", "text": "Table 35.8: Competitive Capability Matrix"},
                make_table_block("tbl_35_8", T[45])
            ]
        }
    })

    # =============================================================
    # SLIDE 44: Strategic Recommendations & 2030 Roadmap
    # =============================================================
    slides.append({
        "template_id": "05_insight_information",
        "slide_index": len(slides),
        "data": {
            "title": "Strategic Recommendations & 2030 Commercialization Roadmap",
            "left_column": [
                {"type": "text", "id": "t_road_left_h", "role": "heading", "text": "Near-Term Priorities (0-18 Months)"},
                {"type": "text", "id": "t_road_left_p", "role": "paragraph", "text": "Suppliers must bridge the trial-to-production chasm by delivering validated reliability in harsh sub-surface environments rather than marketing standalone hardware."},
                {
                    "type": "bullet_list",
                    "id": "bl_road_left",
                    "items": [
                        {"id": "b_rl_1", "text": "Deploy multi-modal LiDAR + Visual SLAM to eliminate GNSS reliance in drift headings.", "level": 0},
                        {"id": "b_rl_2", "text": "Provide plug-and-play retrofit kits for existing light utility vehicles to accelerate entry.", "level": 0},
                        {"id": "b_rl_3", "text": "Establish regional field depots in primary mining hubs (Perth, Sudbury, Antofagasta, Essen).", "level": 0}
                    ]
                }
            ],
            "right_column": [
                {"type": "text", "id": "t_road_right_h", "role": "heading", "text": "Long-Term Scalability (18-36 Months)"},
                {"type": "text", "id": "t_road_right_p", "role": "paragraph", "text": "Sustainable competitive advantage will center on digital mine integration, centralized fleet orchestration software, and predictive maintenance algorithms."},
                {
                    "type": "insight",
                    "id": "ins_road_right",
                    "title": "KEY INSIGHT: Integrated Fleet Solution Imperative",
                    "body": "The winning 2030 business model integrates ruggedized IP68 hardware with recurring fleet management software, edge AI defect detection, and full mine safety compliance."
                }
            ]
        }
    })

    full_report_manifest = {
        "report_id": "rep_mining_ugv_full_2026",
        "title": "Mining Underground Ground Vehicles (UGV) Market",
        "created_at": "2026-09-18T12:00:00Z",
        "template_set": "mining_ugv",
        "defaults": {
            "background": "bg_02.png",
            "font_family": "Arial",
            "accent_color": "#0D3166"
        },
        "slides": slides
    }

    out_path = "examples/mining_ugv_full_email_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(full_report_manifest, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Successfully generated full canonical report manifest!")
    print(f"Manifest path: {out_path}")
    print(f"Total Slides: {len(slides)}")


if __name__ == "__main__":
    build_full_report()
