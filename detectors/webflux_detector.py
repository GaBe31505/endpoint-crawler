from helpers import regex_detector

def webflux_detector(path: str) -> list:
    return regex_detector(
        path,
        r'RequestPredicates\.(?:GET|POST|PUT|DELETE|PATCH)\(\s*"([^"]+)"',
        'WEBFLUX'
    )
