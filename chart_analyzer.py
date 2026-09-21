"""
chart_analyzer.py
Analyzes parsed table data to determine if a chart can be derived from it.
For each graph-worthy table, generates a ChartBlock-compatible dict.

Reuses the existing canonical schema from models/report_model.py.
"""

import re
from typing import List, Dict, Any, Optional, Tuple


# Patterns for extracting numeric values from formatted strings
NUMERIC_PATTERNS = [
    # $4.7 Bn, $5.9 Bn, ~$9.8 Bn
    (r'~?\$?([\d,.]+)\s*[Bb](?:n|illion)', 1_000_000_000),
    # $991 Mn, $347.7 Mn, ~$650 Mn
    (r'~?\$?([\d,.]+)\s*[Mm](?:n|illion)', 1_000_000),
    # €5.502 Bn, €1.576 Bn
    (r'~?€([\d,.]+)\s*[Bb](?:n|illion)', 1_000_000_000),
    # €434 Mn
    (r'~?€([\d,.]+)\s*[Mm](?:n|illion)', 1_000_000),
    # 12.8%, ~14.9%, 40.9%
    (r'~?([\d.]+)\s*%', 1),
    # Plain numbers: 24.9k
    (r'~?([\d.]+)\s*k$', 1_000),
    # Units/trucks with commas or decimals: ~34,000 units
    (r'^~?([\d,]+(?:\.\d+)?)\s*(?:units?|trucks?)$', 1),
    # Plain numbers: 3.43, ~34,000, 5.90
    (r'^~?\$?([\d,]+(?:\.\d+)?)$', 1),
]


def parse_numeric_value(text: str) -> Optional[float]:
    """
    Attempts to extract a numeric value from a formatted string.
    Returns the numeric value or None if not parseable.
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip().replace('\xa0', ' ')
    
    # Skip clearly non-numeric
    if text in ('—', '–', '-', '', 'N/A', 'n/a', 'Total', 'total'):
        return None
    
    for pattern, multiplier in NUMERIC_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                val_str = match.group(1).replace(',', '')
                return float(val_str) * multiplier
            except (ValueError, IndexError):
                continue
    
    return None


def is_percentage_column(values: List[str]) -> bool:
    """Check if a column contains mostly percentage values."""
    pct_count = sum(1 for v in values if '%' in str(v))
    return pct_count >= len(values) * 0.5


def is_year_header(header: str) -> bool:
    """Check if a header looks like a year (2021, 2024A, 2026E, 2030F)."""
    return bool(re.match(r'^\d{4}[AaEeFf]?$', header.strip()))


def detect_chart_type(headers: List[str], rows: List[List[str]]) -> str:
    """
    Determines the best chart type based on data structure.
    
    Returns: 'line', 'bar', 'pie', or 'column_clustered'
    """
    # Check if headers contain years -> time series -> line chart
    year_headers = [h for h in headers[1:] if is_year_header(h)]
    if len(year_headers) >= 3:
        return "line"
    
    # Check if data has percentage columns (share data) -> pie or bar
    if len(headers) > 1:
        first_data_col = [row[1] if len(row) > 1 else '' for row in rows]
        if is_percentage_column(first_data_col):
            # If few rows (<=6), pie chart; otherwise bar
            if len(rows) <= 6:
                return "pie"
            return "bar"
    
    # Default: clustered column chart
    return "column_clustered"


def analyze_table_for_chart(
    table_id: str,
    headers: List[str],
    rows: List[List[str]],
    table_title: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Analyzes a table and determines if a chart can be generated.
    
    Rules for graph-worthiness:
    1. At least 2 columns (1 label + 1 numeric)
    2. At least 3 data rows
    3. At least 1 column with >=50% parseable numeric values
    
    Returns a chart block dict or None if not graph-worthy.
    """
    if not headers or not rows:
        return None
    
    if len(headers) < 2:
        return None
    
    if len(rows) < 3:
        return None
    
    # Analyze each column for numeric content
    numeric_columns = []
    for col_idx in range(1, len(headers)):
        col_values = []
        for row in rows:
            if col_idx < len(row):
                val = parse_numeric_value(str(row[col_idx]))
                col_values.append(val)
            else:
                col_values.append(None)
        
        # Count non-None values
        valid_count = sum(1 for v in col_values if v is not None)
        if valid_count >= len(rows) * 0.5:
            numeric_columns.append((col_idx, col_values))
    
    # Need at least 1 numeric column
    if not numeric_columns:
        return None
    
    # Skip tables where first column is also purely numeric (matrix tables)
    categories = []
    for row in rows:
        if row:
            cat = str(row[0]).strip()
            # Skip "Total" rows from categories
            if cat.lower() in ('total', 'total*', ''):
                continue
            categories.append(cat)
    
    if len(categories) < 3:
        return None
    
    # Determine chart type
    chart_type = detect_chart_type(headers, rows)
    
    # Build series data
    series = []
    for col_idx, col_values in numeric_columns[:4]:  # Limit to 4 series max
        series_name = headers[col_idx] if col_idx < len(headers) else f"Series {col_idx}"
        # Filter values to match categories (skip Total rows)
        filtered_values = []
        for row_idx, row in enumerate(rows):
            cat = str(row[0]).strip() if row else ''
            if cat.lower() in ('total', 'total*', ''):
                continue
            val = col_values[row_idx] if row_idx < len(col_values) else 0
            filtered_values.append(val if val is not None else 0)
        
        # Ensure values match categories length
        while len(filtered_values) < len(categories):
            filtered_values.append(0)
        filtered_values = filtered_values[:len(categories)]
        
        series.append({
            "name": series_name,
            "values": filtered_values
        })
    
    if not series:
        return None
    
    # Build chart title
    chart_title = table_title or f"Data from {table_id}"
    
    chart_block = {
        "type": "chart",
        "id": f"auto_chart_{table_id}",
        "chart_type": chart_type,
        "title": chart_title,
        "categories": categories,
        "series": series
    }
    
    return chart_block


def analyze_tables_for_charts(
    tables: List[Dict[str, Any]]
) -> List[Tuple[int, Dict[str, Any]]]:
    """
    Analyzes a list of table blocks and returns chart blocks for graph-worthy tables.
    
    Args:
        tables: List of table block dicts with 'id', 'headers', 'rows' keys
        
    Returns:
        List of (table_index, chart_block) tuples
    """
    results = []
    
    for idx, table in enumerate(tables):
        table_id = table.get("id", f"table_{idx}")
        headers = table.get("headers", [])
        
        # Extract row values from the structured format
        raw_rows = table.get("rows", [])
        flat_rows = []
        for row in raw_rows:
            if isinstance(row, dict):
                cells = row.get("cells", [])
                flat_row = []
                for cell in cells:
                    if isinstance(cell, dict):
                        flat_row.append(str(cell.get("value", "")))
                    else:
                        flat_row.append(str(cell))
                flat_rows.append(flat_row)
            elif isinstance(row, list):
                flat_rows.append([str(c) for c in row])
        
        title = table.get("_title", "")
        chart = analyze_table_for_chart(table_id, headers, flat_rows, title)
        
        if chart:
            results.append((idx, chart))
    
    return results
