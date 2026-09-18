"""
Canonical Report Data Model with Deterministic Stable IDs
Supports both high-level hierarchical report structures and slide manifests.
Provides provenance tracking for 100% content completeness validation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union


@dataclass
class ContentItem:
    """Base content item carrying a stable ID for completeness tracking."""
    id: str


@dataclass
class TextBlock(ContentItem):
    text: str
    role: str = "body"  # title, subtitle, heading, body, context_note, footer
    style: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BulletItem(ContentItem):
    text: str
    level: int = 0


@dataclass
class BulletListBlock(ContentItem):
    items: List[BulletItem] = field(default_factory=list)


@dataclass
class TOCItem(ContentItem):
    number: str
    title: str


@dataclass
class IndexItem(ContentItem):
    number: str
    title: str


@dataclass
class TableCell(ContentItem):
    value: Any
    style: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableRow(ContentItem):
    cells: List[TableCell] = field(default_factory=list)


@dataclass
class TableBlock(ContentItem):
    headers: List[str] = field(default_factory=list)
    rows: List[TableRow] = field(default_factory=list)
    column_widths: Optional[List[float]] = None
    style: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChartSeries:
    name: str
    values: List[Union[int, float]]


@dataclass
class ChartBlock(ContentItem):
    chart_type: str  # bar, line, pie
    categories: List[str] = field(default_factory=list)
    series: List[ChartSeries] = field(default_factory=list)
    title: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InsightBlock(ContentItem):
    title: str
    body: str
    icon: Optional[str] = None


@dataclass
class ImageBlock(ContentItem):
    src: str
    alt: str = ""
    fit: str = "contain"


@dataclass
class SlideData:
    """Represents the raw content data payload for a single slide."""
    regions: Dict[str, Any] = field(default_factory=dict)
    # Blocks for container/column-driven templates (05, 08)
    left_column_blocks: List[Any] = field(default_factory=list)
    right_column_blocks: List[Any] = field(default_factory=list)


@dataclass
class Slide:
    slide_id: str
    template_id: str
    slide_index: int
    data: SlideData
    title: Optional[str] = None
    continuation_from: Optional[str] = None
    is_continuation: bool = False


@dataclass
class Subsection:
    number: str
    title: str
    id: str = ""


@dataclass
class Section:
    number: str
    title: str
    id: str = ""
    subsections: List[Subsection] = field(default_factory=list)
    slides: List[Slide] = field(default_factory=list)


@dataclass
class Report:
    report_id: str
    title: str
    subtitle: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    created_at: Optional[str] = None
    template_set: str = "mining_ugv"
    sections: List[Section] = field(default_factory=list)
    slides: List[Slide] = field(default_factory=list)
    # Master registry of all input IDs for completeness verification
    all_input_ids: List[str] = field(default_factory=list)


class ReportParser:
    """
    Parses JSON report files into normalized canonical Report objects,
    automatically assigning stable IDs and collecting them for completeness auditing.
    """

    @staticmethod
    def parse_report_json(data: Dict[str, Any]) -> Report:
        # Check if wrapped in "report" top-level key (Prompt Section 25)
        raw_report = data.get("report", data)
        report_id = raw_report.get("report_id", "report_01")
        title = raw_report.get("title", "Untitled Report")
        subtitle = raw_report.get("subtitle")
        author = raw_report.get("author")
        date = raw_report.get("date")
        created_at = raw_report.get("created_at")
        template_set = raw_report.get("template_set", "mining_ugv")

        all_input_ids: List[str] = []
        slides: List[Slide] = []
        sections: List[Section] = []

        # If high-level sections are provided
        if "sections" in raw_report:
            for sec_idx, sec_data in enumerate(raw_report["sections"]):
                sec_num = str(sec_data.get("number", sec_idx + 1))
                sec_title = sec_data.get("title", f"Section {sec_num}")
                sec_id = sec_data.get("id", f"sec_{sec_num}")
                all_input_ids.append(sec_id)

                subsections = []
                for sub_idx, sub_data in enumerate(sec_data.get("subsections", [])):
                    sub_num = str(sub_data.get("number", f"{sec_num}.{sub_idx + 1}"))
                    sub_title = sub_data.get("title", f"Subsection {sub_num}")
                    sub_id = sub_data.get("id", f"sub_{sub_num}")
                    subsections.append(Subsection(number=sub_num, title=sub_title, id=sub_id))
                    all_input_ids.append(sub_id)

                sec_slides = []
                for sl_idx, sl_data in enumerate(sec_data.get("slides", [])):
                    slide = ReportParser._parse_slide_dict(sl_data, len(slides) + len(sec_slides), all_input_ids)
                    sec_slides.append(slide)

                section = Section(
                    number=sec_num,
                    title=sec_title,
                    id=sec_id,
                    subsections=subsections,
                    slides=sec_slides
                )
                sections.append(section)
                slides.extend(sec_slides)

        # If flat slides array is provided (report.schema.json format)
        elif "slides" in raw_report:
            for idx, sl_data in enumerate(raw_report["slides"]):
                slide = ReportParser._parse_slide_dict(sl_data, idx, all_input_ids)
                slides.append(slide)

        return Report(
            report_id=report_id,
            title=title,
            subtitle=subtitle,
            author=author,
            date=date,
            created_at=created_at,
            template_set=template_set,
            sections=sections,
            slides=slides,
            all_input_ids=all_input_ids
        )

    @staticmethod
    def _parse_slide_dict(sl_data: Dict[str, Any], slide_idx: int, all_input_ids: List[str]) -> Slide:
        template_id = sl_data.get("template_id", "05_insight_information")
        slide_id = sl_data.get("slide_id", f"slide_{slide_idx + 1:02d}_{template_id}")
        title = sl_data.get("title")
        raw_data = sl_data.get("data", sl_data.get("content", {}))

        slide_data = SlideData()
        slide_prefix = f"s{slide_idx + 1}"

        # Parse regions / content blocks
        for region_name, content in raw_data.items():
            if isinstance(content, dict):
                parsed = ReportParser._parse_content_item(content, f"{slide_prefix}_{region_name}", all_input_ids)
                slide_data.regions[region_name] = parsed
            elif isinstance(content, list):
                # Could be a list of blocks or list of items
                parsed_list = []
                for b_idx, block in enumerate(content):
                    if isinstance(block, dict):
                        b_parsed = ReportParser._parse_content_item(block, f"{slide_prefix}_{region_name}_{b_idx}", all_input_ids)
                        parsed_list.append(b_parsed)
                    else:
                        parsed_list.append(block)
                slide_data.regions[region_name] = parsed_list
            else:
                # Primitive scalar (string or number)
                item_id = f"{slide_prefix}_{region_name}"
                all_input_ids.append(item_id)
                slide_data.regions[region_name] = TextBlock(id=item_id, text=str(content))

        return Slide(
            slide_id=slide_id,
            template_id=template_id,
            slide_index=slide_idx,
            data=slide_data,
            title=title
        )

    @staticmethod
    def _parse_content_item(c_dict: dict, base_id: str, all_input_ids: list):
        c_type = c_dict.get("type")
        if not c_type:
            if "number" in c_dict and "title" in c_dict:
                c_type = "index_item" if ("." in str(c_dict.get("number", ""))) else "toc_item"
            elif "headers" in c_dict and "rows" in c_dict:
                c_type = "table"
            elif "series" in c_dict or "chart_type" in c_dict:
                c_type = "chart"
            elif "items" in c_dict and isinstance(c_dict.get("items"), list):
                c_type = "bullet_list"
            elif "blocks" in c_dict or ("title" in c_dict and "body" in c_dict):
                c_type = "insight"
            else:
                c_type = "text"
        item_id = c_dict.get("id", base_id)
        all_input_ids.append(item_id)

        if c_type == "text":
            return TextBlock(
                id=item_id,
                text=str(c_dict.get("value", c_dict.get("text", ""))),
                role=c_dict.get("role", "body"),
                style=c_dict.get("style", {})
            )
        elif c_type == "bullet_list":
            items = []
            for i, raw_item in enumerate(c_dict.get("items", [])):
                sub_id = raw_item.get("id", f"{item_id}_b{i}") if isinstance(raw_item, dict) else f"{item_id}_b{i}"
                all_input_ids.append(sub_id)
                text = raw_item.get("text", str(raw_item)) if isinstance(raw_item, dict) else str(raw_item)
                lvl = raw_item.get("level", 0) if isinstance(raw_item, dict) else 0
                items.append(BulletItem(id=sub_id, text=text, level=lvl))
            return BulletListBlock(id=item_id, items=items)

        elif c_type == "table":
            headers = c_dict.get("headers", [])
            rows = []
            for r_idx, r_raw in enumerate(c_dict.get("rows", [])):
                if isinstance(r_raw, dict):
                    row_id = r_raw.get("id", f"{item_id}_r{r_idx}")
                    all_input_ids.append(row_id)
                    cells = []
                    raw_cells = r_raw.get("cells", [])
                    for c_idx, cell_item in enumerate(raw_cells):
                        if isinstance(cell_item, dict):
                            c_id = cell_item.get("id", f"{row_id}_c{c_idx}")
                            c_val = cell_item.get("value", cell_item.get("text", ""))
                        else:
                            c_id = f"{row_id}_c{c_idx}"
                            c_val = str(cell_item)
                        all_input_ids.append(c_id)
                        cells.append(TableCell(id=c_id, value=c_val))
                    rows.append(TableRow(id=row_id, cells=cells))
                else:
                    row_id = f"{item_id}_r{r_idx}"
                    all_input_ids.append(row_id)
                    cells = []
                    for c_idx, cell_val in enumerate(r_raw):
                        c_id = f"{row_id}_c{c_idx}"
                        all_input_ids.append(c_id)
                        cells.append(TableCell(id=c_id, value=cell_val))
                    rows.append(TableRow(id=row_id, cells=cells))
            return TableBlock(
                id=item_id,
                headers=headers,
                rows=rows,
                column_widths=c_dict.get("column_widths"),
                style=c_dict.get("style", {})
            )

        elif c_type == "chart":
            series_list = []
            raw_data = c_dict.get("data", {})
            series_data = raw_data.get("series", c_dict.get("series", []))
            for s_idx, s in enumerate(series_data):
                s_name = s.get("name", f"Series {s_idx + 1}")
                vals = s.get("values", [])
                series_list.append(ChartSeries(name=s_name, values=vals))
            categories = raw_data.get("categories", c_dict.get("categories", []))
            for cat_idx, cat in enumerate(categories):
                all_input_ids.append(f"{item_id}_cat_{cat_idx}")
            return ChartBlock(
                id=item_id,
                chart_type=c_dict.get("chart_type", "bar"),
                categories=categories,
                series=series_list,
                title=c_dict.get("title"),
                options=c_dict.get("options", {})
            )

        elif c_type == "insight":
            if "blocks" in c_dict and isinstance(c_dict.get("blocks"), list):
                blocks = []
                for b_idx, b in enumerate(c_dict.get("blocks", [])):
                    b_id = b.get("id", f"{item_id}_block_{b_idx}")
                    all_input_ids.append(b_id)
                    blocks.append(InsightBlock(
                        id=b_id,
                        title=b.get("title", ""),
                        body=b.get("body", b.get("text", "")),
                        icon=b.get("icon")
                    ))
                return blocks if len(blocks) > 1 else (blocks[0] if blocks else InsightBlock(id=item_id, title="", body=""))
            else:
                return InsightBlock(
                    id=item_id,
                    title=c_dict.get("title", ""),
                    body=c_dict.get("body", c_dict.get("text", "")),
                    icon=c_dict.get("icon")
                )

        elif c_type == "image":
            return ImageBlock(
                id=item_id,
                src=c_dict.get("src", ""),
                alt=c_dict.get("alt", ""),
                fit=c_dict.get("fit", "contain")
            )

        elif c_type == "toc_item":
            return TOCItem(
                id=item_id,
                number=str(c_dict.get("number", "")),
                title=str(c_dict.get("title", ""))
            )

        elif c_type == "index_item":
            return IndexItem(
                id=item_id,
                number=str(c_dict.get("number", "")),
                title=str(c_dict.get("title", ""))
            )

        # Fallback
        return c_dict
