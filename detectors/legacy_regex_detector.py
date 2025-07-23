from crawler.regex_utils import regex_detector

def legacy_regex_detector(path: str) -> list:
    """
    Captures mappings via legacy @RequestMapping and shortcuts.
    """
    patterns = [
        (r'@(RequestMapping)\(.*path\s*=\s*["\']([^"\']+)["\']', 'LEGACY_REGEX'),
        (r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\(\s*["\']([^"\']+)["\']\)', 'LEGACY_REGEX')
    ]
    recs = []
    for pat, tag in patterns:
        recs.extend(regex_detector(path, pat, source=tag))
    return recs
