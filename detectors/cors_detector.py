import re

def detect_cors(origin, text):
    """
    Detect endpoints with @CrossOrigin annotation (CORS).
    Supports class-level and method-level @CrossOrigin, captures CORS attributes.
    """
    lines = text.splitlines()
    # 1) Class-level prefix and CORS attrs
    class_prefix = ''
    class_cors = ''
    in_block = False
    for line in lines:
        if '/*' in line:
            in_block = True
        if '*/' in line:
            in_block = False
            continue
        if in_block or line.strip().startswith('//'):
            continue
        # class-level mapping
        m_map = re.match(r"\s*@RequestMapping\s*\(([^)]*)\)", line)
        if m_map:
            args = m_map.group(1)
            pm = re.search(r"(?:path|value)\s*=\s*\{?\s*['\"]([^}\"]+)['\"]", args)
            if pm:
                class_prefix = pm.group(1).rstrip('/')
            continue
        # class-level CORS
        m_cors = re.match(r"\s*@CrossOrigin\s*(?:\(([^)]*)\))?", line)
        if m_cors:
            class_cors = m_cors.group(1) or ''
            continue
        if re.match(r"\s*public\s+class", line):
            break
    # controller name
    controller = None
    m_cls = re.search(r"public\s+class\s+(\w+)", text)
    if m_cls:
        controller = m_cls.group(1)
    # parse attributes helper
    def parse_attrs(s): 
        return dict(re.findall(r"(\w+)\s*=\s*['\"]([^'\"]+)['\"]", s or ''))
    # 2) method-level
    in_block = False
    for idx, line in enumerate(lines):
        if '/*' in line:
            in_block = True
        if '*/' in line:
            in_block = False
            continue
        if in_block or line.strip().startswith('//'):
            continue
        m2 = re.match(
            r"\s*@(?P<map>(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping))"
            r"\s*\((?P<args>[^)]*)\)", line
        )
        if not m2:
            continue
        mapping, args = m2.group('map'), m2.group('args')
        # paths
        paths = re.findall(r"['\"]([^,'\"]+)['\"]", args) or ['']
        # methods
        if mapping!='RequestMapping':
            methods=[mapping.replace('Mapping','').upper()]
        else:
            methods=re.findall(r"RequestMethod\.(GET|POST|PUT|DELETE|PATCH)", args) or [None]
        # find method-level CORS
        cors_attr=class_cors
        for j in range(idx+1, min(len(lines), idx+6)):
            if '@CrossOrigin' in lines[j]:
                mc=re.match(r"\s*@CrossOrigin\s*\(([^)]*)\)", lines[j])
                cors_attr = mc.group(1) if mc else class_cors
                break
        cors_info = parse_attrs(cors_attr)
        # emit
        for p in paths:
            ep=('/'+p.lstrip('/')).rstrip('/')
            full=(class_prefix+ep) or '/'
            for m in methods:
                yield {
                    'endpoint': full,
                    'method': m,
                    'controller': controller,
                    'file': origin,
                    'line': idx+1,
                    'source': 'detect_cors',
                    'cors_origins': cors_info.get('origins'),
                    'cors_methods': cors_info.get('methods'),
                    'cors_maxAge': cors_info.get('maxAge')
                }
