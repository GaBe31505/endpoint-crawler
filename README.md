# Endpoint Discovery for Java/Spring Boot

A flexible, high‑coverage static analysis tool that automatically discovers HTTP endpoints and routes in Java/Spring Boot codebases via a pluggable detector architecture.

---

## Features

| Feature                  | Description                                                           |
|--------------------------|-----------------------------------------------------------------------|
| **Dynamic Detector Loading** | Auto‑discovers all `detect_*` functions in `detectors/`              |
| **Easy Extensibility**   | Add or remove detectors by dropping `.py` files into `detectors/`    |
| **Robust Orchestration** | Deduplicates identical findings; isolates detector failures          |
| **Multiple Output Modes**| CLI table, CSV, JSON, Markdown, Postman collection                   |

---

## Installation

```bash
# Clone & prepare environment
git clone https://your.repo.url/endpoint-crawler.git
cd endpoint-crawler
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Directory Structure

```text
project-root/
├── crawler/               # Core engine and utilities
│   ├── detect.py          # Dynamic loader & orchestration
│   ├── cli.py             # Command‑line interface
│   ├── io.py              # Input walking & file I/O
│   ├── parsing.py         # Java AST helpers
│   ├── regex_utils.py     # Generic regex detection helper
│   ├── zip_utils.py       # Archive unpacking helper
│   ├── aggregate.py       # Deduplication & sorting of findings
│   └── render.py          # Output formatting logic
├── detectors/             # Detector modules (v4 & v5)
│   ├── ast_detector.py
│   ├── cors_detector.py
│   ├── error_detector.py
│   ├── jsp_detector.py
│   ├── legacy_regex_detector.py
│   ├── preauthorize_detector.py
│   ├── programmatic_detector.py
│   ├── security_detector.py
│   ├── servlet_registration_detector.py
│   ├── static_detector.py
│   ├── webflux_detector.py
│   └── xml_detector.py
└── README.md              # Project overview and quickstart
```

---

## Usage

### Command‑Line Interface

```bash
# Module invocation (recommended)
python3 -m crawler.cli -i <paths> [-o <output_file>] [-f <format>]

# Direct script execution
python crawler/cli.py -i <paths> [-o <output_file>] [-f <format>]
```

#### Options

| Flag             | Description                                                       |
|------------------|-------------------------------------------------------------------|
| `-i, --input`    | **Required.** One or more input directories, files, or archives.  |
| `-o, --output`   | **Optional.** Output file; omit to print CLI table.               |
| `-f, --format`   | **Optional.** `json` (default), `csv`, `markdown`, `postman`.     |

#### Examples

```bash
# Print CLI table (default)
python3 -m crawler.cli -i ./src

# Generate CSV report
python3 -m crawler.cli -i ./src -o endpoints.csv -f csv

# Generate JSON report
python3 -m crawler.cli -i ./src -o report.json -f json

# Generate Markdown table
python3 -m crawler.cli -i ./src -o report.md -f markdown

# Generate Postman collection
python3 -m crawler.cli -i ./src -o collection.json -f postman
```

---

## Output Formats

| Format      | Description                                                   |
|-------------|---------------------------------------------------------------|
| **CLI**     | GitHub‑style table printed to stdout (default)                |
| **CSV**     | Comma‑separated values with header row                        |
| **JSON**    | Array of objects with detailed fields                         |
| **Markdown**| GitHub‑flavored markdown table                                |
| **Postman** | Postman v2.1.0 collection with `{{baseUrl}}` host variable    |

---

## Record Fields

| Field        | Type    | Description                               |
|--------------|---------|-------------------------------------------|
| `endpoint`   | string  | URL path or regex pattern                 |
| `method`     | string  | HTTP verb(s) or `ALL`                     |
| `controller` | string  | Handler class or package name             |
| `file`       | string  | Origin file or archive path               |
| `line`       | integer | Source line number                        |
| `source`     | string  | Detector name                             |
| `confidence` | number  | Detection confidence score (optional)     |
| `extra`      | object  | Detector‑specific metadata (optional)     |

---

## Adding Custom Detectors

1. **Create** a new file `detectors/detect_<feature>.py`.
2. **Define** one or more `detect_` functions:
   ```python
   def detect_<feature>(path: str, content: str) -> List[dict]:
       # path: file path or identifier
       # content: file contents as string
       # returns: list of record dicts with keys:
       #   endpoint, method, controller, file, line, source
       # detection logic here
   ```
3. **Save** the file—it's auto‑loaded on the next run.

---
