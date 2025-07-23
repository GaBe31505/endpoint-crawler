# crawler/render.py

"""
Rendering logic for endpoint discovery.
Provides functions to output records in various formats:
- CLI table (handles missing or non-iterable methods)
- JSON
- CSV
- Markdown
- Postman collection
"""

from tabulate import tabulate
import json
import csv
import sys

def render_cli(records):
    """
    Render records as a CLI table.
    Handles 'method' being None, a string, or a list/tuple.
    """
    if not records:
        print("No endpoints found.")
        return

    headers = ["Endpoint", "Method", "Controller", "File", "Line"]
    rows = []
    for r in records:
        method_val = r.get("method") or ""
        if isinstance(method_val, (list, tuple)):
            method_str = ",".join(method_val)
        else:
            method_str = str(method_val)

        rows.append([
            r.get("endpoint", ""),
            method_str,
            r.get("controller", ""),
            r.get("file", ""),
            r.get("line", "")
        ])
    print(tabulate(rows, headers=headers, tablefmt="github"))

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
    Render records as CSV.
    """
    if not records:
        print("No endpoints found.")
        return

    fieldnames = sorted({key for rec in records for key in rec.keys()})
    if output:
        f = open(output, "w", newline="", encoding="utf-8")
    else:
        f = sys.stdout

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for rec in records:
        writer.writerow(rec)

    if output:
        f.close()

def render_markdown(records, output=None):
    """
    Render records as a GitHub‑flavored markdown table.
    """
    if not records:
        print("No endpoints found.")
        return

    headers = ["Endpoint", "Method", "Controller", "File", "Line"]
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")

    for r in records:
        method_val = r.get("method") or ""
        if isinstance(method_val, (list, tuple)):
            method_str = ",".join(method_val)
        else:
            method_str = str(method_val)

        row = [
            str(r.get("endpoint", "")),
            method_str,
            str(r.get("controller", "")),
            str(r.get("file", "")),
            str(r.get("line", ""))
        ]
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
