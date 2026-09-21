"""
Stack Layout Engine
Calculates dynamic vertical stacking of arbitrary content blocks (headings, paragraphs,
bullets, insights, tables) with automatic spacing reduction when needed.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from layout.text_measurement import measure_multiline_text, fit_text_to_budget
from layout.table_layout import TableLayoutEngine
from models.report_model import TextBlock, BulletListBlock, TableBlock, InsightBlock, IndexItem


@dataclass
class StackedBlockLayout:
    block_id: str
    block_type: str
    x: float
    y: float
    width: float
    height: float
    font_size: float
    data: Any
    fits: bool


@dataclass
class ColumnStackResult:
    blocks: List[StackedBlockLayout]
    total_height: float
    available_height: float
    gap: float
    fits: bool
    overflow_blocks: List[Any] = field(default_factory=list)


class StackLayoutEngine:
    @staticmethod
    def layout_vertical_stack(
        blocks: List[Any],
        x: float,
        start_y: float,
        width: float,
        available_height: float,
        preferred_gap: float = 16.0,
        minimum_gap: float = 8.0,
        font_name: str = "arial"
    ) -> ColumnStackResult:
        """
        Stacks heterogeneous blocks vertically.
        If total height exceeds available_height, reduces gap down to minimum_gap,
        then trims/splits excess blocks into overflow_blocks.
        """
        if not blocks:
            return ColumnStackResult(blocks=[], total_height=0.0, available_height=available_height, gap=preferred_gap, fits=True)

        current_gap = preferred_gap

        def measure_all(gap: float) -> Tuple[List[StackedBlockLayout], float, bool]:
            layouts = []
            curr_y = start_y

            for idx, block in enumerate(blocks):
                b_type, b_h, b_fsize, b_id = StackLayoutEngine._measure_block(block, width, font_name)
                
                # Check fit
                fits = (curr_y + b_h - start_y) <= available_height + 0.5
                layouts.append(StackedBlockLayout(
                    block_id=b_id,
                    block_type=b_type,
                    x=x,
                    y=curr_y,
                    width=width,
                    height=b_h,
                    font_size=b_fsize,
                    data=block,
                    fits=fits
                ))

                curr_y += b_h
                if idx < len(blocks) - 1:
                    curr_y += gap

            total_consumed = curr_y - start_y
            all_fit = total_consumed <= available_height + 0.5
            return layouts, total_consumed, all_fit

        # 1. Try with preferred gap
        layouts, total_h, all_fit = measure_all(preferred_gap)
        if all_fit:
            return ColumnStackResult(blocks=layouts, total_height=total_h, available_height=available_height, gap=preferred_gap, fits=True)

        # 2. Try reducing gap down to minimum_gap
        step_gap = preferred_gap
        while step_gap > minimum_gap:
            step_gap -= 2.0
            layouts, total_h, all_fit = measure_all(step_gap)
            if all_fit:
                return ColumnStackResult(blocks=layouts, total_height=total_h, available_height=available_height, gap=step_gap, fits=True)

        # 3. If still overflows with minimum_gap, partition into fitting and overflow blocks
        fitting_blocks = []
        overflow_blocks = []
        curr_y = start_y

        for idx, block in enumerate(blocks):
            b_type, b_h, b_fsize, b_id = StackLayoutEngine._measure_block(block, width, font_name)

            # If a bullet list overflows, split its items across pages instead of overflowing
            if isinstance(block, BulletListBlock) and len(block.items) > 1 and (curr_y + b_h - start_y > available_height + 0.5):
                fit_items = []
                rem_items = []
                item_y = curr_y
                for it in block.items:
                    indent = it.level * 16.0
                    meas = measure_multiline_text(it.text, font_name, 11, max(20.0, width - indent - 20.0), line_spacing=1.15)
                    it_h = meas["height"] + 6.0
                    if (item_y + it_h - start_y <= available_height + 0.5) or len(fit_items) == 0:
                        fit_items.append(it)
                        item_y += it_h
                    else:
                        rem_items.append(it)
                if fit_items:
                    fit_b = BulletListBlock(id=block.id, type="bullet_list", items=fit_items)
                    _, fit_h, fit_f, fit_id = StackLayoutEngine._measure_block(fit_b, width, font_name)
                    fitting_blocks.append(StackedBlockLayout(
                        block_id=fit_id,
                        block_type="bullet_list",
                        x=x,
                        y=curr_y,
                        width=width,
                        height=fit_h,
                        font_size=fit_f,
                        data=fit_b,
                        fits=True
                    ))
                    curr_y += fit_h + minimum_gap
                if rem_items:
                    rem_b = BulletListBlock(id=f"{block.id}_cont", type="bullet_list", items=rem_items)
                    overflow_blocks.append(rem_b)
                continue

            can_fit = ((curr_y + b_h - start_y) <= available_height + 0.5) or (len(fitting_blocks) == 0)
            if can_fit:
                fitting_blocks.append(StackedBlockLayout(
                    block_id=b_id,
                    block_type=b_type,
                    x=x,
                    y=curr_y,
                    width=width,
                    height=b_h,
                    font_size=b_fsize,
                    data=block,
                    fits=True
                ))
                curr_y += b_h + minimum_gap
            else:
                overflow_blocks.append(block)

        return ColumnStackResult(
            blocks=fitting_blocks,
            total_height=curr_y - start_y - minimum_gap,
            available_height=available_height,
            gap=minimum_gap,
            fits=False,
            overflow_blocks=overflow_blocks
        )

    @staticmethod
    def _measure_block(block: Any, width: float, font_name: str) -> Tuple[str, float, float, str]:
        """Returns (block_type, measured_height, font_size, block_id)."""
        b_id = getattr(block, "id", "block_unknown")

        if isinstance(block, TextBlock):
            f_size = 14 if block.role == "heading" else (16 if block.role == "title" else 11)
            meas = measure_multiline_text(block.text, font_name, f_size, width, line_spacing=1.2)
            return ("text", meas["height"] + 4.0, f_size, b_id)

        elif isinstance(block, BulletListBlock):
            f_size = 11
            total_h = 0.0
            for item in block.items:
                indent = item.level * 16.0
                meas = measure_multiline_text(item.text, font_name, f_size, max(20.0, width - indent - 20.0), line_spacing=1.15)
                total_h += meas["height"] + 6.0
            return ("bullet_list", total_h, f_size, b_id)

        elif isinstance(block, TableBlock):
            f_size = 9
            # Quick estimate
            rows_data = [[c.value for c in r.cells] for r in block.rows]
            table_res = TableLayoutEngine.layout_table(
                headers=block.headers,
                rows=rows_data,
                available_width=width,
                available_height=9999.0,
                preferred_font_size=f_size,
                minimum_font_size=8,
                min_row_height=33.0,
                font_name=font_name
            )
            return ("table", table_res.total_height + 12.0, f_size, b_id)

        elif isinstance(block, InsightBlock):
            f_size = 10
            meas_t = measure_multiline_text(block.title, font_name, 11, width - 24.0)
            meas_b = measure_multiline_text(block.body, font_name, f_size, width - 24.0)
            h = meas_t["height"] + meas_b["height"] + 20.0  # Card padding
            return ("insight", max(60.0, h), f_size, b_id)

        elif isinstance(block, IndexItem):
            f_size = 13
            meas = measure_multiline_text(block.title, font_name, f_size, max(20.0, width - 50.0))
            return ("index_item", max(28.0, meas["height"] + 8.0), f_size, b_id)

        # Fallback string or dict
        text_val = getattr(block, "text", str(block))
        meas = measure_multiline_text(text_val, font_name, 11, width)
        return ("text", meas["height"] + 4.0, 11, b_id)
