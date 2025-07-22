import xml.etree.ElementTree as ET

def xml_detector(path: str) -> list:
    recs = []
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except:
        return recs
    for up in root.findall('.//servlet-mapping/url-pattern'):
        if up.text:
            recs.append({
                'endpoint': up.text.strip(),
                'line': 0, 'method': 'ALL',
                'controller': 'XML',
                'source': 'XML',
                'file': path
            })
    for action in root.findall('.//action'):
        p = action.get('path')
        if p:
            recs.append({
                'endpoint': p,
                'line': 0, 'method': 'ALL',
                'controller': 'Struts',
                'source': 'XML',
                'file': path
            })
    for action in root.findall('.//package/action'):
        name = action.get('name')
        if name:
            recs.append({
                'endpoint': '/' + name,
                'line': 0, 'method': 'ALL',
                'controller': 'Struts',
                'source': 'XML',
                'file': path
            })
    return recs
