import os
import zipfile
from pathlib import Path


def walk_inputs(inputs):
    """
    Yield (origin, text) pairs for directories, ZIP/WARs, or files.
    """
    for inp in inputs:
        if os.path.isdir(inp):
            for root, _, files in os.walk(inp):
                for f in files:
                    path = os.path.join(root, f)
                    try:
                        yield path, open(path, errors='ignore').read()
                    except Exception:
                        pass
        elif zipfile.is_zipfile(inp):
            from crawler.zip_utils import extract_java_from_zip
            yield from extract_java_from_zip(inp)
        else:
            try:
                yield inp, open(inp, errors='ignore').read()
            except Exception:
                pass


def read_file(path: str) -> str:
    """
    Read a file with encoding fallbacks.
    """
    raw = Path(path).read_bytes()
    for enc in ("utf-8","utf-16","latin-1","cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8",errors="ignore")


def read_bytes(raw: bytes) -> str:
    """
    Decode raw bytes into text with fallbacks.
    """
    for enc in ("utf-8","utf-16","latin-1","cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8",errors="ignore")