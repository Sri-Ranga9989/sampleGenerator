"""
api_server.py
FastAPI server exposing endpoints for the HTML → JSON → PPTX pipeline.

Endpoints:
  POST /parse     - Upload HTML file, get JSON manifest back
  POST /generate  - Upload JSON manifest, get PPTX file back
  POST /pipeline  - Upload HTML file, get PPTX file back (end-to-end)
  GET  /health    - Health check
"""

import os
import json
import uuid
import tempfile
import shutil
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from html_parser import parse_html_to_json
from models.report_model import ReportParser
from renderer.template_renderer import TemplateRenderer
from renderer.powerpoint_renderer import PowerPointRenderer
from validators.structural_validator import StructuralValidator
from validators.completeness_validator import CompletenessValidator

app = FastAPI(
    title="PPT Generator V1 API",
    description="Automated HTML email → Consulting-grade PowerPoint pipeline",
    version="1.0.0"
)

OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "output")


def _ensure_output_dir(run_id: str) -> str:
    """Create and return the output directory for a run."""
    run_dir = os.path.join(OUTPUT_BASE, run_id)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "PPT Generator V1",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/parse")
async def parse_html(
    file: UploadFile = File(...),
    auto_charts: bool = Query(True, description="Auto-generate charts for graph-worthy tables")
):
    """
    Parse a Gmail HTML email file into a canonical JSON manifest.
    
    Upload an HTML file and receive the parsed JSON manifest.
    """
    if not file.filename.endswith(('.html', '.htm')):
        raise HTTPException(status_code=400, detail="File must be an HTML file (.html or .htm)")
    
    run_id = f"parse_{uuid.uuid4().hex[:8]}"
    run_dir = _ensure_output_dir(run_id)
    
    try:
        # Save uploaded file
        html_path = os.path.join(run_dir, file.filename)
        with open(html_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Parse
        json_path = os.path.join(run_dir, "report.json")
        report, stats, warnings = parse_html_to_json(
            html_path, json_path, auto_charts=auto_charts
        )
        
        # Save stats
        stats_path = os.path.join(run_dir, "stats.json")
        with open(stats_path, "w") as f:
            json.dump({"run_id": run_id, "stats": stats, "warnings": warnings}, f, indent=2)
        
        return JSONResponse(content={
            "status": "success",
            "run_id": run_id,
            "output_path": json_path,
            "stats": stats,
            "warnings": warnings[:20],
            "slide_count": len(report.get("slides", []))
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")


@app.post("/generate")
async def generate_pptx(
    file: UploadFile = File(...),
    no_rasterize: bool = Query(True, description="Skip COM rasterization")
):
    """
    Generate a PPTX presentation from a JSON manifest file.
    
    Upload a JSON manifest and receive the generated PPTX.
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file (.json)")
    
    run_id = f"gen_{uuid.uuid4().hex[:8]}"
    run_dir = _ensure_output_dir(run_id)
    
    try:
        # Save uploaded file
        json_path = os.path.join(run_dir, "report.json")
        with open(json_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Load and parse
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        report = ReportParser.parse_report_json(data)
        
        # Layout
        t_renderer = TemplateRenderer()
        layout_results = t_renderer.render_report_layout(report)
        
        # Render PPTX
        ppt_renderer = PowerPointRenderer()
        prs, prov_map = ppt_renderer.create_presentation(layout_results)
        
        pptx_path = os.path.join(run_dir, "report.pptx")
        prs.save(pptx_path)
        
        # Validate
        struct_res = StructuralValidator.validate_presentation(prs)
        comp_res = CompletenessValidator.validate_completeness(report.all_input_ids, prov_map)
        
        return FileResponse(
            pptx_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename="report.pptx",
            headers={
                "X-Run-Id": run_id,
                "X-Slides": str(len(layout_results)),
                "X-Structural-Status": struct_res["status"],
                "X-Completeness-Status": comp_res["status"],
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/pipeline")
async def full_pipeline(
    file: UploadFile = File(...),
    auto_charts: bool = Query(True, description="Auto-generate charts for graph-worthy tables")
):
    """
    Full end-to-end pipeline: HTML email → JSON → PPTX.
    
    Upload a Gmail HTML file and receive the generated PPTX presentation.
    """
    if not file.filename.endswith(('.html', '.htm')):
        raise HTTPException(status_code=400, detail="File must be an HTML file (.html or .htm)")
    
    run_id = f"pipe_{uuid.uuid4().hex[:8]}"
    run_dir = _ensure_output_dir(run_id)
    
    try:
        # Save uploaded file
        html_path = os.path.join(run_dir, file.filename)
        with open(html_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Step 1: Parse HTML → JSON
        json_path = os.path.join(run_dir, "report.json")
        report_data, stats, warnings = parse_html_to_json(
            html_path, json_path, auto_charts=auto_charts
        )
        
        # Step 2: JSON → PPTX
        report = ReportParser.parse_report_json(report_data)
        
        t_renderer = TemplateRenderer()
        layout_results = t_renderer.render_report_layout(report)
        
        ppt_renderer = PowerPointRenderer()
        prs, prov_map = ppt_renderer.create_presentation(layout_results)
        
        pptx_path = os.path.join(run_dir, "report.pptx")
        prs.save(pptx_path)
        
        # Step 3: Validate
        struct_res = StructuralValidator.validate_presentation(prs)
        comp_res = CompletenessValidator.validate_completeness(report.all_input_ids, prov_map)
        
        # Save stats
        full_stats = {
            "run_id": run_id,
            "parsing": stats,
            "generation": {
                "slides": len(layout_results),
                "input_items": len(report.all_input_ids),
                "structural_status": struct_res["status"],
                "completeness_status": comp_res["status"],
                "completeness_pct": comp_res.get("completeness_pct", 0),
            },
            "warnings": warnings,
        }
        stats_path = os.path.join(run_dir, "stats.json")
        with open(stats_path, "w") as f:
            json.dump(full_stats, f, indent=2)
        
        return FileResponse(
            pptx_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename="report.pptx",
            headers={
                "X-Run-Id": run_id,
                "X-Slides": str(len(layout_results)),
                "X-Tables": str(stats.get("data_tables", 0)),
                "X-Charts": str(stats.get("charts_generated", 0)),
                "X-Structural-Status": struct_res["status"],
                "X-Completeness-Status": comp_res["status"],
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
