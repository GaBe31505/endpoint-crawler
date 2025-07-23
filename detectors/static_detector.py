from crawler.regex_utils import regex_detector

def static_detector(path: str) -> list:
    """
    Detects static view and resource mappings (addViewController, addResourceHandler).
    """
    patterns = [
        (r'addViewController\(\s*["\']([^"\']+)["\']', 'STATIC'),
        (r'addResourceHandler\(\s*["\']([^"\']+)["\']', 'STATIC'),
    ]
    recs = []
    for pat, tag in patterns:
        recs.extend(regex_detector(path, pat, source=tag))
    return recs
