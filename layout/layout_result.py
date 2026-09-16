"""
LayoutResult Intermediate Representation
The formal contract between the Layout Engine (geometry decisions)
and the PowerPoint Renderer (PowerPoint shape generation).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class RegionGeometry:
    region_id: str
    role: str
    x: float
    y: float
    width: float
    height: float


@dataclass
class ComponentGeometry:
    component_id: str
    component_type: str  # text, table, chart, bullet_list, toc_item, index_item, insight, image
    x: float
    y: float
    width: float
    height: float
    data: Any
    font_size: Optional[float] = None
    style: Dict[str, Any] = field(default_factory=dict)
    provenance_id: Optional[str] = None


@dataclass
class LayoutResult:
    slide_id: str
    slide_index: int
    template_id: str
    background: str
    title: Optional[str] = None
    regions: Dict[str, RegionGeometry] = field(default_factory=dict)
    components: List[ComponentGeometry] = field(default_factory=list)
    overflow_status: str = "FIT"  # FIT, SPLIT, CONTINUED
    continuation_slide: Optional['LayoutResult'] = None
    provenance_map: Dict[str, Dict[str, Any]] = field(default_factory=dict)
