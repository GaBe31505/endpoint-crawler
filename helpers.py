import re
from pathlib import Path
import javalang

def read_file(path: str) -> str:
    """
    Read a file from disk with multi‑encoding fallback.
    """
    raw = Path(path).read_bytes()
    for enc in ("utf-8", "utf-16", "latin-1", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")

def read_bytes(raw: bytes) -> str:
    """
    Decode raw bytes (from a ZIP/WAR entry) with the same fallback logic.
    """
    for enc in ("utf-8", "utf-16", "latin-1", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")

def http_method_from_annotation(name, elem):
    mapping = {
        'GetMapping': 'GET', 'PostMapping': 'POST',
        'PutMapping': 'PUT', 'DeleteMapping': 'DELETE',
        'PatchMapping': 'PATCH',
    }
    if name in mapping:
        return mapping[name]
    if name == 'RequestMapping' and elem:
        txt = getattr(elem, 'string', str(elem))
        for verb in mapping.values():
            if verb in txt:
                return verb
    return 'ALL'

def parse_constants(path: str) -> dict:
    """
    Extract static final String constants from a Java file.
    """
    consts = {}
    src = read_file(path)
    try:
        tree = javalang.parse.parse(src)
        for _, node in tree.filter(javalang.tree.FieldDeclaration):
            if {'static','final'}.issubset(node.modifiers) and getattr(node.type, 'name', None) == 'String':
                for d in node.declarators:
                    init = d.initializer
                    if isinstance(init, javalang.tree.Literal):
                        consts[d.name] = init.value.strip('"').strip("'")
    except:
        pass
    return consts

def regex_detector(path: str, pattern: str, source_tag: str, method: str = 'ALL') -> list:
    """
    Generic regex-based detector: finds all matches of `pattern` in the file content.
    """
    recs = []
    txt = read_file(path)
    for m in re.finditer(pattern, txt):
        ep = m.group(1)
        line = txt[:m.start()].count('\n') + 1
        controller = Path(path).stem
        recs.append({
            'endpoint': ep,
            'line': line,
            'method': method,
            'controller': controller,
            'source': source_tag,
            'file': path
        })
    return recs
