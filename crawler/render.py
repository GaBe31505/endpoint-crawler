"""
Rendering logic for endpoint discovery.

- CLI: minimal, modern, colorized table for human scanning (Rich).
  Location column: filename (not full path) + line, one per line, for readability.
- CSV/Markdown/JSON/Postman: all columns, flattened extras, full paths preserved.
"""

import os
from rich.table import Table
from rich.console import Console
from rich import box
import json
import csv
import sys

# Columns to display in the CLI table
PREFERRED_CLI = [
    "endpoint", "method", "confidence", "source", "location"
]

def format_location_multiline(loc):
    """
    For CLI, show only the filename (not full path) for readability.
    - If list, each entry (file or file:line) is on its own line, showing only filename.
    - If tuple, show filename:line.
    - If single path, show only the basename.
    - All original data is retained for file outputs.
    """
    def short(x):
        # For (file, line) tuples/lists
        if isinstance(x, (tuple, list)) and len(x) == 2:
            return f"{os.path.basename(x[0])}:{x[1]}"
        # For just a file (path)
        return os.path.basename(str(x))
    if isinstance(loc, list):
        return "\n".join(short(x) for x in loc)
    elif isinstance(loc, (tuple, list)) and len(loc) == 2:
        return short(loc)
    return os.path.basename(str(loc))

def render_cli(records):
    """
    Render a modern, readable CLI table of endpoints using Rich.
    - One row per endpoint+location pair, even if the endpoint repeats.
    - Colorful, no banding, all fields shown, NO truncation.
    - Location column is always a single filename:line per row.
    """
    if not records:
        print("No endpoints found.")
        return

    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=box.SIMPLE_HEAD,
        show_lines=False,
        pad_edge=False
    )

    col_styles = {
        "endpoint": "bold blue",
        "method": "green",
        "confidence": "yellow",
        "source": "cyan",
        "location": "dim"
    }

    for col in PREFERRED_CLI:
        table.add_column(
            col.title(),
            style=col_styles.get(col, ""),
            no_wrap=False
        )

    # EXPAND: one row per location (classic behavior)
    expanded_records = []
    for rec in records:
        loc = rec.get("location", f"{rec.get('file','')}:{rec.get('line','')}")
        # If the location is a list, create a row for each item
        if isinstance(loc, list):
            for single_loc in loc:
                new_rec = rec.copy()
                new_rec["location"] = single_loc
                expanded_records.append(new_rec)
        else:
            rec["location"] = loc
            expanded_records.append(rec)

    for rec in expanded_records:
        location = format_location_multiline(rec["location"])
        method = rec.get("method", "")
        if isinstance(method, (list, tuple)):
            method = ",".join(str(m) for m in method)
        elif method is None:
            method = ""
        confidence = rec.get("confidence", "")
        if confidence != "":
            try:
                conf_val = float(confidence)
                confidence_fmt = f"{conf_val:.2f}"
            except Exception:
                conf_val = None
                confidence_fmt = str(confidence)
        else:
            conf_val = None
            confidence_fmt = ""
        endpoint = str(rec.get("endpoint", ""))
        source = str(rec.get("source", ""))

        # Highlight endpoints with high confidence
        endpoint_style = col_styles["endpoint"]
        if conf_val is not None and conf_val >= 0.90:
            endpoint_style += " bold underline"

        row = [
            f"[{endpoint_style}]{endpoint}[/]" if endpoint else "",
            f"[{col_styles['method']}]{method}[/]" if method else "",
            f"[{col_styles['confidence']}]{confidence_fmt}[/]" if confidence_fmt else "",
            f"[{col_styles['source']}]{source}[/]" if source else "",
            f"[{col_styles['location']}]{location}[/]" if location else "",
        ]
        table.add_row(*row)
    Console().print(table)

# --- Helpers for file outputs ---

def get_columns(records, preferred=None):
    """
    Return a list of all keys found in records, with preferred order.
    Flattens any 'extra' dict keys as 'extra.<key>'.
    """
    all_keys = set()
    for rec in records:
        all_keys.update(rec.keys())
        # Flatten any extra fields as columns: extra.foo -> 'extra.foo'
        if "extra" in rec and isinstance(rec["extra"], dict):
            all_keys.update(f"extra.{k}" for k in rec["extra"].keys())
    preferred = preferred or []
    # Preferred columns first, rest sorted at the end
    columns = [col for col in preferred if col in all_keys]
    extra_cols = sorted(k for k in all_keys if k not in columns)
    return columns + extra_cols

def flatten_row(rec, columns):
    """
    Build a flat row for output, flattening extras and joining lists.
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

def render_json(records, output=None):
    """
    Render records as pretty-printed JSON.
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
    All fields (including extras) are present, full paths/lines are preserved.
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
    Render records as a GitHub-flavored markdown table.
    All fields (including extras) are present, full paths/lines are preserved.
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
