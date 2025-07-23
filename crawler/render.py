"""
Rendering logic for endpoint discovery.
- CLI: minimal columns (endpoint, method, confidence, source, location)
- CSV/Markdown/JSON/Postman: all fields (flattened extras)
"""

from rich.table import Table
from rich.console import Console
import json
import csv
import sys

# Preferred CLI columns (minimal)
PREFERRED_CLI = [
    "endpoint", "method", "confidence", "source", "location"
]

def render_cli(records):
    """
    Render a visually-rich CLI table using Rich with only minimal columns.
    Location = file:line.
    """
    if not records:
        print("No endpoints found.")
        return

    table = Table(show_header=True, header_style="bold magenta")
    for col in PREFERRED_CLI:
        col_title = col.title()
        table.add_column(col_title, overflow="fold", no_wrap=False)

    for rec in records:
        # Compose location column
        file = rec.get("file", "")
        line = rec.get("line", "")
        location = f"{file}:{line}" if file or line else ""

        # Compose method (safe for list/tuple)
        method = rec.get("method", "")
        if isinstance(method, (list, tuple)):
            method = ",".join(str(m) for m in method)
        elif method is None:
            method = ""

        # Confidence as float, formatted
        confidence = rec.get("confidence", "")
        if confidence != "":
            try:
                confidence = f"{float(confidence):.2f}"
            except Exception:
                pass

        # Only the minimal columns
        row = [
            str(rec.get("endpoint", "")),
            method,
            confidence,
            str(rec.get("source", "")),
            location
        ]
        table.add_row(*row)
    Console().print(table)

# --- For other outputs, keep all columns and flatten extras as before ---

def get_columns(records, preferred=None):
    all_keys = set()
    for rec in records:
        all_keys.update(rec.keys())
        if "extra" in rec and isinstance(rec["extra"], dict):
            all_keys.update(f"extra.{k}" for k in rec["extra"].keys())
    preferred = preferred or []
    columns = [col for col in preferred if col in all_keys]
    extra_cols = sorted(k for k in all_keys if k not in columns)
    return columns + extra_cols

def flatten_row(rec, columns):
    row = []
    for col in columns:
        if col.startswith("extra."):
            _, key = col.split(".", 1)
            val = rec.get("extra", {}).get(key, "")
        else:
            val = rec.get(col, "")
            if isinstance(val, (list, tuple)):
                val = ",".join(str(x) for x in val)
        row.append(str(val) if val is not None else "")
    return row

def render_json(records, output=None):
    text = json.dumps(records, indent=2)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)

def render_csv(records, output=None):
    if not records:
        print("No endpoints found.")
        return
    preferred = [
        "endpoint", "method", "confidence", "source",
        "controller", "line", "file"
    ]
    columns = get_columns(records, preferred)
    if output:
        f = open(output, "w", newline="", encoding="utf-8")
    else:
        f = sys.stdout
    writer = csv.writer(f)
    writer.writerow(columns)
    for rec in records:
        writer.writerow(flatten_row(rec, columns))
    if output:
        f.close()

def render_markdown(records, output=None):
    if not records:
        print("No endpoints found.")
        return
    preferred = [
        "endpoint", "method", "confidence", "source",
        "controller", "line", "file"
    ]
    columns = get_columns(records, preferred)
    lines = []
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for rec in records:
        row = flatten_row(rec, columns)
        lines.append("| " + " | ".join(row) + " |")
    output_text = "\n".join(lines)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(output_text)
    else:
        print(output_text)

def render_postman(records, output=None):
    collection = {
        "info": {
            "name": "Endpoint Discovery",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }
    for r in records:
        method_val = r.get("method") or "GET"
        if isinstance(method_val, (list, tuple)):
            method = ",".join(method_val)
        else:
            method = str(method_val) or "GET"
        endpoint = r.get("endpoint", "")
        request = {
            "method": method,
            "header": [],
            "url": {
                "raw": "{{baseUrl}}{}".format(endpoint),
                "host": ["{{baseUrl}}"],
                "path": endpoint.lstrip("/").split("/") if endpoint else []
            }
        }
        collection["item"].append({
            "name": f"{method} {endpoint}",
            "request": request
        })
    output_text = json.dumps(collection, indent=2)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(output_text)
    else:
        print(output_text)
