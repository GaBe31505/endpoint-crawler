
import json
from typing import List, Optional
from dataclasses import asdict

def export_endpoints(endpoints: List, export_format: str = 'json', output_path: Optional[str] = None) -> str:
    if not endpoints:
        return "No endpoints found."

    if export_format == 'json':
        data = json.dumps([asdict(e) for e in endpoints], indent=2)
    elif export_format == 'csv':
        keys = list(asdict(endpoints[0]).keys())
        lines = [",".join(keys)]
        for e in endpoints:
            lines.append(",".join(str(getattr(e, k, '')) for k in keys))
        data = "\n".join(lines)
    elif export_format == 'markdown':
        headers = "| " + " | ".join(asdict(endpoints[0]).keys()) + " |"
        sep = "| " + " | ".join(["---"] * len(asdict(endpoints[0]))) + " |"
        rows = ["| " + " | ".join(str(v) for v in asdict(e).values()) + " |" for e in endpoints]
        data = "\n".join([headers, sep] + rows)
    elif export_format == 'postman':
        items = [{
            "name": f"{e.method} {e.full_path}",
            "request": {
                "method": e.method,
                "header": [],
                "url": {
                    "raw": "{{baseUrl}}" + e.full_path,
                    "host": ["{{baseUrl}}"],
                    "path": e.full_path.strip("/").split("/")
                }
            }
        } for e in endpoints]
        data = json.dumps({
            "info": {
                "name": "Discovered Endpoints",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": items
        }, indent=2)
    else:
        data = "\n".join([f"{e.method} {e.full_path} -> {e.controller_class}.{e.method_name}" for e in endpoints])

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(data)

    return data
