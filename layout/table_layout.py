"""
Dynamic Table Layout Engine
Calculates column widths, independent cell wrapping, natural vs allocated row heights,
and vertical/horizontal table splitting with repeated header rows.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from layout.text_measurement import measure_multiline_text, measure_single_line
from models.report_model import TableBlock, TableRow, TableCell


@dataclass
class CellLayout:
    text: str
    width: float
    height: float
    lines: List[str]
    font_size: float
    align: str = "left"


@dataclass
class RowLayout:
    cells: List[CellLayout]
    natural_height: float
    allocated_height: float
    is_header: bool = False


@dataclass
class TableLayoutResult:
    column_widths: List[float]
    rows: List[RowLayout]
    total_width: float
    total_height: float
    fits: bool
    font_size: float
    continuation_table: Optional['TableLayoutResult'] = None
    row_split_index: Optional[int] = None


class TableLayoutEngine:
    """
    Reusable layout engine for tables across 04_table_chart, 06_large_table, 08_multi_table_dashboard_2col.
    """

    @staticmethod
    def calculate_column_widths(
        headers: List[str],
        rows: List[List[str]],
        available_width: float,
        min_col_width: float = 60.0,
        font_name: str = "arial",
        font_size: int = 10
    ) -> List[float]:
        num_cols = len(headers)
        if num_cols == 0:
            return []

        # 1. Find max natural width needed per column
        col_max_widths = []
        for c in range(num_cols):
            # Header width
            h_text = str(headers[c]) if c < len(headers) else ""
            w_h, _ = measure_single_line(h_text, font_name, font_size)
            max_w = max(w_h + 16, min_col_width)

            # Sample row values
            for r in rows:
                if c < len(r):
                    val_str = str(r[c]) if r[c] is not None else ""
                    # For long sentences, clamp single-line width to prevent one column from taking over
                    w_cell, _ = measure_single_line(val_str[:60], font_name, font_size)
                    max_w = max(max_w, min(w_cell + 16, available_width * 0.5))

            col_max_widths.append(max_w)

        # 2. Normalize to available_width
        sum_widths = sum(col_max_widths)
        if sum_widths <= 0:
            return [available_width / num_cols] * num_cols

        scale = available_width / sum_widths
        allocated_widths = [max(min_col_width, w * scale) for w in col_max_widths]

        # Adjust any rounding discrepancy
        diff = available_width - sum(allocated_widths)
        allocated_widths[-1] += diff

        return allocated_widths

    @staticmethod
    def layout_table(
        headers: List[str],
        rows: List[List[Any]],
        available_width: float,
        available_height: float,
        preferred_font_size: int = 10,
        minimum_font_size: int = 8,
        min_row_height: float = 33.0,
        padding_y: float = 8.0,
        font_name: str = "arial",
        min_col_width: float = 60.0
    ) -> TableLayoutResult:
        """
        Lays out a table, independently measuring each cell.
        Natural row height = max(cell heights in row) + padding.
        Allocated row height = max(natural_height, min_row_height).
        Splits table vertically if it exceeds available_height.
        """
        num_cols = len(headers)
        col_widths = TableLayoutEngine.calculate_column_widths(
            headers, rows, available_width, min_col_width=min_col_width, font_name=font_name, font_size=preferred_font_size
        )

        font_size = preferred_font_size
        best_rows_layout = []
        total_h = 0.0

        def build_row_layout(r_data: List[Any], is_header: bool, f_size: int) -> RowLayout:
            cell_layouts = []
            max_cell_h = 0.0

            for col_idx in range(num_cols):
                w = col_widths[col_idx]
                val = r_data[col_idx] if col_idx < len(r_data) else ""
                val_str = str(val) if val is not None else ""

                # Measure with wrapping inside cell width (minus padding)
                inner_w = max(10.0, w - 12.0)
                meas = measure_multiline_text(val_str, font_name, f_size, inner_w, line_spacing=1.15)
                cell_h = meas["height"]
                if cell_h > max_cell_h:
                    max_cell_h = cell_h

                cell_layouts.append(CellLayout(
                    text=val_str,
                    width=w,
                    height=cell_h,
                    lines=meas["lines"],
                    font_size=f_size,
                    align="center" if (is_header or val_str.replace('.', '', 1).isdigit()) else "left"
                ))

            max_lines = max((len(c.lines) for c in cell_layouts), default=1)
            if max_lines > 1:
                natural_h = max_cell_h + padding_y
                allocated_h = max(natural_h, min_row_height)
            else:
                natural_h = min_row_height
                allocated_h = min_row_height

            return RowLayout(
                cells=cell_layouts,
                natural_height=natural_h,
                allocated_height=allocated_h,
                is_header=is_header
            )

        # Header layout
        header_layout = build_row_layout(headers, is_header=True, f_size=font_size)
        rows_layout = [header_layout]
        total_h = header_layout.allocated_height

        for r in rows:
            rl = build_row_layout(r, is_header=False, f_size=font_size)
            rows_layout.append(rl)
            total_h += rl.allocated_height

        # Check if table fits vertically
        if total_h <= available_height + 1.0:
            return TableLayoutResult(
                column_widths=col_widths,
                rows=rows_layout,
                total_width=available_width,
                total_height=total_h,
                fits=True,
                font_size=font_size
            )

        # Step 2: Try reducing font size within limits
        while font_size > minimum_font_size:
            font_size -= 1
            h_layout = build_row_layout(headers, is_header=True, f_size=font_size)
            test_rows = [h_layout]
            test_h = h_layout.allocated_height

            for r in rows:
                rl = build_row_layout(r, is_header=False, f_size=font_size)
                test_rows.append(rl)
                test_h += rl.allocated_height

            if test_h <= available_height + 1.0:
                return TableLayoutResult(
                    column_widths=col_widths,
                    rows=test_rows,
                    total_width=available_width,
                    total_height=test_h,
                    fits=True,
                    font_size=font_size
                )

        # Step 3: Vertical row splitting for continuation table
        # Header is preserved in both tables
        primary_rows = [header_layout]
        continuation_rows_data = []
        current_h = header_layout.allocated_height
        split_idx = None

        for idx, r in enumerate(rows):
            rl = build_row_layout(r, is_header=False, f_size=font_size)
            if current_h + rl.allocated_height <= available_height:
                primary_rows.append(rl)
                current_h += rl.allocated_height
            else:
                if split_idx is None:
                    split_idx = idx
                continuation_rows_data.append(r)

        # Build continuation table layout
        cont_table = None
        if continuation_rows_data:
            cont_table = TableLayoutEngine.layout_table(
                headers=headers,
                rows=continuation_rows_data,
                available_width=available_width,
                available_height=available_height,
                preferred_font_size=font_size,
                minimum_font_size=minimum_font_size,
                min_row_height=min_row_height,
                padding_y=padding_y,
                font_name=font_name,
                min_col_width=min_col_width
            )

        return TableLayoutResult(
            column_widths=col_widths,
            rows=primary_rows,
            total_width=available_width,
            total_height=current_h,
            fits=False,
            font_size=font_size,
            continuation_table=cont_table,
            row_split_index=split_idx
        )
