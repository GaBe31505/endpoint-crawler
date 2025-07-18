
#!/usr/bin/env python3
"""
endpoint_crawler.py - Comprehensive endpoint scanner for Java Spring, Express.js, Angular, etc.

Usage:
    python endpoint_crawler.py <path(s)> -f <format> -o <output_file>
    Supports formats: json, csv, markdown, postman, text
"""

import os
import re
import zipfile
import tempfile
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
import argparse

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
    base_path: str = ""
    full_path: str = ""
    parameters: List[str] = field(default_factory=list)

    def __post_init__(self):
        base = self.base_path.rstrip('/')
        path = self.path.lstrip('/')
        self.full_path = f"{base}/{path}" if base else f"/{path}"
        self.full_path = re.sub(r'/+', '/', self.full_path)
        if not self.full_path.startswith('/'):
            self.full_path = '/' + self.full_path

class EndpointCrawler:
    def __init__(self):
        self.endpoints: List[Endpoint] = []
        self.java_files: List[Path] = []
        self.context_path: str = ""

        self.mapping_annotations = {
            'RequestMapping': 'ANY',
            'GetMapping': 'GET',
            'PostMapping': 'POST',
            'PutMapping': 'PUT',
            'DeleteMapping': 'DELETE',
            'PatchMapping': 'PATCH'
        }

        self.annotation_pattern = re.compile(
            r'@(' + '|'.join(self.mapping_annotations.keys()) + r')\s*(\((.*?)\))?',
            re.DOTALL
        )
        self.method_pattern = re.compile(
            r'(public|private|protected)?\s+[\w<>,\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{',
            re.MULTILINE
        )
        self.class_pattern = re.compile(r'class\s+(\w+)')
        self.path_pattern = re.compile(r'(value\s*=\s*|path\s*=\s*)?["\']([^"\']+)["\']')
        self.method_attr_pattern = re.compile(r'method\s*=\s*RequestMethod\.(\w+)')
        self.path_var_pattern = re.compile(r'@PathVariable(?:\([^)]*\))?\s+\w+\s+(\w+)')
        self.req_param_pattern = re.compile(r'@RequestParam(?:\([^)]*\))?\s+\w+\s+(\w+)')
        self.context_path_pattern = re.compile(r'server\.servlet\.context-path\s*=\s*([^\n]+)')

    def get_base_path(self, content: str) -> str:
        match = re.search(r'@RequestMapping\s*\(\s*(.*?)\)', content)
        if match:
            annotation_content = match.group(1)
            path_match = self.path_pattern.search(annotation_content)
            if path_match:
                return path_match.group(2)
        return ""

    def extract_method_parameters(self, method_block: str) -> List[str]:
        params = self.path_var_pattern.findall(method_block)
        params += [f"{p}(param)" for p in self.req_param_pattern.findall(method_block)]
        return params

    def extract_endpoints_from_file(self, file_path: Path):
        content = read_file_safely(file_path)
        if content is None or '@' not in content:
            return

        class_match = self.class_pattern.search(content)
        class_name = class_match.group(1) if class_match else "Unknown"
        base_path = self.get_base_path(content)

        for match in self.annotation_pattern.finditer(content):
            annotation = match.group(1)
            annotation_args = match.group(3) or ""
            http_method = self.mapping_annotations[annotation]

            if annotation == 'RequestMapping':
                method_override = self.method_attr_pattern.search(annotation_args)
                if method_override:
                    http_method = method_override.group(1)

            path_match = self.path_pattern.search(annotation_args)
            path = path_match.group(2) if path_match else ""

            method_name = self.find_next_method_name(content, match.end())
            params = self.extract_method_parameters(content[match.end():match.end() + 300])
            line_number = content[:match.start()].count('\n') + 1
            self.endpoints.append(Endpoint(
                path=path,
                method=http_method,
                controller_class=class_name,
                method_name=method_name or "Unknown",
                file_path=str(file_path),
                line_number=line_number,
                base_path=base_path,
                parameters=params
            ))

    def find_next_method_name(self, content: str, start_pos: int) -> Optional[str]:
        snippet = content[start_pos:start_pos + 1000]
        match = self.method_pattern.search(snippet)
        return match.group(2) if match else None

    def extract_context_path(self, files: List[Path]):
        for f in files:
            if f.suffix == '.properties':
                content = read_file_safely(f)
                if not content:
                    continue
                match = self.context_path_pattern.search(content)
                if match:
                    self.context_path = match.group(1).strip()
                    break

    def scan_directory(self, base_path: Path):
        config_files = []
        for root, _, files in os.walk(base_path):
            for name in files:
                f = Path(root) / name
                if f.suffix == '.java':
                    self.java_files.append(f)
                elif f.suffix in ['.properties', '.yaml', '.yml']:
                    config_files.append(f)

        self.extract_context_path(config_files)

        for file in self.java_files:
            self.extract_endpoints_from_file(file)

        for ep in self.endpoints:
            if self.context_path:
                ep.full_path = f"{self.context_path.rstrip('/')}{ep.full_path}"

    def scan_zip_or_war(self, archive_path: Path):
        with zipfile.ZipFile(archive_path, 'r') as z:
            with tempfile.TemporaryDirectory() as tmpdir:
                z.extractall(tmpdir)
                self.scan_directory(Path(tmpdir))

    def crawl(self, paths: List[str]):
        for path in paths:
            p = Path(path)
            if p.suffix in ['.zip', '.war']:
                self.scan_zip_or_war(p)
            elif p.is_dir():
                self.scan_directory(p)

    def export(self, export_format: str = 'json', output_path: Optional[str] = None):
        return export_endpoints(self.endpoints, export_format=export_format, output_path=output_path)

def main():
    parser = argparse.ArgumentParser(description="Comprehensive endpoint crawler")
    parser.add_argument("paths", nargs="+", help="Folders or archives to crawl")
    parser.add_argument("-f", "--format", choices=["json", "csv", "markdown", "postman", "text"], default="json")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    args = parser.parse_args()

    crawler = EndpointCrawler()
    crawler.crawl(args.paths)
    result = crawler.export(export_format=args.format, output_path=args.output)
    if not args.output:
        print(result)

if __name__ == "__main__":
    main()
