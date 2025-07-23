import re
from crawler.io import read_file
from pathlib import Path


def regex_detector(path: str, pattern: str, source: str, method: str='ALL') -> list:
    recs=[]
    txt = read_file(path)
    for m in re.finditer(pattern,txt):
        ep = m.group(1)
        line_no = txt[:m.start()].count('')+1
        ctrl = Path(path).stem
        recs.append({'endpoint':ep,'line':line_no,'method':method,'controller':ctrl,'source':source,'file':path})
    return recs