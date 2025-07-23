import os
import javalang
from crawler.parsing import parse_constants, http_method_from_annotation

def ast_detector(path: str) -> list:
    """
    AST‑based detector: picks up Spring mapping annotations and resolves constant paths.
    """
    recs = []
    try:
        src = open(path, 'r', errors='ignore').read()
        tree = javalang.parse.parse(src)
    except Exception:
        return recs

    class_name = os.path.splitext(os.path.basename(path))[0]
    consts     = parse_constants(path)

    for _, node in tree.filter(javalang.tree.Annotation):
        name = node.name
        if name not in (
            'RequestMapping','GetMapping','PostMapping',
            'PutMapping','DeleteMapping','PatchMapping'
        ):
            continue

        # annotations may have a single element or list
        elems = node.element if isinstance(node.element, list) else [node.element]
        for pair in elems or []:
            if getattr(pair, 'name', None) in ('value', 'path', 'fullPath'):
                val = pair.value
                # literal string
                if isinstance(val, javalang.tree.Literal):
                    path_val = val.value.strip('"').strip("'")
                # constant reference
                elif isinstance(val, javalang.tree.MemberReference):
                    path_val = consts.get(val.member)
                else:
                    continue

                if not path_val:
                    continue

                line = node.position[0] if node.position else 0
                recs.append({
                    'endpoint':   path_val,
                    'method':     http_method_from_annotation(name, pair),
                    'controller': class_name,
                    'line':       line,
                    'source':     'AST',
                    'file':       path
                })
    return recs
