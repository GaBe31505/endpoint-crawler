from helpers import regex_detector

def security_detector(path: str) -> list:
    return regex_detector(path, r'antMatchers\(\s*"([^"]+)"', 'SECURITY')
