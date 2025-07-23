"""
Module: aggregate
Merges raw detections into consolidated endpoint records,
computes confidence, normalizes, dedupes, and collects extras.
"""
import os
import re
from collections import defaultdict
from .detect import DETECTORS

# Confidence weighting
DETECTOR_WEIGHTS = {det.__name__: 1 for det in DETECTORS}
TOTAL_WEIGHT = sum(DETECTOR_WEIGHTS.values())

# Core record keys
CORE_FIELDS = [
    'endpoint', 'method', 'confidence', 'module', 'controller',
    'params', 'detailed_params', 'reason', 'line', 'locations'
]

def infer_method_params(record):
    # Placeholder for AST-based param extraction
    return []

def calculate_confidence(sources):
    weight_sum = sum(DETECTOR_WEIGHTS.get(src,1) for src in sources)
    return int((weight_sum / TOTAL_WEIGHT) * 100)

def aggregate(records):
    # Group by normalized endpoint
    groups = defaultdict(list)
    for rec in records:
        raw = rec.get('endpoint') or ''
        norm = raw.lower().rstrip('/') or '/'
        groups[norm].append(rec)

    results = []
    for ep, recs in groups.items():
        sources = sorted({r['source'] for r in recs})
        confidence = calculate_confidence(sources)
        methods = sorted({r['method'] for r in recs})
        controllers = sorted({r['controller'] for r in recs})
        module = os.path.basename(os.path.dirname(recs[0]['file']))
        params = sorted({p for r in recs for p in (r.get('params') or [])})
        detailed = sorted({p for r in recs for p in (r.get('detailed_params') or [])})
        reason = ';'.join(sources)
        lines = [r['line'] for r in recs if r.get('line') is not None]
        line = min(lines) if lines else None
        locations = ';'.join(
            f"{os.path.basename(r['file'])}:{r['line']}" 
            for r in recs if r.get('line') is not None
        )

        record = {
            'endpoint': ep,
            'method': methods[0] if len(methods)==1 else methods,
            'confidence': confidence,
            'module': module,
            'controller': controllers[0] if len(controllers)==1 else controllers,
            'params': params,
            'detailed_params': detailed,
            'reason': reason,
            'line': line,
            'locations': locations
        }

        # Dynamic extras
        extra_keys = set().union(*(r.keys() for r in recs)) - set(record.keys())
        for key in sorted(extra_keys):
            vals = sorted({r.get(key) for r in recs if r.get(key) is not None})
            record[key] = vals if len(vals)>1 else (vals[0] if vals else None)

        results.append(record)
    return results

def merge_overlaps(results):
    wild = [r for r in results if '*' in r['endpoint']]
    spec = [r for r in results if '*' not in r['endpoint']]
    out = list(spec)
    for w in wild:
        prefix = w['endpoint'].rstrip('*')
        if not any(s['endpoint'].startswith(prefix) for s in spec):
            out.append(w)
    return out

def filter_and_sort(results, args):
    out = []
    for r in results:
        if args.filter_confidence is not None and r['confidence'] < args.filter_confidence:
            continue
        if args.filter_method != 'ALL':
            methods = r['method'] if isinstance(r['method'],list) else [r['method']]
            if args.filter_method not in methods:
                continue
        out.append(r)
    if args.sort_by:
        out.sort(key=lambda x: x.get(args.sort_by))
    return out