import javalang
from crawler.io import read_file


def parse_constants(path: str) -> dict:
    """
    Extract static final String constants.
    """
    consts = {}
    src = read_file(path)
    try:
        tree = javalang.parse.parse(src)
        for _, node in tree.filter(javalang.tree.FieldDeclaration):
            if {'static','final'}.issubset(node.modifiers) and getattr(node.type,'name',None)=='String':
                for decl in node.declarators:
                    if decl.initializer and isinstance(decl.initializer, javalang.tree.Literal):
                        consts[decl.name] = decl.initializer.value.strip('"')
    except Exception:
        pass
    return consts


def http_method_from_annotation(name: str, elem) -> str:
    """
    Map Spring annotations to HTTP verbs.
    """
    mapping = {'GetMapping':'GET','PostMapping':'POST','PutMapping':'PUT','DeleteMapping':'DELETE','PatchMapping':'PATCH'}
    if name in mapping:
        return mapping[name]
    if name=='RequestMapping' and elem:
        txt = getattr(elem,'string',str(elem))
        for verb in mapping.values():
            if verb in txt:
                return verb
    return 'ALL'