from helpers import regex_detector

def programmatic_detector(path: str) -> list:
    return (
        regex_detector(path, r'registerMapping\s*\(\s*"([^"]+)"', 'PROGRAMMATIC')
        + regex_detector(path, r'addServlet\s*\(\s*"([^"]+)"', 'PROGRAMMATIC')
    )
