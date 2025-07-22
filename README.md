# Modular Endpoint Crawler

A flexible, high‑coverage static analysis tool to discover all HTTP endpoints in a legacy Java/Spring Boot codebase.

## Features

- **AST Annotation Extraction** (`@RequestMapping`, `@GetMapping`, etc.)
- **JAX‑RS** `@Path` scanning
- **Programmatic Registration** hooks (`registerMapping`, `addServlet`)
- **Spring WebFlux Functional Routes** via `RequestPredicates`
- **Static Resource & View Handlers** (`addResourceHandler`, `addViewController`)
- **Security & CORS Config** (`antMatchers`)
- **Error & Fallback Mappings** (`ErrorController`, `@ControllerAdvice`)
- **XML Config Parsing** (`web.xml`, Struts `.template`)
- **JSP View Discovery** (when mapped)
- **Constant Resolution** for `static final String` paths
- **Parameter Inference** for `{param}` segments
- **Robust Encoding Support**: automatic fallback across UTF‑8, UTF‑16, Latin‑1, CP1252, then ignore errors
- **Dynamic Detector Registration**: drop new detector modules into the `detectors/` directory; register each with a tag and function
- **Multi‑Input Scanning**: accept multiple directories, files, or ZIP/WAR archives in one run
- **Modular Codebase**: `helpers.py`, `detectors/`, `crawler.py`
- **Rich CLI Output**: color‑coded, rounded tables via [Rich](https://github.com/Textualize/rich)
- **Multiple Output Formats**: CSV, JSON, Markdown, Postman Collection

## Installation

```bash
pip install javalang rich
```

Clone the repo:

```bash
git clone <repo-url>
cd endpoint_crawler_modular
```

## Directory Structure

```
endpoint_crawler_modular/
├── crawler.py         # Main entrypoint
├── helpers.py         # Utility functions (file I/O, parsing, encoding)
└── detectors/         # One module per detection strategy
    ├── ast_detector.py
    ├── jaxrs_detector.py
    ├── programmatic_detector.py
    ├── webflux_detector.py
    ├── static_detector.py
    ├── security_detector.py
    ├── error_detector.py
    ├── xml_detector.py
    └── jsp_detector.py
```

## Usage

```bash
python crawler.py \
  -i /path/to/dir file.java archive.zip myapp.war \
  -o endpoints.csv \
  -f csv
```

| Option        | Description                                                     | Default |
|---------------|-----------------------------------------------------------------|---------|
| `-i, --inputs`| One or more directories, individual files, or ZIP/WAR archives   | (none)  |
| `-o, --output`| Path where results will be written (CSV, JSON, Markdown, Postman)| (none)  |
| `-f, --format`| Output format (`csv`, `json`, `markdown`, `postman`)            | `csv`   |

## Output

- **CSV/JSON/Markdown**: columns/fields:
  - `endpoint` — the URL path
  - `confidence` — % score (100 = at least two independent detections)
  - `reason` — which detectors (tags) agreed
  - `params` — comma‑separated `{…}` variables
  - `locations` — `file:line` entries of each detection

- **Postman Collection**:
  - Exports a v2.1.0 collection with GET requests (`{{baseUrl}}` placeholder)
  - Includes `locations` in the request description

## Extending with New Detectors

1. Create a new file in `detectors/`, e.g. `my_detector.py`.
2. Export a function `my_detector(origin: str, text: str) -> List[dict]`:
   ```python
   def my_detector(origin, text):
       # analyze the provided `text`, return list of dicts
       # each dict must have keys: endpoint, line, method, controller, source, file
   ```
3. In `crawler.py`, add an entry to the `DETECTORS` list:
   ```python
   DETECTORS.append(('MYTAG', my_detector))
   ```
4. Re-run the crawler.

## Notes

- **Multi‑Input Support**: scan multiple directories, files, and archives in one pass.
- **In‑Memory Scanning**: detectors operate on provided text for both disk files and archive entries.
- **Dynamic Registration**: detectors are tagged for provenance; drop new modules into `detectors/` and register them.
- **Encoding Robustness**: files are decoded with a fallback chain (UTF‑8 → UTF‑16 → Latin‑1 → CP1252 → ignore errors).
- **Performance**: removing predicate lambdas means all detectors run on all inputs—tune as needed for large codebases.
- Results are grouped by endpoint, deduplicated, and scored by multi‑source provenance.

---

Happy crawling! 🚀
