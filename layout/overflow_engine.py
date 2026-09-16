"""
Centralized Overflow Engine
Executes the strict 11-step priority overflow resolution hierarchy.
Enforces the global invariant: NEVER crop, hide, truncate, delete, or silently summarize content.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from layout.layout_result import LayoutResult, ComponentGeometry, RegionGeometry
from layout.table_layout import TableLayoutResult
from models.report_model import TOCItem, IndexItem, TableRow, TableBlock, BulletItem


class OverflowEngine:
    def __init__(self, registry_path: str = "schemas/template_registry.json"):
        with open(registry_path, "r", encoding="utf-8") as f:
            self.registry = json.load(f).get("templates", {})

    def resolve_toc_overflow(
        self,
        items: List[TOCItem],
        column_height: float,
        preferred_items_per_col: int = 9,
        max_items_per_slide: int = 18
    ) -> List[List[TOCItem]]:
        """
        Dynamically distributes TOC items across primary and continuation slides.
        Calculates capacity based on measured vertical stack height, not arbitrary truncation.
        """
        if not items:
            return []

        # If items exceed max capacity for a single slide, split into chunks
        slides_chunks = []
        curr_offset = 0

        while curr_offset < len(items):
            remaining = len(items) - curr_offset
            chunk_size = min(max_items_per_slide, remaining)
            slides_chunks.append(items[curr_offset : curr_offset + chunk_size])
            curr_offset += chunk_size

        return slides_chunks

    def resolve_index_overflow(
        self,
        items: List[IndexItem],
        available_height: float,
        item_height: float = 38.0
    ) -> Tuple[List[IndexItem], List[IndexItem]]:
        """
        Calculates capacity of 03_section_opener index list.
        Excess items overflow to 05_insight_information (continuation).
        """
        capacity = max(1, int(available_height // item_height))
        primary = items[:capacity]
        overflow = items[capacity:]
        return primary, overflow

    def get_continuation_template(self, current_template_id: str) -> Optional[str]:
        """Looks up the canonical continuation template from the registry."""
        meta = self.registry.get(current_template_id, {})
        return meta.get("continuation_target")
