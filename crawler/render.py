"""
Rendering logic for endpoint discovery.

- CLI table (Rich): Beautiful, colored, all columns present.
- CSV: Consistent columns, flattened extras, easy to import.
- Markdown: GitHub-flavored table, all columns.
- JSON: Pretty and direct (all fields, including extra).
- Postman: As before.
"""

from rich.table import Table
from rich.console import Console
import json
import csv
import sys

def get_columns(records, preferred=None):
    """
    Return a list of all keys found in records, preferring 'preferred' order.
    Flattens any 'extra' dict keys as 'extra.<key>'.
    """
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
    """
    Build a flat row for CSV/Markdown/CLI, with all extras flattened.
    """
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

def render_cli(records):
    """
    Render records as a visually-rich CLI table using Rich.
    All columns shown, including confidence, source, and extra fields.
    """
    if not records:
        print("No endpoints found.")
        return

    preferred = [
        "endpoint", "method", "confidence", "source",
        "controller", "line", "file"
    ]
    columns = get_columns(records, preferred)
    table = Table(show_header=True, header_style="bold magenta")
    for col in columns:
        table.add_column(col.title(), overflow="fold", no_wrap=False)
    for rec in records:
        row = flatten_row(rec, columns)
        table.add_row(*row)
    Console().print(table)

def render_json(records, output=None):
    """
    Render records as pretty JSON.
    """
    text = json.dumps(records, indent=2)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)

def render_csv(records, output=None):
    """
    Render records as CSV with consistent columns.
    """
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
    """
    Render records as a GitHub-flavored markdown table with all columns.
    """
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
    """
    Render records as a Postman collection (v2.1.0).
    """
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
