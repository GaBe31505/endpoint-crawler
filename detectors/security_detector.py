from crawler.regex_utils import regex_detector

def security_detector(path: str) -> list:
    """
    Finds antMatchers(...) patterns in Spring Security config.
    """
    return regex_detector(
        path,
        r'antMatchers\(\s*["\']([^"\']+)["\']',
        source='SECURITY'
    )
