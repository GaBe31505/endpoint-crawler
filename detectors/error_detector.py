import os

def error_detector(path: str) -> list:
    recs = []
    txt = open(path,'r',errors='ignore').read()
    for kw in ('@ControllerAdvice','implements ErrorController'):
        idx = txt.find(kw)
        if idx >= 0:
            line = txt[:idx].count('\n') + 1
            controller = os.path.splitext(os.path.basename(path))[0]
            recs.append({
                'endpoint': '/error',
                'line': line,
                'method': 'ALL',
                'controller': controller,
                'source': 'ERROR',
                'file': path
            })
    return recs
