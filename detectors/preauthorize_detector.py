import re

def detect_preauthorize(origin, text):
    """
    Yields a record for each @PreAuthorize(...) that guards a Spring Web mapping.
    Supports:
      • Class‑level @RequestMapping prefixes
      • Arrays of paths (e.g. {"/a","/b"})
      • Both value= and path= attributes
      • A wider scan window (skips comments / Javadoc)
    """
    # 1) Grab any class-level @RequestMapping prefix
    class_prefix = ''
    for line in text.splitlines():
        if line.strip().startswith('//'):
            continue
        m = re.match(r'\s*@RequestMapping\s*\(([^)]*)\)', line)
        if m:
            args = m.group(1)
            pm = re.search(r'(?:path|value)\s*=\s*\{?\s*["\']([^}\']+)["\']', args)
            if pm:
                class_prefix = pm.group(1).rstrip('/')
            break

    # 2) Optionally capture controller class name
    controller = None
    mcls = re.search(r'public\s+class\s+(\w+)', text)
    if mcls:
        controller = mcls.group(1)

    lines = text.splitlines()
    in_block = False
    for idx, line in enumerate(lines):
        # handle /* … */ block comments
        if '/*' in line:
            in_block = True
        if '*/' in line:
            in_block = False
            continue
        if in_block or line.strip().startswith('//'):
            continue

        # find method‑level @PreAuthorize
        if '@PreAuthorize' in line:
            # look ahead up to 15 non-comment lines for a mapping
            looked = 0
            j = idx + 1
            while j < len(lines) and looked < 15:
                w = lines[j]; j += 1
                if not w.strip() or w.strip().startswith('//'):
                    continue
                looked += 1

                # match any mapping annotation
                m2 = re.match(
                    r'\s*@(?P<map>(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping))'
                    r'\s*\((?P<args>[^)]*)\)', w
                )
                if not m2:
                    continue

                mapping = m2.group('map')
                args    = m2.group('args')

                # extract one or more paths
                paths = re.findall(r'["\']([^,"\']+)["\']', args) or ['']
                # determine HTTP verbs
                if mapping.endswith('Mapping') and mapping != 'RequestMapping':
                    methods = [mapping.replace('Mapping','').upper()]
                else:
                    methods = re.findall(r'RequestMethod\.(GET|POST|PUT|DELETE|PATCH)', args) or [None]

                # emit one record per path
                for p in paths:
                    ep = ('/'+p.lstrip('/')).rstrip('/')
                    full_ep = (class_prefix + ep) or '/'
                    yield {
                        'endpoint': full_ep,
                        'method': methods[0] if len(methods)==1 else methods,
                        'controller': controller,
                        'file': origin,
                        'line': idx+1,
                        'source': 'detect_preauthorize'
                    }
                break
