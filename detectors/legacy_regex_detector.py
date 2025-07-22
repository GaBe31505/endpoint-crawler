import re
from typing import List, Dict

# Comprehensive regex patterns for legacy endpoints
PATTERNS = {
    'SPRING_CLASS_BASE': re.compile(r'@RequestMapping\(([^)]*)\)'),
    'SPRING_METHOD_MAP': re.compile(r'@(RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\(([^)]*)\)'),
    'STRUTS_XML_ACTION': re.compile(r'<action[^>]+(?:path|name)="([^"]+)"'),
    'STRUTS_ANNOTATION': re.compile(r'@Action\(([^)]*)\)'),
    'JAXRS_PATH': re.compile(r'@Path\("([^"]+)"\)'),
    'SERVLET_MAPPING': re.compile(r'@WebServlet\("([^"]+)"\)'),
    'WEB_XML_MAPPING': re.compile(r'<url-pattern>([^<]+)</url-pattern>'),
    'JSP_HREF': re.compile(r'(?:href|action)="([^\"]+\.jsp)"'),
    'JSP_INCLUDE': re.compile(r'<jsp:include\s+page="([^\"]+)"'),
    'FREEMARKER_URL': re.compile(r'(?:href|action)="([^\"]+\.ftl)"'),
    'REDIRECT': re.compile(r'response\.sendRedirect\(\s*"([^\"]+)"'),
}


def legacy_regex_detector(origin: str, text: str) -> List[Dict]:
    """
    Detect endpoints in legacy code via regex patterns.
    Returns a list of records with fields: endpoint, line, method, controller, source, file.
    """
    records = []
    for name, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            # extract path: prefer second group if present
            try:
                ep = m.group(2)
            except IndexError:
                ep = m.group(1)
            if not ep:
                continue
            line = text[:m.start()].count("\n") + 1
            records.append({
                'endpoint': ep,
                'line': line,
                'method': 'ALL',
                'controller': name,
                'source': 'REGEX_LEGACY',  # will be overwritten by crawler tag
                'file': origin
            })
    return records
