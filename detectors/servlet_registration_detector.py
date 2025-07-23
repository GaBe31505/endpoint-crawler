import re
import xml.etree.ElementTree as ET

def detect_servlet_registration(origin, text):
    """
    Detect endpoints registered via:
      1) web.xml / web-fragment.xml <servlet-mapping> and <filter-mapping>
      2) servletContext.addServlet(...).addMapping(...)
      3) new ServletRegistrationBean<>(new FooServlet(), "/path")
      4) @WebServlet(urlPatterns=...) and @WebFilter(urlPatterns=...)
    """
    # 1) XML-based detection (web.xml & web-fragment.xml)
    if origin.lower().endswith('.xml') and ('<web-app' in text or '<web-fragment' in text):
        try:
            root = ET.fromstring(text)
            # servlet-mapping
            for mapping in root.findall('.//servlet-mapping'):
                ep = mapping.findtext('url-pattern') or ''
                name = mapping.findtext('servlet-name') or None
                yield {
                    'endpoint': ep,
                    'method': None,
                    'controller': name,
                    'file': origin,
                    'line': None,
                    'source': 'detect_servlet_registration'
                }
            # filter-mapping
            for mapping in root.findall('.//filter-mapping'):
                ep = mapping.findtext('url-pattern') or ''
                name = mapping.findtext('filter-name') or None
                yield {
                    'endpoint': ep,
                    'method': None,
                    'controller': name,
                    'file': origin,
                    'line': None,
                    'source': 'detect_servlet_registration'
                }
        except ET.ParseError:
            pass

    # 2) Code-based detection
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        # servletContext.addServlet("name", FooServlet.class).addMapping("/path")
        m1 = re.search(
            r"\.addServlet\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*\w+\.class\s*\)",
            line
        )
        if m1:
            servlet_name = m1.group(1)
            # look ahead for addMapping
            for j in range(idx, min(len(lines), idx+5)):
                m2 = re.search(
                    r"\.addMapping\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
                    lines[j]
                )
                if m2:
                    yield {
                        'endpoint': m2.group(1),
                        'method': None,
                        'controller': servlet_name,
                        'file': origin,
                        'line': j+1,
                        'source': 'detect_servlet_registration'
                    }
                    break

        # new ServletRegistrationBean<>(new FooServlet(), "/path")
        m3 = re.search(
            r"new\s+ServletRegistrationBean<[^>]*>\s*\(\s*new\s+(\w+)\s*\(\)\s*,\s*['\"]([^'\"]+)['\"]",
            line
        )
        if m3:
            servlet_name, ep = m3.group(1), m3.group(2)
            yield {
                'endpoint': ep,
                'method': None,
                'controller': servlet_name,
                'file': origin,
                'line': idx,
                'source': 'detect_servlet_registration'
            }

        # @WebServlet(urlPatterns = "/foo")
        if '@WebServlet' in line:
            m4 = re.search(
                r"@WebServlet\s*\(.*?urlPatterns\s*=\s*\{?['\"]([^'\"]+)['\"]",
                line
            )
            if m4:
                yield {
                    'endpoint': m4.group(1),
                    'method': None,
                    'controller': None,
                    'file': origin,
                    'line': idx,
                    'source': 'detect_servlet_registration'
                }

        # @WebFilter(urlPatterns = "/foo")
        if '@WebFilter' in line:
            m5 = re.search(
                r"@WebFilter\s*\(.*?urlPatterns\s*=\s*\{?['\"]([^'\"]+)['\"]",
                line
            )
            if m5:
                yield {
                    'endpoint': m5.group(1),
                    'method': None,
                    'controller': None,
                    'file': origin,
                    'line': idx,
                    'source': 'detect_servlet_registration'
                }
