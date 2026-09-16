# PPT Generator (Automated Market-Research PowerPoint Generator)

A production-grade, template-driven PowerPoint document layout engine designed to take structured report content (JSON) and generate presentations that faithfully reproduce the visual hierarchy, typography, data density, dynamic tables, charts, and spacing of premium research reports (such as the reference *Mining UGV Market* report).

---

## Final Template Registry

All 8 templates are defined with a consistent schema structure:

| # | Template ID | File | Primary Content | Continuation Target |
|---|---|---|---|---|
| 01 | `01_cover_title_image` | [`01_cover_title_image.json`](assets/templates/mining_ugv/annotations/01_cover_title_image.json) | Cover title, subtitle, metadata & hero visual | — |
| 02 | `02_toc_image` | [`02_toc_image.json`](assets/templates/mining_ugv/annotations/02_toc_image.json) | Diamond-badge TOC, 2-col × 9 items (max 18 items) | `02_toc_image` (Continuation TOC) |
| 03 | `03_section_opener` | [`03_section_opener.json`](assets/templates/mining_ugv/annotations/03_section_opener.json) | Section title + index list + visual | `05_insight_information` |
| 04 | `04_table_chart` | [`04_table_chart.json`](assets/templates/mining_ugv/annotations/04_table_chart.json) | Context note + chart (left) + heading/narrative/table/insight (right) | — |
| 05 | `05_insight_information` | [`05_insight_information.json`](assets/templates/mining_ugv/annotations/05_insight_information.json) | 2-col block containers (paragraphs, bullets, index, insight) | Self (`05_insight_information`) |
| 06 | `06_large_table` | [`06_large_table.json`](assets/templates/mining_ugv/annotations/06_large_table.json) | Title + one dominant table (~1705×902px) | Self (`06_large_table`) |
| 07 | `07_large_chart` | [`07_large_chart.json`](assets/templates/mining_ugv/annotations/07_large_chart.json) | Title + legend + one dominant chart (~1650×650px) | Self (`07_large_chart`) |
| 08 | `08_multi_table_dashboard_2col` | [`08_multi_table_dashboard_2col.json`](assets/templates/mining_ugv/annotations/08_multi_table_dashboard_2col.json) | 2-col dynamic blocks (heading, paragraph, bullet, table, insight, index) | Self (`08_multi_table_dashboard_2col`) |

---

## Overflow / Continuation Graph

Content is never silently truncated, hidden, or shrunken below readable limits. If content exceeds available container height or width, the layout engine splits rows/items or dispatches to continuation slides:

```mermaid
graph TD
    T02["02_toc_image (>18 items)"] -->|excess TOC items| T02_cont["02_toc_image (Continuation)"]
    T03["03_section_opener"] -->|excess index items| T05["05_insight_information"]
    T05 -->|excess content| T05
    T06["06_large_table"] -->|row/column split| T06
    T07["07_large_chart"] -->|continuation| T07
    T08["08_multi_table_dashboard_2col"] -->|excess blocks| T08
```

---

## Shared Renderer Architecture

Layout rendering logic is unified across all templates to prevent code duplication and guarantee visual consistency:

```mermaid
graph TD
    TR["table_renderer"] --> T04["04_table_chart"]
    TR --> T06["06_large_table"]
    TR --> T08["08_multi_table_dashboard_2col"]
    CR["chart_renderer"] --> T04
    CR --> T07["07_large_chart"]
    TXR["text_renderer"] --> ALL["All templates"]
    LR["list_renderer"] --> T02["02_toc_image"]
    LR --> T03["03_section_opener"]
    LR --> T05["05_insight_information"]
    LR --> T08["08_multi_table_dashboard_2col"]
```

---

## Backgrounds

The presentation system separates structural slide geometry from background assets:

| Asset | Metadata | Used By Templates |
|---|---|---|
| `bg_01.png` | [`bg_01.json`](assets/backgrounds/bg_01.json) | `02_toc_image`, `04_table_chart`, `05_insight_information`, `06_large_table`, `07_large_chart`, `08_multi_table_dashboard_2col` |
| `bg_02.png` | [`bg_02.json`](assets/backgrounds/bg_02.json) | `03_section_opener` |
| `bg_03.png` | [`bg_03.json`](assets/backgrounds/bg_03.json) | `01_cover_title_image` |

---

## Schemas

All configurations, template annotations, and content payloads are formally validated via JSON Schema (Draft-07):

| Schema | File | Purpose |
|---|---|---|
| Template Annotation | [`template.schema.json`](schemas/template.schema.json) | Validates template annotations. Region types: text, subtitle, image, table, chart, chart_component, bullet_list, insight, column, container, footer, source, section_label. Geometry: fixed, fixed_anchor, dynamic. |
| Content Input | [`content.schema.json`](schemas/content.schema.json) | Validates slide data payloads (text, table, chart, image, bullet_list, insight). |
| Report Manifest | [`report.schema.json`](schemas/report.schema.json) | Validates full deck manifests (ordered slides, defaults, report metadata). |
| Template Registry | [`template_registry.json`](schemas/template_registry.json) | Master registry mapping template IDs to annotations, backgrounds, and continuation strategies. |

---

## Canonical JSON Top-Level Keys

Every template annotation strictly adheres to this uniform schema:

```json
{
  "template_id": "...",
  "template_name": "...",
  "version": "...",
  "canvas": {},
  "background": {},
  "safe_area": {},
  "regions": {},
  "components": {},
  "layout": {},
  "typography": {},
  "spacing": {},
  "constraints": {},
  "overflow": {},
  "content_model": {}
}
```

---

## Core Engine Architecture

```
ppt-generator/
│
├── assets/
│   ├── backgrounds/               # High-res slide background templates (bg_01, bg_02, bg_03)
│   └── templates/
│       └── mining_ugv/
│           ├── annotations/       # Machine-readable JSON annotations for all 8 templates
│           ├── reference/         # Visual ground-truth reference images
│           └── rendered/          # Slide-by-slide rendered outputs for verification
│
├── schemas/                       # JSON Schemas (template, content, report, registry)
├── layout/                        # Deterministic layout, measurement, & overflow engines
│   ├── coordinate_system.py       # 1920x1080 px to PPTX EMU/inch coordinate mapper
│   ├── text_measurement.py        # Font-aware deterministic text measuring & wrapping
│   ├── table_layout.py            # Dynamic table row/col sizing, cell wrapping & splitting
│   ├── chart_layout.py            # Dynamic chart plot sizing & label positioning
│   ├── stack_layout.py            # Vertical stack layout with spacing compaction
│   └── overflow_engine.py         # Multi-phase overflow resolution & continuation logic
│
├── renderer/                      # PowerPoint element rendering layer (python-pptx)
│   ├── powerpoint_renderer.py     # Main deck assembler and PPTX generator
│   ├── template_renderer.py       # Slide-level template executor
│   ├── text_renderer.py           # Headings, paragraphs, index lists, TOC badges
│   ├── table_renderer.py          # Native editable PowerPoint tables
│   ├── chart_renderer.py          # Native editable PowerPoint charts (bar, line, pie)
│   ├── image_renderer.py          # Image placement with aspect ratio handling
│   └── component_renderer.py      # Reusable visual components (badges, cards, insights)
│
├── validators/                    # Quality assurance & compliance validators
│   ├── geometry_validator.py      # Boundary and safe-area enforcement
│   ├── text_validator.py          # Text clipping & font constraint checks
│   ├── table_validator.py         # Cell clipping & overflow checks
│   ├── chart_validator.py         # Chart label & plot area validation
│   └── completeness_validator.py  # Verifies 100% of input content was rendered
│
├── examples/                      # Synthetic reports and test datasets (simple to edge cases)
├── tests/                         # Unit and integration test suites
└── output/                        # Generated presentations (.pptx)
```

---

## Installation & Requirements

- Python 3.10+ on Windows / Linux / macOS
- Core Dependencies: `python-pptx`, `jsonschema`, `pillow`, `numpy`, `pywin32` (for Windows PowerPoint 16.0 COM rasterization)

```bash
pip install python-pptx jsonschema pillow numpy pywin32
```

---

## CLI Commands

The engine provides unified CLI tools via `python -m ppt_generator`:

### 1. Validate Input JSON Manifest
Validates input JSON schema (Draft-07) and canonical data model compatibility:
```bash
python -m ppt_generator validate-input --input examples/mining_ugv_report.json
```

### 2. Generate Full Presentation (.pptx)
Executes end-to-end pipeline (layout, measurement, overflow, PPTX construction, structural validation, completeness audit, and slide rasterization):
```bash
python -m ppt_generator generate --input examples/mining_ugv_report.json --output output/mining_ugv_report.pptx
```

### 3. Validate PPTX Presentation Structure
Evaluates PPTX shapes, coordinates, boundary overruns, and minimum font thresholds:
```bash
python -m ppt_generator validate-pptx --input output/mining_ugv_report.pptx
```

### 4. Render Single Template Archetype
Renders a specific slide archetype to an editable PowerPoint presentation:
```bash
python -m ppt_generator render-template --template-id 04_table_chart --input examples/mining_ugv_report.json --output output/single_template.pptx
```

### 5. Compare Rendered Slide Against Ground-Truth Reference
Compares rendered PNG against reference PNG; returns `SKIPPED` if reference image is absent:
```bash
python -m ppt_generator compare --reference assets/templates/mining_ugv/reference/01_cover_title_image.png --generated assets/templates/mining_ugv/rendered/01_cover_title_image.png
```

---

## Testing & Calibration Suites

### Comprehensive 19 Edge Case Stress Testing
Verifies row-specific cell expansion, TOC continuation, index list overflow routing, multi-slide table splitting, column width balancing, category density, and font clamps:
```bash
python -m unittest tests/test_stress_cases.py
```

### Individual Template Calibration (Phase 0.5)
Calibrates all 8 template archetypes with realistic reference data, generates PPTX, performs COM rasterization to 1920×1080 PNG, and runs structural and rendered validation:
```bash
python calibration/calibrate_templates.py
```

---

## Output Artifacts

- **Presentation:** [`output/mining_ugv_report.pptx`](output/mining_ugv_report.pptx) (9 slides, 100% complete)
- **Rendered High-Res PNGs:** `output/rendered/` (1920×1080 native rasterized slides)
- **Archetype Calibration Outputs:** `output/calibration/` and `assets/templates/mining_ugv/rendered/`
