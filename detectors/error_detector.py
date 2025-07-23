from crawler.regex_utils import regex_detector

def error_detector(path: str) -> list:
    """
    Finds @ExceptionHandler mappings in @ControllerAdvice classes.
    """
    pattern = r'@ExceptionHandler\(\s*\{?([^}]+)\}?'
    return regex_detector(path, pattern, source='ERROR')
