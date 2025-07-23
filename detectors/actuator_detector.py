import re

def detect_actuator_endpoints(origin, text):
    """
    Detect Spring Boot Actuator endpoints via:
      1) @Endpoint(id="x") plus @ReadOperation/@WriteOperation/@DeleteOperation
      2) management.endpoints.web.base-path in application.properties or YAML
      3) management.endpoints.web.exposure.include in properties or YAML
      4) Security config using EndpointRequest.to(XEndpoint.class)
    """
    # 1) Determine base-path
    base = '/actuator'
    if origin.lower().endswith('.properties'):
        m_bp = re.search(
            r"management\.endpoints\.web\.base-path\s*=\s*(\S+)",
            text
        )
        if m_bp:
            base = m_bp.group(1).rstrip('/')
    elif origin.lower().endswith(('.yml', '.yaml')):
        for line in text.splitlines():
            m_bp = re.match(r"\s*base-path\s*:\s*(\S+)", line)
            if m_bp:
                base = m_bp.group(1).rstrip('/')
                break

    # 2) @Endpoint and operation-level HTTP method inference
    for em in re.finditer(r"@Endpoint\s*\(\s*id\s*=\s*['\"](\w+)['\"]", text):
        eid = em.group(1)
        snippet = text[em.end(): em.end()+200]
        methods = []
        if '@ReadOperation' in snippet:
            methods.append('GET')
        if '@WriteOperation' in snippet:
            methods.append('POST')
        if '@DeleteOperation' in snippet:
            methods.append('DELETE')
        method = methods[0] if len(methods)==1 else methods or None
        yield {
            'endpoint': f"{base}/{eid}",
            'method': method,
            'controller': None,
            'file': origin,
            'line': text.count('\n', 0, em.start()) + 1,
            'source': 'detect_actuator_endpoints'
        }

    # 3) Exposure include (properties)
    if origin.lower().endswith('.properties'):
        for match in re.finditer(
            r"management\.endpoints\.web\.exposure\.include\s*=\s*([^\n]+)",
            text
        ):
            for eid in match.group(1).split(','):
                yield {
                    'endpoint': f"{base}/{eid.strip()}",
                    'method': None,
                    'controller': None,
                    'file': origin,
                    'line': text.count('\n', 0, match.start()) + 1,
                    'source': 'detect_actuator_endpoints'
                }

    # 4) Exposure include (YAML)
    if origin.lower().endswith(('.yml', '.yaml')):
        lines = text.splitlines()
        in_exposure = False
        for idx, line in enumerate(lines, start=1):
            if re.match(r"\s*exposure\s*:\s*$", line):
                in_exposure = True
                continue
            if in_exposure:
                m_inc = re.match(r"\s*include\s*:\s*(.+)", line)
                if m_inc:
                    for eid in m_inc.group(1).split(','):
                        yield {
                            'endpoint': f"{base}/{eid.strip()}",
                            'method': None,
                            'controller': None,
                            'file': origin,
                            'line': idx,
                            'source': 'detect_actuator_endpoints'
                        }
                # exit block on de‑indent
                if not line.startswith(' '):
                    in_exposure = False

    # 5) Security config via EndpointRequest.to(...)
    for m in re.finditer(r"EndpointRequest\.to\((\w+)Endpoint\.class\)", text):
        cls = m.group(1)
        path = f"{base}/{cls[0].lower()}{cls[1:]}"
        yield {
            'endpoint': path,
            'method': None,
            'controller': None,
            'file': origin,
            'line': text.count('\n', 0, m.start()) + 1,
            'source': 'detect_actuator_endpoints'
        }
