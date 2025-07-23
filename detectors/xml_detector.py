import xml.etree.ElementTree as ET

def xml_detector(path: str) -> list:
    """
    Parses web.xml mappings including servlet-mapping and filter-mapping url-pattern entries.
    """
    recs = []
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        for tag in ('servlet-mapping','filter-mapping'):
            for up in root.findall(f'.//{tag}/url-pattern'):
                recs.append({
                    'endpoint':   up.text or '',
                    'method':     'ALL',
                    'controller': '',
                    'line':       1,
                    'source':     tag.upper(),
                    'file':       path
                })
    except Exception:
        pass
    return recs
