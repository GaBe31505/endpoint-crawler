import os

def jsp_detector(root: str) -> list:
    recs = []
    for dp, _, files in os.walk(root):
        for fn in files:
            if fn.lower().endswith('.jsp'):
                rel = os.path.relpath(os.path.join(dp, fn), root)
                recs.append({
                    'endpoint': '/' + rel.replace(os.path.sep, '/'),
                    'line': 0, 'method': 'GET',
                    'controller': 'JSP',
                    'source': 'JSP',
                    'file': dp
                })
    return recs
