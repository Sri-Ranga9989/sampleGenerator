"""
Dynamic Chart Layout Engine
Calculates chart sizing, margins, plot area, and legend layout for Bar, Line, and Pie charts.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from layout.text_measurement import measure_single_line


@dataclass
class ChartLayoutResult:
    chart_type: str
    width: float
    height: float
    plot_width: float
    plot_height: float
    legend_position: str  # right, bottom, top, none
    legend_width: float
    legend_height: float
    show_data_labels: bool
    font_size: float
    categories: List[str]
    series_names: List[str]
    fits: bool

    @property
    def has_legend(self) -> bool:
        return self.legend_position != "none"


class ChartLayoutEngine:
    @staticmethod
    def layout_chart(
        chart_type: str,
        categories: List[str],
        series_names: List[str],
        available_width: float,
        available_height: float,
        title: Optional[str] = None
    ) -> ChartLayoutResult:
        """
        Determines plot area, legend location, margins, and label clearances.
        """
        chart_type = chart_type.lower()
        num_categories = len(categories)
        num_series = len(series_names)

        # Title margin
        title_h = 35.0 if title else 0.0

        # Legend placement decision
        # If line chart with multiple series or pie with <= 6 categories, legend on right or bottom
        if chart_type == "pie":
            legend_pos = "right" if available_width >= 500 else "bottom"
            legend_w = 120.0 if legend_pos == "right" else available_width
            legend_h = available_height * 0.4 if legend_pos == "right" else 40.0
            show_labels = True
        elif num_series > 1:
            legend_pos = "top"
            legend_w = available_width
            legend_h = 30.0
            show_labels = (num_categories <= 8)
        else:
            # Single series bar chart
            legend_pos = "none"
            legend_w = 0.0
            legend_h = 0.0
            show_labels = (num_categories <= 10)

        # Axis clearance
        axis_x_clearance = 60.0  # Y-axis numbers
        axis_y_clearance = 45.0  # X-axis category labels

        # Plot dimensions
        plot_w = max(100.0, available_width - axis_x_clearance - (legend_w if legend_pos == "right" else 0.0))
        plot_h = max(100.0, available_height - title_h - axis_y_clearance - (legend_h if legend_pos in ["top", "bottom"] else 0.0))

        # Check font sizing
        font_size = 10.0
        if num_categories > 12:
            font_size = 8.5
        elif num_categories > 8:
            font_size = 9.0

        fits = (plot_w >= 150.0) and (plot_h >= 120.0)

        return ChartLayoutResult(
            chart_type=chart_type,
            width=available_width,
            height=available_height,
            plot_width=plot_w,
            plot_height=plot_h,
            legend_position=legend_pos,
            legend_width=legend_w,
            legend_height=legend_h,
            show_data_labels=show_labels,
            font_size=font_size,
            categories=categories,
            series_names=series_names,
            fits=fits
        )
