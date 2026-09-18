"""
build_email_report_json.py
Parses source_email.html and generates a complete, canonical report JSON manifest
(examples/mining_ugv_email_report.json) using real data from the source email.
"""

import json
import re
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


def build_report():
    print("Reading source_email.html...")
    with open("source_email.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    tables = soup.find_all("table")
    print(f"Parsed {len(tables)} tables from HTML.")

    # Extract required tables
    t4 = extract_table(tables[4])   # Table 1.1 Market Snapshot
    t6 = extract_table(tables[6])   # Table 1.3 Application Demand
    t8 = extract_table(tables[8])   # Table 1.5 Buyer Requirements
    t12 = extract_table(tables[12]) # Table 3.1 Historical Development
    t14 = extract_table(tables[14]) # Table 4.1 Market Structure
    t15 = extract_table(tables[15]) # Table 8.1 Application Intelligence
    t18 = extract_table(tables[18]) # Table 11.1 Technical Requirements
    t19 = extract_table(tables[19]) # Table 11.2 Customer-Validated Requirements
    t22 = extract_table(tables[22]) # Table 17.1 Pricing Benchmarks
    t23 = extract_table(tables[23]) # Table 17.2 Negotiation Factors
    t26 = extract_table(tables[26]) # Table 21.1 Adoption Funnel
    t30 = extract_table(tables[30]) # Table 26.1 Europe Market Data
    t33 = extract_table(tables[33]) # Table 26.3 Germany Market Data
    t36 = extract_table(tables[36]) # Table 32.1 White Space Matrix
    t38 = extract_table(tables[38]) # Table 35.1 Komatsu Financials
    t40 = extract_table(tables[40]) # Table 35.2 Komatsu Fleet Metrics

    slides = []

    # -------------------------------------------------------------
    # SLIDE 1: Cover Title with Image (01_cover_title_image)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "01_cover_title_image",
        "slide_index": 0,
        "data": {
            "title": {
                "type": "text",
                "id": "cov_title",
                "value": "Mining Underground Ground Vehicles (UGV) Market"
            },
            "subtitle": {
                "type": "text",
                "id": "cov_sub",
                "value": "Global Fleet Sizing, Autonomous Navigation & Commercial Forecast 2020-2030F"
            },
            "metadata": {
                "type": "text",
                "id": "cov_meta",
                "value": "Industry Intelligence Report | Source: Comprehensive Mining Research | September 2026"
            }
        }
    })

    # -------------------------------------------------------------
    # SLIDE 2: Table of Contents (02_toc_image) - 18 items
    # -------------------------------------------------------------
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
        "slide_index": 1,
        "data": {
            "items": [
                {
                    "type": "toc_item",
                    "id": f"toc_{i+1:02d}",
                    "number": f"{i+1:02d}",
                    "title": t
                } for i, t in enumerate(toc_titles)
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 3: Section 1 Opener (03_section_opener)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": 2,
        "data": {
            "section_title": {
                "type": "text",
                "id": "s1_title",
                "value": "1. Executive Summary & Strategic Findings"
            },
            "index_list": [
                {"type": "index_item", "id": "sub_1_1", "number": "1.1", "title": "Market Snapshot & Growth Trajectory"},
                {"type": "index_item", "id": "sub_1_2", "number": "1.2", "title": "Demand & Near-Term Purchase Pipeline"},
                {"type": "index_item", "id": "sub_1_3", "number": "1.3", "title": "Application Demand & Fleet Economics"},
                {"type": "index_item", "id": "sub_1_4", "number": "1.4", "title": "Critical Buyer Specifications & Thresholds"},
                {"type": "index_item", "id": "sub_1_5", "number": "1.5", "title": "Core Technology Adoption Dynamics"},
                {"type": "index_item", "id": "sub_1_6", "number": "1.6", "title": "Strategic Market Opportunities & White-Space"}
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 4: Market Snapshot (04_table_chart)
    # -------------------------------------------------------------
    snap_headers = t4[0]
    snap_rows = t4[1:5]
    slides.append({
        "template_id": "04_table_chart",
        "slide_index": 3,
        "data": {
            "context_note": {
                "type": "text",
                "id": "s4_note",
                "value": "Comprehensive market valuation and fleet growth across forecast horizons (2025-2030F)"
            },
            "chart": {
                "type": "chart",
                "id": "ch_s4_val",
                "chart_type": "bar",
                "title": "Mining UGV Market Value ($M) & Annual Deployments (Units)",
                "data": {
                    "categories": ["2025", "2026E", "2030F"],
                    "series": [
                        {"name": "Market Value Midpoint ($M)", "values": [220, 270, 650]},
                        {"name": "Deployments Midpoint (Units)", "values": [1350, 1750, 4500]}
                    ]
                }
            },
            "section_heading": {
                "type": "text",
                "id": "s4_head",
                "value": "Market Acceleration & Underground Share"
            },
            "narrative": {
                "type": "text",
                "id": "s4_narr",
                "value": "Underground operations account for 60-72% of total UGV demand, expanding at an 18-23% CAGR. Market value is projected to reach $520-780M by 2030 as operators transition from single-vehicle trials to multi-unit fleet production."
            },
            "table": {
                "type": "table",
                "id": "tbl_s4_snap",
                "headers": snap_headers,
                "rows": snap_rows
            },
            "supporting_insight": {
                "type": "insight",
                "id": "ins_s4_snap",
                "blocks": [
                    {
                        "id": "ins_s4_snap_b",
                        "title": "Worker Safety Driving CAPEX Budgets",
                        "body": "Worker exposure reduction ranks as the #1 purchase trigger (18-24% weighting), far exceeding initial equipment price (4-7%), compelling rapid fleet automation in hazardous stopes."
                    }
                ]
            }
        }
    })

    # -------------------------------------------------------------
    # SLIDE 5: Strategic Findings & Customer Pain Points (05_insight_information)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "05_insight_information",
        "slide_index": 4,
        "data": {
            "title": {
                "type": "text",
                "id": "s5_title",
                "value": "Strategic Market Findings & Structural Buyer Dynamics"
            },
            "left_column": [
                {
                    "type": "text",
                    "id": "s5_l_h",
                    "value": "Key Commercial Transition Vectors",
                    "role": "heading"
                },
                {
                    "type": "text",
                    "id": "s5_l_p",
                    "value": "Underground mining represents the primary near-term commercial market. While inspection and mapping are the dominant initial entry points, safety, hazardous-area intervention, and production-support systems are expanding at the fastest CAGR."
                },
                {
                    "type": "bullet_list",
                    "id": "s5_l_b",
                    "items": [
                        {"id": "s5_l_b_1", "text": "Pilot conversion is the principal bottleneck: 35-55% of mine pilots convert to commercial contracts."},
                        {"id": "s5_l_b_2", "text": "Retrofit autonomy kits offer a faster, lower-CAPEX route than complete machinery replacement."},
                        {"id": "s5_l_b_3", "text": "Multi-unit fleet deployments (10-50+ units) trigger massive operational economies of scale."}
                    ]
                }
            ],
            "right_column": [
                {
                    "type": "text",
                    "id": "s5_r_h",
                    "value": "Value Shift: Hardware to Software & AI",
                    "role": "heading"
                },
                {
                    "type": "text",
                    "id": "s5_r_p",
                    "value": "Technology differentiation is decisively shifting away from vehicle chassis mechanics toward GNSS-denied autonomy, multi-sensor fusion, edge AI inference, and deep integration with mine management systems."
                },
                {
                    "type": "insight",
                    "id": "s5_r_ins",
                    "blocks": [
                        {
                            "id": "s5_r_ins_b",
                            "title": "Expanded Revenue Beyond Hardware",
                            "body": "Software licenses, sensor payloads, communications infrastructure, and centralized fleet management software expand total deployment revenue by 30-50% over bare vehicle hardware."
                        }
                    ]
                }
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 6: Section 3 Opener (03_section_opener)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": 5,
        "data": {
            "section_title": {
                "type": "text",
                "id": "s6_title",
                "value": "3. Historical Development & Market Sizing (2020-2030F)"
            },
            "index_list": [
                {"type": "index_item", "id": "sub_3_1", "number": "3.1", "title": "Historical Market Value & Annual Deployments"},
                {"type": "index_item", "id": "sub_3_2", "number": "3.2", "title": "Installed Fleet Expansion (2,400 to 18,000 Units)"},
                {"type": "index_item", "id": "sub_3_3", "number": "3.3", "title": "System ASP Compression & Pricing Trends"},
                {"type": "index_item", "id": "sub_3_4", "number": "3.4", "title": "New Deployments vs Retrofit Share Evolution"},
                {"type": "index_item", "id": "sub_3_5", "number": "3.5", "title": "Shift from Pilot Programs to Commercial Fleets"}
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 7: Historical Development Large Table (06_large_table)
    # -------------------------------------------------------------
    t12_headers = t12[0]
    t12_rows = t12[1:]
    slides.append({
        "template_id": "06_large_table",
        "slide_index": 6,
        "data": {
            "table_title": {
                "type": "text",
                "id": "s7_title",
                "value": "Table 3.1: Historical Market Development & Fleet Sizing (2020-2030F)"
            },
            "table": {
                "type": "table",
                "id": "tbl_s7_hist",
                "headers": t12_headers,
                "rows": t12_rows
            }
        }
    })

    # -------------------------------------------------------------
    # SLIDE 8: Growth Trajectory Line Chart (07_large_chart)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "07_large_chart",
        "slide_index": 7,
        "data": {
            "chart_title": {
                "type": "text",
                "id": "s8_title",
                "value": "Mining UGV Market Trajectory & Fleet Installed Base (2020-2030F)"
            },
            "chart": {
                "type": "chart",
                "id": "ch_s8_traj",
                "chart_type": "line",
                "title": "Global Market Valuation ($M), Annual Shipments (x10), and Installed Base (x100)",
                "data": {
                    "categories": ["2020", "2021", "2022", "2023", "2024", "2025", "2026E", "2030F"],
                    "series": [
                        {"name": "Market Value Midpoint ($M)", "values": [125, 137, 150, 167, 190, 220, 270, 650]},
                        {"name": "Annual Deployments (x10 Units)", "values": [80, 87, 96, 105, 117, 135, 175, 450]},
                        {"name": "Installed Fleet Base (x100 Units)", "values": [29, 33, 37, 41, 45, 50, 62, 150]}
                    ]
                }
            }
        }
    })

    # -------------------------------------------------------------
    # SLIDE 9: Section 4 Opener (03_section_opener)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": 8,
        "data": {
            "section_title": {
                "type": "text",
                "id": "s9_title",
                "value": "4. Market Structure & Core Segmentation Analysis"
            },
            "index_list": [
                {"type": "index_item", "id": "sub_4_1", "number": "4.1", "title": "UGV Type: Inspection, Mapping & Heavy Transport"},
                {"type": "index_item", "id": "sub_4_2", "number": "4.2", "title": "Autonomy Levels: Teleoperation to Full Autonomy"},
                {"type": "index_item", "id": "sub_4_3", "number": "4.3", "title": "Platform Sizing & Weight Distribution"},
                {"type": "index_item", "id": "sub_4_4", "number": "4.4", "title": "Payload Capacity & System ASP Benchmarking"},
                {"type": "index_item", "id": "sub_4_5", "number": "4.5", "title": "Propulsion: Wheeled, Tracked & Legged Robotics"}
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 10: Market Structure Large Table (06_large_table)
    # -------------------------------------------------------------
    t14_headers = t14[0]
    clean_t14_rows = []
    curr_dim = ""
    for r in t14[1:]:
        dim = r[0] if r[0] else curr_dim
        curr_dim = dim
        clean_t14_rows.append([dim, r[1], r[2], r[3], r[4], r[5]])

    slides.append({
        "template_id": "06_large_table",
        "slide_index": 9,
        "data": {
            "table_title": {
                "type": "text",
                "id": "s10_title",
                "value": "Table 4.1: Mining UGV Market Structure & Core Segmentation (2025)"
            },
            "table": {
                "type": "table",
                "id": "tbl_s10_struct",
                "headers": t14_headers,
                "rows": clean_t14_rows
            }
        }
    })

    # -------------------------------------------------------------
    # SLIDE 11: Section 8 Opener (03_section_opener)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": 10,
        "data": {
            "section_title": {
                "type": "text",
                "id": "s11_title",
                "value": "8. Application & End-User Intelligence"
            },
            "index_list": [
                {"type": "index_item", "id": "sub_8_1", "number": "8.1", "title": "Mine Inspection & 3D Mapping Operations"},
                {"type": "index_item", "id": "sub_8_2", "number": "8.2", "title": "Hazardous Area & Safety Inspection Demand"},
                {"type": "index_item", "id": "sub_8_3", "number": "8.3", "title": "Material Transport & Autonomous Haulage"},
                {"type": "index_item", "id": "sub_8_4", "number": "8.4", "title": "End-User Fleet Economics & Budget Thresholds"},
                {"type": "index_item", "id": "sub_8_5", "number": "8.5", "title": "Mining Contractors vs Mine Owners Adoption"}
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 12: Application Intelligence (04_table_chart)
    # -------------------------------------------------------------
    t15_headers = [t15[0][0], t15[0][1], t15[0][4], t15[0][6]]
    t15_rows = [[r[0], r[1], r[4], r[6]] for r in t15[1:6]]
    slides.append({
        "template_id": "04_table_chart",
        "slide_index": 11,
        "data": {
            "context_note": {
                "type": "text",
                "id": "s12_note",
                "value": "Relative share and growth velocity across primary underground UGV operational missions"
            },
            "chart": {
                "type": "chart",
                "id": "ch_s12_apps",
                "chart_type": "bar",
                "title": "Application Market Share Comparison (2025 vs 2030F)",
                "data": {
                    "categories": ["Mine Inspection", "3D Mapping", "Safety Ops", "Infrastructure", "Env Monitoring", "Material Transport"],
                    "series": [
                        {"name": "2025 Share (%)", "values": [22.5, 17.5, 14.5, 12.5, 10.0, 10.0]},
                        {"name": "2030F Share (%)", "values": [20.0, 14.0, 17.0, 15.0, 12.0, 12.5]}
                    ]
                }
            },
            "section_heading": {
                "type": "text",
                "id": "s12_head",
                "value": "High-Velocity Operational Use Cases"
            },
            "narrative": {
                "type": "text",
                "id": "s12_narr",
                "value": "Mine inspection and mapping represent the primary volume base, but hazardous-area safety inspection and material transport are expanding fastest (21-29% CAGR), driven by direct human hazard removal."
            },
            "table": {
                "type": "table",
                "id": "tbl_s12_apps",
                "headers": t15_headers,
                "rows": t15_rows
            },
            "supporting_insight": {
                "type": "insight",
                "id": "ins_s12_apps",
                "blocks": [
                    {
                        "id": "ins_s12_apps_b",
                        "title": "Autonomous Sampling Expansion",
                        "body": "Specialized sampling and explosive-zone inspection UGVs show the highest growth rate at 25-32% CAGR, as mines enforce total non-entry in blast clearance zones."
                    }
                ]
            }
        }
    })

    # -------------------------------------------------------------
    # SLIDE 13: Section 11 Opener (03_section_opener)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": 12,
        "data": {
            "section_title": {
                "type": "text",
                "id": "s13_title",
                "value": "11. Customer Requirements & Specifications"
            },
            "index_list": [
                {"type": "index_item", "id": "sub_11_1", "number": "11.1", "title": "Technical Specs across UGV Platform Classes"},
                {"type": "index_item", "id": "sub_11_2", "number": "11.2", "title": "Validated Specification Thresholds"},
                {"type": "index_item", "id": "sub_11_3", "number": "11.3", "title": "GNSS-Denied Navigation & SLAM Standards"},
                {"type": "index_item", "id": "sub_11_4", "number": "11.4", "title": "Environmental Protection: IP65 to IP68"},
                {"type": "index_item", "id": "sub_11_5", "number": "11.5", "title": "Mine Network Integration & Communications"}
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 14: Two-Column Dashboard: Specs & Thresholds (08_multi_table_dashboard_2col)
    # -------------------------------------------------------------
    t18_headers = ["Specification", "Compact", "Medium", "Heavy-Duty", "2030 Exp"]
    t18_rows = [
        ["Vehicle weight", "20-80 kg", "80-500 kg", "500-2,000+ kg", "30-1,500 kg"],
        ["Payload capacity", "5-30 kg", "30-250 kg", "250-1,000+ kg", "10-1,000 kg"],
        ["Operating speed", "3-8 km/h", "5-15 km/h", "8-30 km/h", "5-30 km/h"],
        ["Runtime", "4-10 h", "6-14 h", "6-16 h", "8-24 h"],
        ["IP protection", "IP54-IP67", "IP65-IP68", "IP65-IP68", "IP67-IP69K"],
        ["Nav accuracy", "5-20 cm", "5-20 cm", "5-30 cm", "2-10 cm"]
    ]
    t19_headers = ["Requirement", "Buyers %", "Min Threshold", "Preferred Spec"]
    t19_rows = [
        ["Worker-safe remote op", "75-90%", "Remote control", "Autonomous fallback"],
        ["Autonomous navigation", "65-80%", "Semi-autonomous", "Highly autonomous"],
        ["GNSS-denied nav", "55-75%", "Basic localiz.", "LiDAR + Visual SLAM"],
        ["Collision avoidance", "65-80%", "Obstacle detect", "Predictive avoidance"],
        ["8+ hour runtime", "45-65%", "6 hours", "8-12+ hours"],
        ["Mine network integration", "60-75%", "Wi-Fi / Mesh", "Private LTE / 5G"]
    ]
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": 13,
        "data": {
            "title": {
                "type": "text",
                "id": "s14_title",
                "value": "Technical Specifications by UGV Class & Buyer Requirement Thresholds"
            },
            "left_column": [
                {
                    "type": "text",
                    "id": "s14_l_h",
                    "value": "Table 11.1: Platform Class Technical Specifications",
                    "role": "heading"
                },
                {
                    "type": "table",
                    "id": "tbl_s14_specs",
                    "headers": t18_headers,
                    "rows": t18_rows
                },
                {
                    "type": "text",
                    "id": "s14_l_p",
                    "value": "Vehicle endurance and environmental ruggedness requirements intensify as platforms scale from man-portable inspection scouts to autonomous haulage platforms."
                }
            ],
            "right_column": [
                {
                    "type": "text",
                    "id": "s14_r_h",
                    "value": "Table 11.2: Validated Specification Thresholds",
                    "role": "heading"
                },
                {
                    "type": "table",
                    "id": "tbl_s14_thresh",
                    "headers": t19_headers,
                    "rows": t19_rows
                },
                {
                    "type": "insight",
                    "id": "ins_s14_thresh",
                    "blocks": [
                        {
                            "id": "ins_s14_thresh_b",
                            "title": "GNSS-Denied Localization is Critical",
                            "body": "Over 75% of underground operators view multi-sensor SLAM (LiDAR + visual + IMU) as mandatory for commercial production acceptance."
                        }
                    ]
                }
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 15: Section 17 Opener (03_section_opener)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": 14,
        "data": {
            "section_title": {
                "type": "text",
                "id": "s15_title",
                "value": "17. Pricing, Transaction & Negotiation Intelligence"
            },
            "index_list": [
                {"type": "index_item", "id": "sub_17_1", "number": "17.1", "title": "UGV Platform & Subsystem Pricing Benchmarks"},
                {"type": "index_item", "id": "sub_17_2", "number": "17.2", "title": "Sensor Package & Autonomy Software Pricing"},
                {"type": "index_item", "id": "sub_17_3", "number": "17.3", "title": "Volume Discount Schedules & Bundling Economics"},
                {"type": "index_item", "id": "sub_17_4", "number": "17.4", "title": "Distributor & System-Integrator Margins"},
                {"type": "index_item", "id": "sub_17_5", "number": "17.5", "title": "Total Cost of Ownership (TCO) & Payback Targets"}
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 16: Two-Column Dashboard: Pricing & Negotiation (08_multi_table_dashboard_2col)
    # -------------------------------------------------------------
    t22_headers = ["Pricing / Transaction Metric", "Market Range"]
    t22_rows = [
        ["Compact inspection UGV ASP", "USD 50K-120K"],
        ["Medium mining UGV ASP", "USD 120K-250K"],
        ["Heavy-duty mining UGV ASP", "USD 250K-750K+"],
        ["LiDAR / sensor package", "USD 15K-80K"],
        ["Autonomy navigation software", "USD 10K-60K"],
        ["Site integration / commissioning", "USD 10K-100K"]
    ]
    t23_headers = ["Negotiation Variable", "Typical Range / Impact"]
    t23_rows = [
        ["Volume discount - 5-10 units", "5-10%"],
        ["Volume discount - 10-25 units", "10-18%"],
        ["Volume discount - 25+ units", "15-25%"],
        ["Technical performance weighting", "20-30%"],
        ["Reliability / uptime weighting", "15-25%"],
        ["Equipment price weighting", "10-20%"]
    ]
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": 15,
        "data": {
            "title": {
                "type": "text",
                "id": "s16_title",
                "value": "Pricing Benchmarks, Transaction Structures & Supplier Selection Weights"
            },
            "left_column": [
                {
                    "type": "text",
                    "id": "s16_l_h",
                    "value": "Table 17.1: Equipment & Subsystem Pricing",
                    "role": "heading"
                },
                {
                    "type": "table",
                    "id": "tbl_s16_price",
                    "headers": t22_headers,
                    "rows": t22_rows
                },
                {
                    "type": "text",
                    "id": "s16_l_p",
                    "value": "Sensors and autonomy software represent up to 45% of complete vehicle deployment value, offering recurring annual software license revenue."
                }
            ],
            "right_column": [
                {
                    "type": "text",
                    "id": "s16_r_h",
                    "value": "Table 17.2: Volume Discounts & Decision Weights",
                    "role": "heading"
                },
                {
                    "type": "table",
                    "id": "tbl_s16_neg",
                    "headers": t23_headers,
                    "rows": t23_rows
                },
                {
                    "type": "insight",
                    "id": "ins_s16_neg",
                    "blocks": [
                        {
                            "id": "ins_s16_neg_b",
                            "title": "Uptime Outweighs Upfront Price",
                            "body": "Initial purchase price carries only 10-20% weight in final supplier selection. Demonstrated uptime, mine integration, and local support network command 60%+ combined weight."
                        }
                    ]
                }
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 17: Section 21 Opener (03_section_opener)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": 16,
        "data": {
            "section_title": {
                "type": "text",
                "id": "s17_title",
                "value": "21. Technology Trial & Adoption Pipeline"
            },
            "index_list": [
                {"type": "index_item", "id": "sub_21_1", "number": "21.1", "title": "Technology Screening & Evaluation Programs"},
                {"type": "index_item", "id": "sub_21_2", "number": "21.2", "title": "Proof-of-Concept (POC) Conversion Dynamics"},
                {"type": "index_item", "id": "sub_21_3", "number": "21.3", "title": "Mine-Site Pilots & Commercial Deployment"},
                {"type": "index_item", "id": "sub_21_4", "number": "21.4", "title": "Multi-Site Fleet Expansion Programs"},
                {"type": "index_item", "id": "sub_21_5", "number": "21.5", "title": "Near-Term Identifiable Equipment Pipeline"}
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 18: Adoption Funnel (04_table_chart)
    # -------------------------------------------------------------
    t26_headers = t26[0]
    t26_rows = t26[1:6]
    slides.append({
        "template_id": "04_table_chart",
        "slide_index": 17,
        "data": {
            "context_note": {
                "type": "text",
                "id": "s18_note",
                "value": "Conversion metrics and active programs across the commercial mining UGV adoption lifecycle"
            },
            "chart": {
                "type": "chart",
                "id": "ch_s18_funnel",
                "chart_type": "bar",
                "title": "Active Commercial Programs & Pipeline Value ($M)",
                "data": {
                    "categories": ["Screening", "POC", "Prototype", "Mine Pilot", "Production", "Fleet Expansion"],
                    "series": [
                        {"name": "Active Programs Midpoint", "values": [150, 82, 55, 35, 13, 7]},
                        {"name": "Program Value Midpoint ($M)", "values": [42.5, 31.5, 25.0, 21.0, 10.0, 15.0]}
                    ]
                }
            },
            "section_heading": {
                "type": "text",
                "id": "s18_head",
                "value": "Adoption Funnel & Conversion Chasm"
            },
            "narrative": {
                "type": "text",
                "id": "s18_narr",
                "value": "Over 200 programs are actively evaluating UGVs. The critical commercial hurdle occurs between POC and mine pilot (35-50% conversion), where systems must prove communications and environmental resilience."
            },
            "table": {
                "type": "table",
                "id": "tbl_s18_funnel",
                "headers": t26_headers,
                "rows": t26_rows
            },
            "supporting_insight": {
                "type": "insight",
                "id": "ins_s18_funnel",
                "blocks": [
                    {
                        "id": "ins_s18_funnel_b",
                        "title": "USD 83M-207M Identifiable Pipeline",
                        "body": "Identified near-term programs encompass 650-1,220 prospective UGV units representing $83M-$207M in equipment and software procurement through 2027."
                    }
                ]
            }
        }
    })

    # -------------------------------------------------------------
    # SLIDE 19: Section 26 Opener (03_section_opener)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": 18,
        "data": {
            "section_title": {
                "type": "text",
                "id": "s19_title",
                "value": "26. Regional Intelligence: Europe & Germany"
            },
            "index_list": [
                {"type": "index_item", "id": "sub_26_1", "number": "26.1", "title": "European Mining UGV Market Sizing & Fleet"},
                {"type": "index_item", "id": "sub_26_2", "number": "26.2", "title": "Demand Concentration: Nordics & Central Europe"},
                {"type": "index_item", "id": "sub_26_3", "number": "26.3", "title": "Germany Market Sizing & Tunneling Crossover"},
                {"type": "index_item", "id": "sub_26_4", "number": "26.4", "title": "European Buyer & CE Compliance Standards"},
                {"type": "index_item", "id": "sub_26_5", "number": "26.5", "title": "Regional Service & Technical Support Networks"}
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 20: Two-Column Dashboard: Europe & Germany (08_multi_table_dashboard_2col)
    # -------------------------------------------------------------
    t30_headers = t30[0]
    t30_rows = [
        ["Market value", "USD 40-55M", "USD 50-70M", "USD 60-85M", "USD 110-160M"],
        ["Annual deployments", "250-400", "300-500", "350-600", "700-1,100"],
        ["Installed fleet", "900-1,400", "1,100-1,600", "1,300-1,900", "2,800-4,200"],
        ["Underground share", "60-68%", "62-70%", "63-71%", "65-73%"]
    ]
    t33_headers = t33[0]
    t33_rows = [
        ["Market value", "USD 3.5-4.5M", "USD 4-6M", "USD 5-7M", "USD 9-14M"],
        ["Annual deployments", "20-35", "25-45", "30-55", "60-100"],
        ["Installed fleet", "80-130", "100-150", "120-180", "250-400"],
        ["Tunnel / underground", "45-55%", "45-55%", "45-60%", "50-60%"]
    ]
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": 19,
        "data": {
            "title": {
                "type": "text",
                "id": "s20_title",
                "value": "Regional Deep Dive: European Market & Germany Sub-Surface Opportunity"
            },
            "left_column": [
                {
                    "type": "text",
                    "id": "s20_l_h",
                    "value": "Table 26.1: Europe Mining UGV Market Data",
                    "role": "heading"
                },
                {
                    "type": "table",
                    "id": "tbl_s20_eur",
                    "headers": t30_headers,
                    "rows": t30_rows
                },
                {
                    "type": "text",
                    "id": "s20_l_p",
                    "value": "Europe represents 23-28% of global market revenue, anchored by highly automated Swedish and Finnish underground hard-rock mines."
                }
            ],
            "right_column": [
                {
                    "type": "text",
                    "id": "s20_r_h",
                    "value": "Table 26.3: Germany Market Sizing & Tunneling",
                    "role": "heading"
                },
                {
                    "type": "table",
                    "id": "tbl_s20_ger",
                    "headers": t33_headers,
                    "rows": t33_rows
                },
                {
                    "type": "insight",
                    "id": "ins_s20_ger",
                    "blocks": [
                        {
                            "id": "ins_s20_ger_b",
                            "title": "Tunneling & Industrial Infrastructure",
                            "body": "Germany's opportunity centers on underground tunneling inspection, infrastructure monitoring, and industrial robotics crossover, scaling to $9-14M by 2030."
                        }
                    ]
                }
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 21: Section 32 Opener (03_section_opener)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": 20,
        "data": {
            "section_title": {
                "type": "text",
                "id": "s21_title",
                "value": "32. Customer-Validated Market Opportunity & White-Space Analysis"
            },
            "index_list": [
                {"type": "index_item", "id": "sub_32_1", "number": "32.1", "title": "GNSS-Denied Navigation Capability Gap"},
                {"type": "index_item", "id": "sub_32_2", "number": "32.2", "title": "Multi-Sensor Inspection & Edge AI Analytics"},
                {"type": "index_item", "id": "sub_32_3", "number": "32.3", "title": "Long-Endurance Battery & Hot-Swap Architecture"},
                {"type": "index_item", "id": "sub_32_4", "number": "32.4", "title": "Retrofit Autonomy Kits for Existing Machinery"},
                {"type": "index_item", "id": "sub_32_5", "number": "32.5", "title": "Recurring Robotics-as-a-Service (RaaS) Models"}
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 22: White-Space Large Table (06_large_table)
    # -------------------------------------------------------------
    t36_headers = t36[0]
    t36_rows = t36[1:]
    slides.append({
        "template_id": "06_large_table",
        "slide_index": 21,
        "data": {
            "table_title": {
                "type": "text",
                "id": "s22_title",
                "value": "Table 32.1: Customer-Validated Market Opportunity & White-Space Matrix"
            },
            "table": {
                "type": "table",
                "id": "tbl_s22_white",
                "headers": t36_headers,
                "rows": t36_rows
            }
        }
    })

    # -------------------------------------------------------------
    # SLIDE 23: Section 35 Opener (03_section_opener)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "03_section_opener",
        "slide_index": 22,
        "data": {
            "section_title": {
                "type": "text",
                "id": "s23_title",
                "value": "35. Company Benchmarking: Komatsu Ltd."
            },
            "index_list": [
                {"type": "index_item", "id": "sub_35_1", "number": "35.1", "title": "Corporate Financials & Mining Equipment Scope"},
                {"type": "index_item", "id": "sub_35_2", "number": "35.2", "title": "FrontRunner Autonomous Haulage System (AHS)"},
                {"type": "index_item", "id": "sub_35_3", "number": "35.3", "title": "1,000+ Autonomous Truck Milestone & Nevada Deployment"},
                {"type": "index_item", "id": "sub_35_4", "number": "35.4", "title": "Proprietary Autonomous Revenue & Fleet Sizing"},
                {"type": "index_item", "id": "sub_35_5", "number": "35.5", "title": "Strategic Positioning in Heavy Mining UGVs"}
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 24: Two-Column Dashboard: Komatsu Intelligence (08_multi_table_dashboard_2col)
    # -------------------------------------------------------------
    t38_headers = ["Financial / Operational Metric", "Komatsu Ltd."]
    t38_rows = [
        ["Headquarters", "Tokyo, Japan"],
        ["FY2025 Revenue", "JPY 4,132.8B"],
        ["FY2025 Operating Income", "JPY 567.3B (13.7%)"],
        ["FY2025 R&D Expenditure", "JPY 110.5B (2.7%)"],
        ["Mining Equipment Sales", "JPY 1,916.2B (>50%)"],
        ["Core Mining Tech", "FrontRunner, DISPATCH"]
    ]
    t40_headers = ["FrontRunner Platform Metric", "Fleet Indicator"]
    t40_rows = [
        ["Commercial launch", "2008 (18+ years)"],
        ["Autonomous trucks commissioned", "1,000+ units"],
        ["Material moved autonomously", "11.5B+ tonnes"],
        ["1,000th autonomous unit", "930E-5AT (290t, Barrick)"],
        ["Active AHS mine sites", "35-50 sites worldwide"],
        ["Annual autonomous shipments", "90-160 units"]
    ]
    slides.append({
        "template_id": "08_multi_table_dashboard_2col",
        "slide_index": 23,
        "data": {
            "title": {
                "type": "text",
                "id": "s24_title",
                "value": "Company Benchmarking: Komatsu Ltd. Financial Profile & FrontRunner AHS Fleet"
            },
            "left_column": [
                {
                    "type": "text",
                    "id": "s24_l_h",
                    "value": "Table 35.1: Komatsu Financials & Mining Profile",
                    "role": "heading"
                },
                {
                    "type": "table",
                    "id": "tbl_s24_komatsu",
                    "headers": t38_headers,
                    "rows": t38_rows
                },
                {
                    "type": "text",
                    "id": "s24_l_p",
                    "value": "Komatsu's mining equipment business exceeded 50% of total company sales, generating substantial cash flow to fund autonomous and electrification R&D."
                }
            ],
            "right_column": [
                {
                    "type": "text",
                    "id": "s24_r_h",
                    "value": "Table 35.2: FrontRunner Autonomous Haulage Metrics",
                    "role": "heading"
                },
                {
                    "type": "table",
                    "id": "tbl_s24_ahs",
                    "headers": t40_headers,
                    "rows": t40_rows
                },
                {
                    "type": "insight",
                    "id": "ins_s24_ahs",
                    "blocks": [
                        {
                            "id": "ins_s24_ahs_b",
                            "title": "Unmatched Haulage Operational Record",
                            "body": "With over 11.5 billion tonnes moved autonomously across 1,000+ ultra-class haul trucks, Komatsu sets the industry benchmark for commercial reliability in surface autonomous operations."
                        }
                    ]
                }
            ]
        }
    })

    # -------------------------------------------------------------
    # SLIDE 25: Strategic Recommendations & Action Framework (05_insight_information)
    # -------------------------------------------------------------
    slides.append({
        "template_id": "05_insight_information",
        "slide_index": 24,
        "data": {
            "title": {
                "type": "text",
                "id": "s25_title",
                "value": "Strategic Recommendations & 2030 Commercialization Roadmap"
            },
            "left_column": [
                {
                    "type": "text",
                    "id": "s25_l_h",
                    "value": "Near-Term Priorities (0-18 Months)",
                    "role": "heading"
                },
                {
                    "type": "text",
                    "id": "s25_l_p",
                    "value": "Suppliers must bridge the trial-to-production chasm by delivering validated reliability in harsh sub-surface environments rather than marketing standalone hardware."
                },
                {
                    "type": "bullet_list",
                    "id": "s25_l_b",
                    "items": [
                        {"id": "s25_l_b_1", "text": "Deploy multi-modal LiDAR + Visual SLAM to eliminate GNSS reliance in drift headings."},
                        {"id": "s25_l_b_2", "text": "Provide plug-and-play retrofit kits for existing light utility vehicles to accelerate entry."},
                        {"id": "s25_l_b_3", "text": "Establish regional field depots in primary hubs (Perth, Sudbury, Antofagasta)."}
                    ]
                }
            ],
            "right_column": [
                {
                    "type": "text",
                    "id": "s25_r_h",
                    "value": "Long-Term Scalability (18-36 Months)",
                    "role": "heading"
                },
                {
                    "type": "text",
                    "id": "s25_r_p",
                    "value": "Sustainable competitive advantage will center on digital mine integration, centralized fleet orchestration software, and predictive maintenance algorithms."
                },
                {
                    "type": "insight",
                    "id": "ins_s25_rec",
                    "blocks": [
                        {
                            "id": "ins_s25_rec_b",
                            "title": "Integrated Fleet Solution Imperative",
                            "body": "The winning 2030 business model integrates ruggedized IP68 hardware with recurring fleet management software, edge AI defect detection, and full mine safety compliance."
                        }
                    ]
                }
            ]
        }
    })

    report_manifest = {
        "report_id": "rep_mining_ugv_email_2026",
        "title": "Mining Underground Ground Vehicles (UGV) Market",
        "created_at": "2026-09-18T12:00:00Z",
        "template_set": "mining_ugv",
        "defaults": {
            "background": "bg_02.png",
            "font_family": "Arial",
            "accent_color": "#1B365D"
        },
        "slides": slides
    }

    output_path = "examples/mining_ugv_email_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_manifest, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated '{output_path}' with {len(slides)} slides.")


if __name__ == "__main__":
    build_report()
