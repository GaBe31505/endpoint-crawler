#!/usr/bin/env python3
import os
import argparse
from .io import walk_inputs
from .detect import run_detectors
from .aggregate import aggregate, filter_and_sort, merge_overlaps
from .render import render_cli, render_json, render_csv, render_markdown, render_postman

def parse_args():
    parser = argparse.ArgumentParser(
        description='Discover endpoints in Java/Spring code'
    )
    parser.add_argument('-i', '--inputs', nargs='+', required=True,
                        help='Input directories, files, or archives')
    parser.add_argument('-o', '--output',
                        help='Output file path (omit for CLI output)')
    parser.add_argument('-f', '--format',
                        choices=['csv', 'json', 'markdown', 'postman'],
                        default='csv', help='Output format')
    parser.add_argument('--sort-by',
                        choices=['confidence', 'module', 'method', 'endpoint', 'controller'],
                        help='Sort results by field')
    parser.add_argument('--filter-confidence', type=int, metavar='PERCENT',
                        help='Only include endpoints with confidence ≥ PERCENT')
    parser.add_argument('--filter-method',
                        choices=['GET','POST','PUT','DELETE','PATCH','ALL'],
                        default='ALL', help='Filter by HTTP method')
    return parser.parse_args()

RENDERERS = {
    "json": render_json,
    "csv": render_csv,
    "markdown": render_markdown,
    "postman": render_postman
}

def main():
    args = parse_args()
    if args.output:
        root, ext = os.path.splitext(args.output)
        if not ext:
            args.format = 'json'
            args.output = root + '.json'

    inputs = list(walk_inputs(args.inputs))
    raw = run_detectors(inputs)
    aggregated = aggregate(raw)
    filtered = filter_and_sort(aggregated, args)
    final = merge_overlaps(filtered)

    if args.output:
        render_fn = RENDERERS.get(args.format, render_json)
        render_fn(final, args.output)
    else:
        render_cli(final)

if __name__ == '__main__':
    main()
