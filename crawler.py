#!/usr/bin/env python3
"""
Modular endpoint crawler supporting multiple inputs (dirs, files, ZIPs/WARs),
batched I/O, pathlib usage, dynamic detector registration, and helper utilities.
Supports output formats: csv, json, markdown, postman

This version combines AST parsing with comprehensive regex detectors for
maximum coverage, including legacy Struts/XML and hard-coded redirects.
If `-o/--output` is omitted, only CLI output is shown.

Usage:
  python crawler.py \
    -i /path/to/dir file.java archive.zip myapp.war \
    [-o endpoints.csv] \
    [-f csv]

Dependencies:
  pip install javalang rich
"""
from pathlib import Path
import re, argparse, json, zipfile
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.theme import Theme
from rich import box

from helpers import read_file, read_bytes

# Detector imports
from detectors.ast_detector import ast_detector
from detectors.jaxrs_detector import jaxrs_detector
from detectors.programmatic_detector import programmatic_detector
from detectors.webflux_detector import webflux_detector
from detectors.static_detector import static_detector
from detectors.security_detector import security_detector
from detectors.error_detector import error_detector
from detectors.xml_detector import xml_detector
from detectors.jsp_detector import jsp_detector
from detectors.legacy_regex_detector import legacy_regex_detector

# Register detectors dynamically with tags
DETECTORS = [
    ('AST',          ast_detector),
    ('JAXRS',        jaxrs_detector),
    ('PROGRAMMATIC', programmatic_detector),
    ('WEBFLUX',      webflux_detector),
    ('STATIC',       static_detector),
    ('SECURITY',     security_detector),
    ('ERROR',        error_detector),
    ('XML',          xml_detector),
    ('JSP',          jsp_detector),
    ('REGEX_LEGACY', legacy_regex_detector),
]


def parse_args():
    p = argparse.ArgumentParser('Modular Endpoint Crawler')
    p.add_argument('-i', '--inputs', nargs='+', required=True,
                   help='Dirs, files, ZIP/WAR archives')
    p.add_argument('-o', '--output', required=False,
                   help='Output path (omit for CLI-only)')
    p.add_argument('-f', '--format', choices=['csv','json','markdown','postman'], default='csv',
                   help='Output format (only used if --output is provided)')
    return p.parse_args()


def walk_inputs(inputs):
    """Yield (origin, text) pairs for files, directories, and archives."""
    for inp in inputs:
        p = Path(inp)
        if p.is_dir():
            for f in p.rglob('*'):
                if f.is_file():
                    yield str(f), read_file(str(f))
        elif p.suffix.lower() in ('.zip', '.war'):
            with zipfile.ZipFile(p) as zf:
                for name in zf.namelist():
                    if name.endswith('/'):
                        continue
                    raw = zf.read(name)
                    yield f"{inp}:{name}", read_bytes(raw)
        elif p.is_file():
            yield str(p), read_file(str(p))


def run_detectors(origin, text):
    """Run all detectors on the given origin/text and return list of records."""
    records = []
    for tag, func in DETECTORS:
        try:
            recs = func(origin, text) if func.__code__.co_argcount == 2 else func(origin)
        except Exception:
            recs = []
        for r in recs:
            r['source'] = tag
            r['file'] = origin
            records.append(r)
    return records


def aggregate(records):
    """Deduplicate and score by endpoint."""
    grouped = defaultdict(list)
    for r in records:
        grouped[r['endpoint']].append(r)

    results = []
    for ep, recs in grouped.items():
        sources = {r['source'] for r in recs}
        confidence = 100 if len(sources) >= 2 else int((len(sources)/2)*100)
        reason = "; ".join(sorted(sources))
        params = ",".join(re.findall(r"\{([^}]+)\}", ep))
        first = recs[0]
        module = Path(first['file'].split(':')[0]).name
        locations = "; ".join(f"{r['file']}:{r['line']}" for r in recs)
        results.append({
            'module':    module,
            'method':    first['method'],
            'endpoint':  ep,
            'controller':first['controller'],
            'line':      first['line'],
            'confidence':confidence,
            'reason':    reason,
            'params':    params,
            'locations': locations
        })
    return results


def render_cli(results):
    console = Console(theme=Theme({
        'high': 'bold green', 'medium': 'bold yellow', 'low': 'bold red', 'header': 'bold cyan'
    }))
    table = Table(title='Detected Endpoints', box=box.ROUNDED, header_style='header')
    # truncate long module names
    table.add_column('Module', style='cyan', overflow='fold', max_width=20)
    for col, style in [
        ('Method','magenta'),('Endpoint','white'),('Confidence',None),
        ('Sources','white'),('Controller','green'),('Line',None)
    ]:
        table.add_column(col, style=style, justify='right' if col in ('Confidence','Line') else None)
    for r in results:
        lvl = 'high' if r['confidence'] == 100 else 'medium' if r['confidence'] >= 50 else 'low'
        table.add_row(
            r['module'], r['method'], r['endpoint'],
            f"[{lvl}]{r['confidence']}%[/{lvl}]", r['reason'],
            r['controller'], str(r['line'])
        )
    console.print(table)


def render_file(results, path, fmt):
    if not path:
        return
    if fmt == 'csv':
        import csv
        with open(path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'module','method','endpoint','controller','line',
                'confidence','reason','params','locations'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)
    elif fmt == 'json':
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
    elif fmt == 'markdown':
        with open(path, 'w', encoding='utf-8') as f:
            f.write('| endpoint | confidence | reason | params | locations |')
            f.write('|---|---|---|---|---|')
            for r in results:
                f.write(f"| {r['endpoint']} | {r['confidence']}% | {r['reason']} | {r['params']} | {r['locations']} |")
    else:  # postman
        collection = {
            'info': {'name':'Endpoints','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
            'item': []
        }
        for r in results:
            collection['item'].append({
                'name': r['endpoint'],
                'request': {
                    'method': r['method'], 'header': [],
                    'url': {'raw': '{{baseUrl}}'+r['endpoint'],'host':['{{baseUrl}}'],'path':r['endpoint'].lstrip('/').split('/')}
                },
                'response': [],
                'description': r['locations']
            })
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2)


def main():
    args = parse_args()
    all_records = []
    jsp_flag = False

    for origin, text in walk_inputs(args.inputs):
        recs = run_detectors(origin, text)
        for r in recs:
            all_records.append(r)
            if r['source'] == 'XML' and r['endpoint'].lower().endswith('.jsp'):
                jsp_flag = True

    if jsp_flag:
        for inp in args.inputs:
            all_records += jsp_detector(inp)

    results = aggregate(all_records)
    render_cli(results)
    if args.output:
        render_file(results, args.output, args.format)

if __name__ == '__main__':
    main()
