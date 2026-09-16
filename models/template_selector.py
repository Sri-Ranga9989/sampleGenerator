"""
Deterministic Template Selector
Maps content semantics and structure to canonical template IDs.
Never uses non-deterministic heuristics or runtime LLM calls.
"""

from typing import Dict, Any, List


class TemplateSelector:
    @staticmethod
    def select_template(content_data: Dict[str, Any], explicit_template_id: str = None) -> str:
        """
        Returns a canonical template_id for the given content payload.
        If explicit_template_id is provided and valid, it is honored.
        """
        valid_templates = {
            "01_cover_title_image",
            "02_toc_image",
            "03_section_opener",
            "04_table_chart",
            "05_insight_information",
            "06_large_table",
            "07_large_chart",
            "08_multi_table_dashboard_2col"
        }

        if explicit_template_id and explicit_template_id in valid_templates:
            return explicit_template_id

        # Check content markers
        content_type = content_data.get("type", "").lower()
        if content_type in ["cover", "title_slide", "report_cover"]:
            return "01_cover_title_image"
        if content_type in ["toc", "table_of_contents"]:
            return "02_toc_image"
        if content_type in ["section_opener", "section_intro"]:
            return "03_section_opener"

        regions = content_data.get("regions", content_data)
        
        # Check presence of key region types
        has_chart = any("chart" in k.lower() or (isinstance(v, dict) and v.get("type") == "chart") for k, v in regions.items())
        table_count = sum(1 for k, v in regions.items() if "table" in k.lower() or (isinstance(v, dict) and v.get("type") == "table"))
        has_toc_items = any("toc" in k.lower() for k in regions.items())
        has_index_items = any("index" in k.lower() for k in regions.items())

        if has_toc_items or "toc_items" in content_data:
            return "02_toc_image"

        if has_index_items and "section_title" in regions:
            return "03_section_opener"

        # Analytical layouts
        if has_chart and table_count >= 1:
            return "04_table_chart"

        if table_count >= 2:
            return "08_multi_table_dashboard_2col"

        if table_count == 1 and not has_chart:
            # If the table is the dominant content
            return "06_large_table"

        if has_chart and table_count == 0:
            return "07_large_chart"

        # Default narrative / multi-block information slide
        return "05_insight_information"
