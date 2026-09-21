"""
html_parser.py
Generic, fault-tolerant HTML email parser for market-research Gmail emails.
Parses arbitrary HTML email files into the canonical JSON manifest format
compatible with the PPT Generator V1 pipeline.

Key design:
  - Reuses extract_table() and make_table_block() patterns from build_full_email_report_json.py
  - Generic section/table detection (not hardcoded to any specific email)
  - Auto-chart injection via chart_analyzer.py
  - High fault tolerance: try/except per section, empty filtering, unicode normalization

Usage:
  python html_parser.py "Gmail - Fwd_ Automated Guided Forklifts Market.html" --output output/agf/report.json
"""

import json
import re
import os
import sys
import argparse
import unicodedata
from datetime import datetime, timezone
from bs4 import BeautifulSoup, Tag, NavigableString
from typing import List, Dict, Any, Optional, Tuple
from chart_analyzer import analyze_table_for_chart


# ─── Utility Functions (reused from build_full_email_report_json.py) ─────────

def extract_table(table_tag) -> List[List[str]]:
    """Extract a table from an HTML <table> tag into a list of rows."""
    rows = table_tag.find_all("tr")
    grid = []
    for r in rows:
        cells = [c.get_text(strip=True).replace("\xa0", " ") for c in r.find_all(["th", "td"])]
        if any(cells):
            grid.append(cells)
    return grid


def make_table_block(block_id: str, grid: List[List[str]]) -> Dict[str, Any]:
    """Convert a table grid into a canonical table block dict."""
    if not grid:
        return {"type": "table", "id": block_id, "headers": [], "rows": []}
    headers = grid[0]
    rows = []
    for r_idx, row in enumerate(grid[1:]):
        padded_row = row + [""] * max(0, len(headers) - len(row))
        rows.append({
            "id": f"{block_id}_r{r_idx+1}",
            "cells": [
                {"id": f"{block_id}_r{r_idx+1}_c{c_idx+1}", "value": val}
                for c_idx, val in enumerate(padded_row[:len(headers)])
            ]
        })
    return {
        "type": "table",
        "id": block_id,
        "headers": headers,
        "rows": rows
    }


def normalize_text(text: str) -> str:
    """Normalize unicode and whitespace in text."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.replace("\xa0", " ").replace("\u200b", "").replace("\u200e", "")
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def slugify(text: str) -> str:
    """Create a URL/ID-safe slug from text."""
    slug = re.sub(r'[^a-z0-9]+', '_', text.lower().strip())
    return slug.strip('_')[:60]


# ─── Gmail Wrapper Detection ────────────────────────────────────────────────

def is_gmail_wrapper_table(table_tag) -> bool:
    """
    Detect if a <table> is a Gmail email wrapper (header/chrome) rather than data.
    Gmail wraps emails in outer tables with specific patterns.
    """
    # Check if table has very few cells (1-2) — likely a layout wrapper
    cells = table_tag.find_all(["th", "td"])
    if len(cells) <= 2:
        return True
    
    # Check for Gmail-specific class or pattern
    parent_classes = []
    for parent in table_tag.parents:
        if hasattr(parent, 'get') and parent.get('class'):
            parent_classes.extend(parent.get('class', []))
    
    # Check for width="100%" with no data content
    if table_tag.get("width") == "100%":
        text = table_tag.get_text(strip=True)
        # If the table text looks like email header info
        if any(kw in text.lower() for kw in ['gmail', '@gmail.com', 'forwarded message', 'subject:', 'from:', 'to:']):
            return True
    
    # Check for img tags (logo tables)
    imgs = table_tag.find_all("img")
    if imgs and len(cells) <= 4:
        return True
    
    return False


def is_data_table(table_tag) -> bool:
    """
    Determine if a table contains actual data (market research) content.
    """
    grid = extract_table(table_tag)
    
    # Need at least header + 1 data row
    if len(grid) < 2:
        return False
    
    # Need at least 2 columns
    if not grid[0] or len(grid[0]) < 2:
        return False
    
    # Skip tables that are purely text/layout (single column of text)
    if all(len(row) <= 1 for row in grid):
        return False
    
    return True


# ─── Section Detection ──────────────────────────────────────────────────────

def extract_section_number(text: str) -> Optional[str]:
    """Extract section number from heading text like '1. Executive Summary'."""
    match = re.match(r'^(\d+)\.\s+', text.strip())
    if match:
        return match.group(1)
    return None


def extract_subsection_items(text: str) -> List[Dict[str, str]]:
    """
    Extract numbered subsection items from a paragraph block.
    E.g.: "1.1 Global Market Snapshot\n1.2 Market Size..."
    """
    items = []
    lines = re.split(r'[\n\r]+|<br\s*/?>|<br>', text)
    
    for line in lines:
        line = normalize_text(line)
        match = re.match(r'^(\d+\.\d+(?:\.\d+)?)\s+(.+)$', line)
        if match:
            items.append({
                "number": match.group(1),
                "title": match.group(2).strip()
            })
    
    return items


# ─── Company Profile Detection ──────────────────────────────────────────────

def extract_company_list(element) -> List[str]:
    """Extract company names from a <ul> list."""
    companies = []
    for li in element.find_all("li"):
        name = normalize_text(li.get_text())
        if name:
            companies.append(name)
    return companies


# ─── Main Parser ────────────────────────────────────────────────────────────

class EmailReportParser:
    """
    Generic parser for Gmail market-research email HTML files.
    Produces a canonical JSON manifest compatible with the PPT Generator V1 pipeline.
    """
    
    def __init__(self, auto_charts: bool = True):
        self.auto_charts = auto_charts
        self.warnings: List[str] = []
        self.stats = {
            "total_html_tables": 0,
            "data_tables": 0,
            "gmail_wrappers_skipped": 0,
            "sections_detected": 0,
            "charts_generated": 0,
            "slides_generated": 0,
            "subsection_items": 0,
            "insight_blocks": 0,
            "company_lists": 0,
        }
    
    def parse_html_file(self, html_path: str) -> Dict[str, Any]:
        """
        Main entry point: parse an HTML email file into a canonical report JSON.
        
        Args:
            html_path: Path to the Gmail HTML file
            
        Returns:
            Canonical report dict compatible with ReportParser.parse_report_json()
        """
        print(f"[PARSE] Loading HTML file: {html_path}")
        
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 1. Extract report title from <h1> or <title>
        report_title = self._extract_report_title(soup, html_path)
        print(f"[PARSE] Report title: {report_title}")
        
        # 2. Find the email body content (strip Gmail wrappers)
        body_content = self._find_email_body(soup)
        
        # 3. Extract all sections and content
        sections, all_tables = self._extract_content_structure(body_content)
        
        # 4. Build slides from sections
        slides = self._build_slides(sections, all_tables, report_title)
        
        self.stats["slides_generated"] = len(slides)
        
        # 5. Build report manifest
        report = {
            "report_id": f"rep_{slugify(report_title)}",
            "title": report_title,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "template_set": "mining_ugv",
            "defaults": {
                "background": "bg_02.png",
                "font_family": "Arial",
                "accent_color": "#0D3166"
            },
            "slides": slides
        }
        
        print(f"\n[PARSE] === Parsing Complete ===")
        print(f"  -> Sections detected: {self.stats['sections_detected']}")
        print(f"  -> Data tables extracted: {self.stats['data_tables']}")
        print(f"  -> Charts auto-generated: {self.stats['charts_generated']}")
        print(f"  -> Total slides: {self.stats['slides_generated']}")
        print(f"  -> Warnings: {len(self.warnings)}")
        
        if self.warnings:
            for w in self.warnings[:10]:
                print(f"     ⚠ {w}")
        
        return report
    
    def _extract_report_title(self, soup: BeautifulSoup, html_path: str) -> str:
        """Extract the main report title."""
        # Try <h1> first
        h1 = soup.find("h1")
        if h1:
            title = normalize_text(h1.get_text())
            if title and len(title) > 5:
                return title
        
        # Try <title> tag
        title_tag = soup.find("title")
        if title_tag:
            raw_title = normalize_text(title_tag.get_text())
            # Strip "Gmail - Fwd: " prefix
            raw_title = re.sub(r'^Gmail\s*-\s*Fwd:\s*', '', raw_title, flags=re.IGNORECASE)
            if raw_title and len(raw_title) > 5:
                return raw_title
        
        # Fallback to filename
        return os.path.splitext(os.path.basename(html_path))[0]
    
    def _find_email_body(self, soup: BeautifulSoup) -> Tag:
        """
        Find the actual email body content, stripping Gmail chrome.
        """
        # Look for the forwarded message content
        # Gmail wraps content in divs with dir="ltr" or class="gmail_quote"
        gmail_quote = soup.find("div", class_="gmail_quote")
        if gmail_quote:
            return gmail_quote
        
        # Fallback: look for the maincontent div
        main = soup.find("div", class_="maincontent")
        if main:
            return main
        
        # Last resort: return body
        body = soup.find("body")
        return body or soup
    
    def _extract_content_structure(self, body: Tag) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract the full content structure from the email body.
        
        Returns:
            (sections, all_tables) where each section has headings, sub-items, tables, and text
        """
        sections = []
        all_tables_collected = []
        current_section = None
        current_subsection_title = None
        table_counter = 0
        
        # Walk through all direct and nested elements
        elements = list(body.descendants) if body else []
        
        # Track processed elements to avoid duplicates
        processed_tables = set()
        processed_headings = set()
        
        for element in elements:
            if not isinstance(element, Tag):
                continue
            
            try:
                # === SECTION HEADINGS (h3 with numbered pattern like "1. Executive Summary") ===
                if element.name == "h3" and id(element) not in processed_headings:
                    text = normalize_text(element.get_text())
                    sec_num = extract_section_number(text)
                    
                    if sec_num:
                        processed_headings.add(id(element))
                        # Save previous section
                        if current_section:
                            sections.append(current_section)
                        
                        current_section = {
                            "number": sec_num,
                            "title": re.sub(r'^\d+\.\s+', '', text),
                            "full_title": text,
                            "subsections": [],
                            "tables": [],
                            "insights": [],
                            "sub_headings": [],
                        }
                        self.stats["sections_detected"] += 1
                        current_subsection_title = None
                    elif current_section:
                        # This is a sub-heading within a section (like "3.1 Global Market Development")
                        current_subsection_title = text
                        current_section["sub_headings"].append(text)
                
                # === DATA SECTION HEADINGS (h2 with section data) ===
                elif element.name == "h2" and id(element) not in processed_headings:
                    text = normalize_text(element.get_text())
                    sec_num = extract_section_number(text)
                    if sec_num and current_section is None:
                        processed_headings.add(id(element))
                        current_section = {
                            "number": sec_num,
                            "title": re.sub(r'^\d+\.\s+', '', text),
                            "full_title": text,
                            "subsections": [],
                            "tables": [],
                            "insights": [],
                            "sub_headings": [],
                        }
                        self.stats["sections_detected"] += 1
                    elif text and current_section:
                        current_subsection_title = text
                        current_section["sub_headings"].append(text)
                
                # === SUBSECTION LISTS (paragraphs with "1.1 xxx\n1.2 xxx") ===
                elif element.name == "p" and current_section:
                    text = element.get_text()
                    sub_items = extract_subsection_items(text)
                    if sub_items:
                        current_section["subsections"].extend(sub_items)
                        self.stats["subsection_items"] += len(sub_items)
                    else:
                        # Regular paragraph — could be insight/commentary
                        clean_text = normalize_text(text)
                        if clean_text and len(clean_text) > 30:
                            current_section["insights"].append({
                                "text": clean_text,
                                "context": current_subsection_title or current_section.get("title", "")
                            })
                            self.stats["insight_blocks"] += 1
                
                # === DATA TABLES ===
                elif element.name == "table" and id(element) not in processed_tables:
                    processed_tables.add(id(element))
                    self.stats["total_html_tables"] += 1
                    
                    if is_gmail_wrapper_table(element):
                        self.stats["gmail_wrappers_skipped"] += 1
                        continue
                    
                    if is_data_table(element):
                        table_counter += 1
                        grid = extract_table(element)
                        table_id = f"tbl_{table_counter:02d}"
                        table_block = make_table_block(table_id, grid)
                        
                        # Attach title context
                        table_block["_title"] = current_subsection_title or ""
                        table_block["_section_num"] = current_section["number"] if current_section else "0"
                        
                        if current_section:
                            current_section["tables"].append(table_block)
                        
                        all_tables_collected.append(table_block)
                        self.stats["data_tables"] += 1
                
                # === COMPANY LISTS (ul with li items) ===
                elif element.name == "ul" and current_section:
                    companies = extract_company_list(element)
                    if companies and len(companies) >= 3:
                        current_section.setdefault("company_lists", []).append(companies)
                        self.stats["company_lists"] += 1
                
            except Exception as e:
                self.warnings.append(f"Error processing element <{getattr(element, 'name', '?')}>: {str(e)[:100]}")
                continue
        
        # Don't forget the last section
        if current_section:
            sections.append(current_section)
        
        return sections, all_tables_collected
    
    def _build_slides(
        self,
        sections: List[Dict],
        all_tables: List[Dict],
        report_title: str
    ) -> List[Dict[str, Any]]:
        """
        Convert extracted sections into canonical slide dicts.
        """
        slides = []
        
        # ─── SLIDE 1: Cover Title ────────────────────────────────────────
        slides.append({
            "template_id": "01_cover_title_image",
            "slide_index": 0,
            "data": {
                "title": {
                    "type": "text",
                    "id": "cov_title",
                    "value": report_title
                },
                "subtitle": {
                    "type": "text",
                    "id": "cov_sub",
                    "value": f"Comprehensive Market Intelligence & Strategic Analysis"
                },
                "metadata": {
                    "type": "text",
                    "id": "cov_meta",
                    "value": f"Enterprise Intelligence Deck | {self.stats['data_tables']} Verified Data Grids | {len(sections)} Strategic Sections"
                }
            }
        })
        
        # ─── SLIDE 2: Table of Contents ──────────────────────────────────
        toc_items = []
        for i, sec in enumerate(sections):
            toc_items.append({
                "id": f"toc_item_{i+1:02d}",
                "number": f"{i+1:02d}",
                "title": sec["title"]
            })
        
        if toc_items:
            slides.append({
                "template_id": "02_toc_image",
                "slide_index": len(slides),
                "data": {
                    "title": {"type": "text", "id": "toc_heading", "value": "TABLE OF CONTENTS"},
                    "items": toc_items
                }
            })
        
        # ─── SECTION SLIDES ──────────────────────────────────────────────
        for sec_idx, section in enumerate(sections):
            try:
                self._build_section_slides(slides, section, sec_idx)
            except Exception as e:
                self.warnings.append(f"Error building slides for section '{section.get('title', '?')}': {str(e)[:200]}")
                continue
        
        # Update slide indices
        for i, slide in enumerate(slides):
            slide["slide_index"] = i
        
        return slides
    
    def _build_section_slides(
        self,
        slides: List[Dict],
        section: Dict,
        sec_idx: int
    ):
        """Build all slides for a single section."""
        sec_num = section["number"]
        sec_title = section["title"]
        tables = section.get("tables", [])
        insights = section.get("insights", [])
        subsections = section.get("subsections", [])
        sub_headings = section.get("sub_headings", [])
        company_lists = section.get("company_lists", [])
        
        # ─── Section Opener ──────────────────────────────────────────
        index_items = []
        for sub in subsections[:12]:  # Limit to 12 for the opener
            index_items.append({
                "id": f"sub_{slugify(sub['number'])}",
                "number": sub["number"],
                "title": sub["title"]
            })
        
        slides.append({
            "template_id": "03_section_opener",
            "slide_index": len(slides),
            "data": {
                "section_title": f"{sec_num}. {sec_title}",
                "index_list": index_items
            }
        })
        
        # ─── Table Slides ────────────────────────────────────────────
        # Strategy: 
        #   - Single table → 06_large_table
        #   - Two adjacent tables with insights → 08_multi_table_dashboard_2col
        #   - Table + auto-chart → 04_table_chart
        
        table_queue = list(tables)
        insight_queue = list(insights)
        
        while table_queue:
            table = table_queue.pop(0)
            table_title = table.get("_title", "") or f"Section {sec_num} Data"
            table_id = table["id"]
            
            # Check for auto-chart
            chart_block = None
            if self.auto_charts:
                headers = table.get("headers", [])
                raw_rows = table.get("rows", [])
                flat_rows = []
                for row in raw_rows:
                    if isinstance(row, dict):
                        cells = row.get("cells", [])
                        flat_rows.append([str(c.get("value", "")) if isinstance(c, dict) else str(c) for c in cells])
                    elif isinstance(row, list):
                        flat_rows.append([str(c) for c in row])
                
                chart_block = analyze_table_for_chart(table_id, headers, flat_rows, table_title)
            
            if chart_block and len(table.get("rows", [])) <= 12:
                # ─── Table + Chart slide (04_table_chart) ────────────
                insight_text = ""
                if insight_queue:
                    ins = insight_queue.pop(0)
                    insight_text = ins["text"]
                
                # Clean table block (remove internal metadata)
                clean_table = {k: v for k, v in table.items() if not k.startswith("_")}
                
                slides.append({
                    "template_id": "04_table_chart",
                    "slide_index": len(slides),
                    "data": {
                        "context_note": table_title,
                        "chart": chart_block,
                        "heading": table_title,
                        "narrative": insight_text[:300] if insight_text else f"Key data metrics from {table_title}",
                        "table": clean_table,
                        "insight": {
                            "type": "insight",
                            "id": f"ins_{table_id}",
                            "title": "KEY INSIGHT",
                            "body": insight_text[:200] if insight_text else f"Data analysis from {table_title}"
                        }
                    }
                })
                self.stats["charts_generated"] += 1
            
            elif table_queue and len(table.get("rows", [])) <= 10 and len(table_queue[0].get("rows", [])) <= 10:
                # ─── Dashboard: pair two small tables (08_multi_table_dashboard_2col) ──
                table2 = table_queue.pop(0)
                table2_title = table2.get("_title", "") or "Additional Data"
                
                left_blocks = [
                    {"type": "text", "id": f"h_{table_id}", "role": "heading", "text": table_title},
                    {k: v for k, v in table.items() if not k.startswith("_")},
                ]
                right_blocks = [
                    {"type": "text", "id": f"h_{table2['id']}", "role": "heading", "text": table2_title},
                    {k: v for k, v in table2.items() if not k.startswith("_")},
                ]
                
                # Add insights if available
                if insight_queue:
                    ins = insight_queue.pop(0)
                    left_blocks.append({
                        "type": "insight",
                        "id": f"ins_{table_id}",
                        "title": "Key Finding",
                        "body": ins["text"][:200]
                    })
                if insight_queue:
                    ins = insight_queue.pop(0)
                    right_blocks.append({
                        "type": "insight",
                        "id": f"ins_{table2['id']}",
                        "title": "Key Finding",
                        "body": ins["text"][:200]
                    })
                
                slides.append({
                    "template_id": "08_multi_table_dashboard_2col",
                    "slide_index": len(slides),
                    "data": {
                        "title": f"{table_title} & {table2_title}",
                        "left_column": left_blocks,
                        "right_column": right_blocks
                    }
                })
                
                # Auto-chart for first table of the pair if applicable
                if chart_block:
                    slides.append({
                        "template_id": "07_large_chart",
                        "slide_index": len(slides),
                        "data": {
                            "title": chart_block.get("title", "Data Visualization"),
                            "chart": chart_block
                        }
                    })
                    self.stats["charts_generated"] += 1
            
            else:
                # ─── Large Table slide (06_large_table) ──────────────
                clean_table = {k: v for k, v in table.items() if not k.startswith("_")}
                
                slides.append({
                    "template_id": "06_large_table",
                    "slide_index": len(slides),
                    "data": {
                        "title": table_title,
                        "table": clean_table
                    }
                })
                
                # Auto-chart after the table
                if chart_block:
                    slides.append({
                        "template_id": "07_large_chart",
                        "slide_index": len(slides),
                        "data": {
                            "title": chart_block.get("title", "Data Visualization"),
                            "chart": chart_block
                        }
                    })
                    self.stats["charts_generated"] += 1
        
        # ─── Remaining Insights (if no tables consumed them) ─────────
        if insight_queue and len(insight_queue) >= 2:
            # Build an insight information slide
            left_items = []
            right_items = []
            
            for i, ins in enumerate(insight_queue[:6]):
                target = left_items if i % 2 == 0 else right_items
                target.append({
                    "type": "text",
                    "id": f"t_{sec_num}_ins_{i}",
                    "role": "paragraph",
                    "text": ins["text"]
                })
            
            if left_items or right_items:
                slides.append({
                    "template_id": "05_insight_information",
                    "slide_index": len(slides),
                    "data": {
                        "title": f"{sec_title} — Key Findings",
                        "left_column": left_items if left_items else [{"type": "text", "id": f"t_{sec_num}_empty_l", "role": "paragraph", "text": "See data tables for detailed analysis."}],
                        "right_column": right_items if right_items else [{"type": "text", "id": f"t_{sec_num}_empty_r", "role": "paragraph", "text": "Additional intelligence available in supplementary data."}]
                    }
                })
        
        # ─── Company Lists ───────────────────────────────────────────
        for cl_idx, companies in enumerate(company_lists):
            slides.append({
                "template_id": "05_insight_information",
                "slide_index": len(slides),
                "data": {
                    "title": f"{sec_title} — Company Profiles",
                    "left_column": [
                        {
                            "type": "bullet_list",
                            "id": f"cl_{sec_num}_{cl_idx}_l",
                            "items": [
                                {"id": f"cl_{sec_num}_{cl_idx}_l_{i}", "text": c, "level": 0}
                                for i, c in enumerate(companies[:len(companies)//2 + 1])
                            ]
                        }
                    ],
                    "right_column": [
                        {
                            "type": "bullet_list",
                            "id": f"cl_{sec_num}_{cl_idx}_r",
                            "items": [
                                {"id": f"cl_{sec_num}_{cl_idx}_r_{i}", "text": c, "level": 0}
                                for i, c in enumerate(companies[len(companies)//2 + 1:])
                            ]
                        }
                    ]
                }
            })


def parse_html_to_json(
    html_path: str,
    output_path: Optional[str] = None,
    auto_charts: bool = True
) -> Dict[str, Any]:
    """
    Convenience function: parse HTML file to JSON manifest.
    
    Args:
        html_path: Path to Gmail HTML file
        output_path: Optional path to save JSON output
        auto_charts: Whether to auto-generate charts for graph-worthy tables
        
    Returns:
        Canonical report dict
    """
    parser = EmailReportParser(auto_charts=auto_charts)
    report = parser.parse_html_file(html_path)
    
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n[PARSE] Saved JSON manifest: {output_path}")
    
    return report, parser.stats, parser.warnings


def main():
    parser = argparse.ArgumentParser(description="Parse Gmail HTML email into PPT Generator JSON manifest")
    parser.add_argument("input", help="Path to Gmail HTML file")
    parser.add_argument("--output", "-o", default=None, help="Path to output JSON file")
    parser.add_argument("--no-auto-charts", action="store_true", help="Disable automatic chart generation")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"[ERROR] File not found: {args.input}")
        sys.exit(1)
    
    # Default output path
    if not args.output:
        base = os.path.splitext(os.path.basename(args.input))[0]
        slug = slugify(base)
        args.output = os.path.join("output", slug, "report.json")
    
    report, stats, warnings = parse_html_to_json(
        args.input,
        args.output,
        auto_charts=not args.no_auto_charts
    )
    
    # Print stats summary
    print(f"\n[STATS] Parsing Statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
