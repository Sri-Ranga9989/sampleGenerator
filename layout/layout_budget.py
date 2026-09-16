"""
Universal Layout Budget Concept
Tracks available space vs required space across all slide regions and content blocks.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LayoutBudget:
    available_width: float
    available_height: float
    consumed_width: float = 0.0
    consumed_height: float = 0.0

    @property
    def remaining_width(self) -> float:
        return max(0.0, self.available_width - self.consumed_width)

    @property
    def remaining_height(self) -> float:
        return max(0.0, self.available_height - self.consumed_height)

    def fits(self, required_width: float, required_height: float) -> bool:
        """Determines if a block fits within remaining budget."""
        return (required_width <= self.remaining_width + 0.5) and (required_height <= self.remaining_height + 0.5)

    def consume(self, width: float, height: float):
        """Consumes budget vertically."""
        self.consumed_height += height
        self.consumed_width = max(self.consumed_width, width)

    def reset_consumption(self):
        self.consumed_width = 0.0
        self.consumed_height = 0.0


@dataclass
class BlockMeasurement:
    required_width: float
    required_height: float
    fits: bool
    font_size: float
    line_count: int = 1
    excess_height: float = 0.0
