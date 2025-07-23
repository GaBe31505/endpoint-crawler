"""
Module: detect
Loads all detectors (custom or built‑in) and runs them, deduping identical reports.
"""

import pkgutil
import importlib
import inspect

# ——— Path to detectors package (sibling folder to crawler/) ———
# This lets us iterate over every .py in detectors/ without touching __init__.py
from detectors import __path__ as detectors_path

# ------------------------------------------------------------------------------
# 1. Dynamically discover all functions named detect_* in detectors/
# ------------------------------------------------------------------------------

DETECTORS = []

for finder, module_name, is_pkg in pkgutil.iter_modules(detectors_path):
    # Import each detectors.<module_name>
    module = importlib.import_module(f"detectors.{module_name}")
    # Inspect its module‑level functions
    for fn_name, fn in inspect.getmembers(module, inspect.isfunction):
        if fn_name.startswith("detect_"):
            DETECTORS.append(fn)

# Sort by function name for a stable, alphabetical order
DETECTORS.sort(key=lambda fn: fn.__name__)


# ------------------------------------------------------------------------------
# 2. Core orchestration: apply every detector, dedupe identical findings
# ------------------------------------------------------------------------------

def run_detectors(input_pairs):
    """
    Apply each detector to the given inputs and collect unique records.

    Args:
        input_pairs (Iterable[(origin, text)]):
            Tuples of (source identifier, file contents), e.g.
            ("src/com/foo/Bar.java", "public class Bar { ... }").

    Returns:
        List[dict]: Deduplicated list of all detector records.
    """
    seen = set()
    records = []

    for origin, text in input_pairs:
        for det in DETECTORS:
            try:
                for rec in det(origin, text):
                    # Build a signature to avoid exact duplicates:
                    sig = (
                        det.__name__,           # which detector
                        origin,                 # file or archive path
                        rec.get("endpoint"),    # the discovered path
                        rec.get("method"),      # HTTP verb
                        rec.get("controller"),  # handler class
                        rec.get("line"),        # source line number
                    )
                    if sig in seen:
                        continue
                    seen.add(sig)
                    records.append(rec)
            except Exception:
                # If one detector blows up on a file, skip it and keep going
                continue

    return records