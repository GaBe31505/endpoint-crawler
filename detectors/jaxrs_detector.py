import os
import javalang
from crawler.parsing import parse_constants, http_method_from_annotation

def jaxrs_detector(path: str) -> list:
    """
    JAX‑RS @Path annotations on classes or methods.
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
        if node.name != 'Path':
            continue
        elems = node.element if isinstance(node.element, list) else [node.element]
        for elem in elems or []:
            if getattr(elem, 'name', None) == 'value':
                raw = elem.value
                if isinstance(raw, javalang.tree.Literal):
                    path_val = raw.value.strip('"')
                elif isinstance(raw, javalang.tree.MemberReference):
                    path_val = consts.get(raw.member)
                else:
                    continue

                if not path_val:
                    continue

                line = node.position[0] if node.position else 0
                recs.append({
                    'endpoint':   path_val,
                    'method':     http_method_from_annotation(node.name, elem),
                    'controller': class_name,
                    'line':       line,
                    'source':     'JAXRS',
                    'file':       path
                })
    return recs
