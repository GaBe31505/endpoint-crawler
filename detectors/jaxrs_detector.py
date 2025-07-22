import os, javalang
from helpers import parse_constants

def jaxrs_detector(path: str) -> list:
    recs = []
    try:
        tree = javalang.parse.parse(open(path,'r',errors='ignore').read())
    except:
        return recs
    class_name = os.path.splitext(os.path.basename(path))[0]
    for _, node in tree.filter(javalang.tree.Annotation):
        if node.name=='Path' and node.element:
            line = node.position[0] if node.position else 0
            val = node.element
            path_val = None
            if isinstance(val, javalang.tree.Literal):
                path_val = val.value.strip('"').strip("'")
            elif isinstance(val, javalang.tree.MemberReference):
                consts = parse_constants(path)
                path_val = consts.get(val.member)
            if path_val:
                recs.append({
                    'endpoint': path_val,
                    'line': line,
                    'method': 'ALL',
                    'controller': class_name,
                    'source': 'JAXRS',
                    'file': path
                })
    return recs
