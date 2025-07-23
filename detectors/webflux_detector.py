from crawler.regex_utils import regex_detector

def webflux_detector(path: str) -> list:
    """
    Captures functional WebFlux routes (router.GET, GET).
    """
    patterns = [
        (r'router\.\s*(GET|POST|PUT|DELETE|PATCH)\(\s*["\']([^"\']+)["\']', 'WEBFLUX'),
        (r'(GET|POST|PUT|DELETE|PATCH)\(\s*["\']([^"\']+)["\']', 'WEBFLUX'),
    ]
    recs = []
    for pat, tag in patterns:
        recs.extend(regex_detector(path, pat, source=tag))
    return recs
