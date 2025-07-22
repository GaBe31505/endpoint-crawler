import os, javalang
from helpers import parse_constants, http_method_from_annotation

def ast_detector(path: str) -> list:
    recs = []
    src = open(path, 'r', errors='ignore').read()
    try:
        tree = javalang.parse.parse(src)
    except:
        return recs
    class_name = os.path.splitext(os.path.basename(path))[0]
    consts = parse_constants(path)
    for _, node in tree.filter(javalang.tree.Annotation):
        name = node.name
        line = node.position[0] if node.position else 0
        if name in ('RequestMapping','GetMapping','PostMapping','PutMapping','DeleteMapping','PatchMapping'):
            elems = node.element if isinstance(node.element,list) else [node.element]
            for pair in elems or []:
                if getattr(pair,'name',None) in ('value','path','fullPath'):
                    val = pair.value
                    path_val = None
                    if isinstance(val, javalang.tree.Literal):
                        path_val = val.value.strip('"').strip("'")
                    elif isinstance(val, javalang.tree.MemberReference):
                        path_val = consts.get(val.member)
                    if path_val:
                        recs.append({
                            'endpoint': path_val,
                            'line': line,
                            'method': http_method_from_annotation(name,pair),
                            'controller': class_name,
                            'source': 'AST',
                            'file': path
                        })
    return recs
