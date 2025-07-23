import os
from crawler.io import read_file

def jsp_detector(path: str) -> list:
    """
    Maps JSP filenames to endpoint paths, respecting /WEB-INF/views layout.
    """
    recs = []
    if not path.endswith('.jsp'):
        return recs

    if '/WEB-INF/views/' in path.replace('\\','/'):
        suffix = path.split('/WEB-INF/views/')[-1]
        endpoint = '/' + suffix.replace('\\','/')
    else:
        name = os.path.splitext(os.path.basename(path))[0]
        endpoint = f"/{name}.jsp"

    recs.append({
        'endpoint':   endpoint,
        'method':     'ALL',
        'controller': '',
        'line':       1,
        'source':     'JSP',
        'file':       path
    })
    return recs
