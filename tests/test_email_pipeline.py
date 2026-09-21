"""
test_email_pipeline.py
Unit and integration tests for the HTML email parsing pipeline, chart analyzer, and API server.
"""

import os
import json
import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from html_parser import EmailReportParser, parse_html_to_json, extract_section_number, extract_subsection_items
from chart_analyzer import parse_numeric_value, is_percentage_column, is_year_header, detect_chart_type, analyze_table_for_chart
from api_server import app
from models.report_model import ReportParser
from renderer.template_renderer import TemplateRenderer
from renderer.powerpoint_renderer import PowerPointRenderer
from validators.structural_validator import StructuralValidator
from validators.completeness_validator import CompletenessValidator

HTML_FILE = "Gmail - Fwd_ Automated Guided Forklifts Market.html"


class TestChartAnalyzer:
    """Tests for table graph-worthiness and chart generation."""

    def test_parse_numeric_values(self):
        assert parse_numeric_value("$4.7 Bn") == 4_700_000_000.0
        assert parse_numeric_value("$5.9 Bn") == 5_900_000_000.0
        assert parse_numeric_value("$991 Mn") == 991_000_000.0
        assert parse_numeric_value("€5.502 Bn") == 5_502_000_000.0
        assert parse_numeric_value("~34,000") == 34000.0
        assert parse_numeric_value("12.8%") == 12.8
        assert parse_numeric_value("24.9k") == 24900.0
        assert parse_numeric_value("3.43") == 3.43
        assert parse_numeric_value("—") is None
        assert parse_numeric_value("N/A") is None
        assert parse_numeric_value("Total") is None

    def test_column_type_detection(self):
        years = ["2021", "2022", "2023", "2024", "2025", "2026E"]
        assert all(is_year_header(y) for y in years)

        pcts = ["12.2%", "12.0%", "9.5%", "11.3%"]
        assert is_percentage_column(pcts) is True

    def test_graph_worthiness_and_generation(self):
        headers = ["Segment", "Units", "Market Value", "Share"]
        rows = [
            ["Automated Counterbalance", "~15,500", "$1.74 Bn", "29.5%"],
            ["Automated Reach / VNA", "~6,800", "$1.16 Bn", "19.7%"],
            ["Automated Pallet / Stackers", "~9,700", "$0.96 Bn", "16.3%"],
            ["Autonomous Heavy-Duty", "~3,100", "$0.78 Bn", "13.2%"],
            ["Total", "~43,100", "$5.90 Bn", "100%"]
        ]
        chart = analyze_table_for_chart("tbl_test", headers, rows, "Market Structure")
        assert chart is not None
        assert chart["type"] == "chart"
        assert len(chart["categories"]) == 4  # Total row should be excluded
        assert len(chart["series"]) >= 1


class TestHtmlParser:
    """Tests for the generic HTML email parser."""

    def test_section_number_extraction(self):
        assert extract_section_number("1. Executive Summary") == "1"
        assert extract_section_number("37. Appendix") == "37"
        assert extract_section_number("Executive Summary") is None

    def test_subsection_items_extraction(self):
        raw = "1.1 Global Market Snapshot\n1.2 Market Size, Volume & Fleet Outlook\n1.3 Deployment"
        items = extract_subsection_items(raw)
        assert len(items) == 3
        assert items[0]["number"] == "1.1"
        assert items[0]["title"] == "Global Market Snapshot"

    @pytest.mark.skipif(not os.path.exists(HTML_FILE), reason="AGF HTML file required")
    def test_parse_agf_email(self):
        parser = EmailReportParser(auto_charts=True)
        report = parser.parse_html_file(HTML_FILE)

        assert report["title"] == "Automated Guided Forklifts Market"
        assert parser.stats["sections_detected"] >= 35
        assert parser.stats["data_tables"] >= 30
        assert parser.stats["charts_generated"] >= 20
        assert len(report["slides"]) >= 70

        # Validate canonical report model parsing
        canonical_report = ReportParser.parse_report_json(report)
        assert len(canonical_report.slides) == len(report["slides"])
        assert len(canonical_report.all_input_ids) > 1000


class TestApiServer:
    """Tests for the FastAPI server endpoints."""

    def test_health_endpoint(self):
        client = TestClient(app)
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

    @pytest.mark.skipif(not os.path.exists(HTML_FILE), reason="AGF HTML file required")
    def test_parse_endpoint(self):
        client = TestClient(app)
        with open(HTML_FILE, "rb") as f:
            res = client.post("/parse", files={"file": ("agf.html", f, "text/html")})
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "success"
        assert body["stats"]["data_tables"] >= 30
        assert body["stats"]["sections_detected"] >= 35
        assert body["slide_count"] >= 70

    @pytest.mark.skipif(not os.path.exists(HTML_FILE), reason="AGF HTML file required")
    def test_pipeline_endpoint(self):
        client = TestClient(app)
        with open(HTML_FILE, "rb") as f:
            res = client.post("/pipeline", files={"file": ("agf.html", f, "text/html")})
        assert res.status_code == 200
        assert res.headers["x-structural-status"] == "PASS"
        assert res.headers["x-completeness-status"] == "PASS"
        assert int(res.headers["x-slides"]) >= 70
        assert len(res.content) > 100_000
