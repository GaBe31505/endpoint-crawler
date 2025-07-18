#!/usr/bin/env python3
"""
Enhanced Multi-Framework Endpoint Crawler with Base Path Merging and Constant Resolution
"""
import os
import re
import argparse
import zipfile
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict
from collections import defaultdict

from helpers.file_utils import read_file_safely
from helpers.export_utils import export_endpoints

@dataclass
class Endpoint:
    path: str
    method: str
    controller_class: str
    method_name: str
    file_path: str
    line_number: int
    base_path: str
    full_path: str
    parameters: str
    source_type: str
    severity: str = field(default="low")
    module: str = field(default="")

# -----------------------------
# Regexes
# -----------------------------
JAVA_CONSTANT = re.compile(r'public\s+static\s+final\s+String\s+(\w+)\s*=\s*"([^"]+)"')
SPRING_CLASS_BASE = re.compile(r'@RequestMapping\(([^)]*)\)')
SPRING_METHOD_MAP = re.compile(r'@(RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\(([^)]*)\)')
SPRING_CONTROLLER = re.compile(r'@(RestController|Controller)')
STRUTS_XML_ACTION = re.compile(r'<action[^>]+(?:path|name)="([^"]+)"')
STRUTS_ANNOTATION = re.compile(r'@Action\(([^)]*)\)')
JAXRS_PATH = re.compile(r'@Path\("([^"]+)"\)')
SERVLET_MAPPING = re.compile(r'@WebServlet\("([^"]+)"\)')
JSP_HREF = re.compile(r'(?:href|action)="([^"]+\\.jsp)"')
JSP_INCLUDE = re.compile(r'<jsp:include\\s+page="([^"]+)"')
FREEMARKER_URL = re.compile(r'(?:href|action)="([^"]+\\.ftl)"')
WEB_XML_MAPPING = re.compile(r'<url-pattern>([^<]+)</url-pattern>')

# -----------------------------
# Utilities
# -----------------------------
def determine_severity(method: str, annotations: List[str]) -> str:
    method = method.upper()
    if method in {"DELETE", "PATCH"}:
        return "high"
    if any(a in annotations for a in ["@PermitAll", "@AllowAnonymous"]):
        return "high"
    if method == "POST":
        return "medium"
    return "low"

def infer_module_from_path(path: str) -> str:
    parts = Path(path).parts
    for i, part in enumerate(parts):
        if part in {"src", "modules", "apps"} and i + 1 < len(parts):
            return parts[i + 1]
    return parts[0] if parts else "root"

def parse_mapping_args(arg_string: str) -> str:
    match = re.search(r'(value|path)?\s*=\s*"([^"]+)"', arg_string)
    if match:
        return match.group(2)
    if arg_string.strip().startswith('"'):
        return arg_string.strip().strip('"')
    return arg_string

# -----------------------------
# Scanning
# -----------------------------
def extract_endpoints_from_file(filepath: str, content: str, constants: Dict[str, str]) -> List[Endpoint]:
    endpoints = []
    lines = content.splitlines()
    base_path = ""
    class_name = os.path.basename(filepath).replace(".java", "")

    for i, line in enumerate(lines):
        if SPRING_CLASS_BASE.search(line):
            base_path = parse_mapping_args(SPRING_CLASS_BASE.search(line).group(1))

        for match in SPRING_METHOD_MAP.finditer(line):
            method_type = match.group(1).replace("Mapping", "").upper()
            sub_path = parse_mapping_args(match.group(2))
            full = os.path.join(base_path, sub_path).replace("\\", "/")
            endpoints.append(Endpoint(
                path=sub_path,
                method=method_type,
                controller_class=class_name,
                method_name="unknown",
                file_path=filepath,
                line_number=i + 1,
                base_path=base_path,
                full_path=full,
                parameters="",
                source_type="SPRING_ANNOTATION"
            ))

    for pattern, tag, regex in [
        (STRUTS_XML_ACTION, "STRUTS_XML", STRUTS_XML_ACTION),
        (STRUTS_ANNOTATION, "STRUTS_ANNOT", STRUTS_ANNOTATION),
        (JAXRS_PATH, "JAXRS", JAXRS_PATH),
        (SERVLET_MAPPING, "SERVLET", SERVLET_MAPPING),
        (WEB_XML_MAPPING, "WEB_XML", WEB_XML_MAPPING),
        (JSP_HREF, "JSP", JSP_HREF),
        (JSP_INCLUDE, "JSP_INCLUDE", JSP_INCLUDE),
        (FREEMARKER_URL, "FREEMARKER", FREEMARKER_URL),
    ]:
        for m in regex.finditer(content):
            endpoints.append(Endpoint(
                path=m.group(1),
                method="GET",
                controller_class="",
                method_name="",
                file_path=filepath,
                line_number=content[:m.start()].count('\n') + 1,
                base_path="",
                full_path=m.group(1),
                parameters="",
                source_type=tag
            ))

    return endpoints

def scan_path(path: str) -> List[Endpoint]:
    extracted = []
    constants = {}
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, 'r') as zip_ref:
            with tempfile.TemporaryDirectory() as tmp_dir:
                zip_ref.extractall(tmp_dir)
                for root, _, files in os.walk(tmp_dir):
                    for f in files:
                        file_path = os.path.join(root, f)
                        content = read_file_safely(file_path)
                        if content and file_path.endswith((".java", ".xml", ".jsp", ".html", ".ftl")):
                            extracted.extend(extract_endpoints_from_file(file_path, content, constants))
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in files:
                file_path = os.path.join(root, f)
                content = read_file_safely(file_path)
                if content and file_path.endswith((".java", ".xml", ".jsp", ".html", ".ftl")):
                    extracted.extend(extract_endpoints_from_file(file_path, content, constants))
    return extracted

# -----------------------------
# Deduplication
# -----------------------------
def deduplicate_endpoints(endpoints: List[Endpoint]) -> List[Endpoint]:
    grouped = defaultdict(list)
    for ep in endpoints:
        key = (ep.method, ep.full_path)
        grouped[key].append(ep)

    deduped = []
    for (method, path), group in grouped.items():
        primary = group[0]
        primary.file_path = ", ".join(sorted(set(e.file_path for e in group)))
        primary.line_number = min(e.line_number for e in group)
        primary.source_type = ", ".join(sorted(set(e.source_type for e in group)))
        primary.severity = max(group, key=lambda e: ["low", "medium", "high"].index(e.severity)).severity
        deduped.append(primary)

    return deduped

# -----------------------------
# CLI Entry
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Enhanced endpoint crawler")
    parser.add_argument("paths", nargs="+", help="Files or folders to scan")
    parser.add_argument("-f", "--format", choices=["json", "csv", "markdown", "text", "postman"], default="json")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("--raw", action="store_true", help="Show raw (non-deduplicated) endpoint output")
    args = parser.parse_args()

    all_results: List[Endpoint] = []
    for path in args.paths:
        all_results.extend(scan_path(path))

    for ep in all_results:
        ep.module = infer_module_from_path(ep.file_path)
        ep.severity = determine_severity(ep.method, [ep.source_type])

    if not args.raw:
        all_results = deduplicate_endpoints(all_results)

    all_results.sort(key=lambda e: (e.module, e.controller_class, e.full_path))

    if not args.output:
        print("\n\033[1m[INFO] Detected Endpoints:\033[0m\n")
        for ep in all_results:
            color = {
                "high": "\033[91m",     # red
                "medium": "\033[93m",   # yellow
                "low": "\033[92m",      # green
            }.get(ep.severity.lower(), "\033[0m")
            reset = "\033[0m"
            print(f"- {ep.method:<6} {ep.full_path:<45}"
                  f"\n  ↳ Controller: {ep.controller_class:<20} Line: {ep.line_number:<4} Source: {ep.source_type:<25} Severity: {color}{ep.severity.upper()}{reset}")

    export_endpoints(all_results, args.format, args.output)

if __name__ == "__main__":
    main()

