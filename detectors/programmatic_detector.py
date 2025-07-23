from crawler.regex_utils import regex_detector

def programmatic_detector(path: str) -> list:
    """
    Detects endpoints via programmatic servlet API (addServlet, registerMapping).
    """
    patterns = [
        (r'addServlet\(\s*["\']([^"\']+)["\']', 'PROGRAMMATIC'),
        (r'registerMapping\(\s*["\']([^"\']+)["\']', 'PROGRAMMATIC'),
    ]
    recs = []
    for pat, tag in patterns:
        recs.extend(regex_detector(path, pat, source=tag, method='ALL'))
    return recs
