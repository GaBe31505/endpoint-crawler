from helpers import regex_detector

def static_detector(path: str) -> list:
    return (
        regex_detector(path, r'addResourceHandler\(\s*"([^"]+)"', 'STATIC')
        + regex_detector(path, r'addViewController\(\s*"([^"]+)"', 'STATIC')
    )
