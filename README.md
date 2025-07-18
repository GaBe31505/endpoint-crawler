# 🕵️ Endpoint Crawler

A comprehensive Python-based tool to discover REST/API endpoints across multiple frameworks and packaging formats, including:

- ✅ **Spring Boot** (`@RequestMapping`, `@GetMapping`, etc.)
- ✅ **Servlets** (`@WebServlet`)
- ✅ **Struts 1.x / 2.x**
- ✅ **JAX-RS**
- ✅ **Express.js** (Node.js)
- ✅ **Angular Router** (AngularJS & Angular 2+)
- ✅ **YAML/Properties config** (for `server.servlet.context-path`)
- ✅ **Supports `.zip`, `.war`, and directory scanning**

---

## 🚀 Features

- **Endpoint Discovery**: Finds REST endpoints across multiple frameworks
- **Multi-Repository & Archive Support**: Scan folders, `.zip`, and `.war` files
- **Complete URL Construction**: Combines context path, class-level, and method-level mappings
- **Parameter Detection**: Detects path variables and request parameters
- **Multiple Output Formats**: JSON, CSV, Markdown, Postman, and plain text reports
- **Configuration Analysis**: Reads application properties and YAML files
- **Detailed Reporting**: Controller class, method, file location, line number
- **Encoding Resilient**: Safely reads files with multiple fallback encodings

---

## 📋 Requirements

- Python 3.7+
- No external Python dependencies

---

## 📁 Directory Structure

```
endpoint-crawler/
├── endpoint_crawler.py        # Main script
└── helpers/
    ├── file_utils.py          # Safe file reading utilities
    └── export_utils.py        # Output formatting utilities
```

---

## 🔧 Usage

### 🔹 Basic Usage

```bash
python endpoint_crawler.py /path/to/project
```

### 🔹 Scan Multiple Paths (folders, zips, wars)

```bash
python endpoint_crawler.py ./service1 ./legacy.zip ./api.war
```

### 🔹 Output Formats

```bash
# JSON output (default)
python endpoint_crawler.py ./src -f json -o endpoints.json

# CSV
python endpoint_crawler.py ./src -f csv -o endpoints.csv

# Markdown
python endpoint_crawler.py ./src -f markdown -o report.md

# Plain text
python endpoint_crawler.py ./src -f text -o summary.txt

# Postman collection
python endpoint_crawler.py ./src -f postman -o postman_collection.json
```

### 🔹 Command-Line Options

```bash
Usage:
  python endpoint_crawler.py [OPTIONS] PATHS...

Arguments:
  PATHS...                 One or more directories or archives (.zip/.war)

Options:
  -f, --format FORMAT      Output format: json, csv, markdown, postman, text
  -o, --output PATH        Output file (default: print to stdout)
  -h, --help               Show help message
```

---

## 📊 Supported Annotations

### Spring Boot
- `@RequestMapping`
- `@GetMapping`
- `@PostMapping`
- `@PutMapping`
- `@DeleteMapping`
- `@PatchMapping`
- JAX-RS equivalents like `@Path`

### Others
- `@WebServlet` (Servlets)
- Struts `action` XML path attributes
- Express `app.get/post/put/...`
- Angular `RouterModule.forRoot()` or route array definitions

---

## 📤 Sample Output (JSON)

```json
[
  {
    "method": "GET",
    "full_path": "/api/v1/users",
    "controller_class": "UserController",
    "method_name": "getUsers",
    "file_path": "/src/UserController.java",
    "line_number": 42,
    "parameters": []
  }
]
```

---

## 📬 Postman Export

Exports a v2.1 compatible Postman Collection:
```bash
python endpoint_crawler.py ./src -f postman -o endpoints.postman.json
```

You can then import this file into Postman and configure `{{baseUrl}}` as an environment variable.

---

## 🏗️ Project Use Cases

- 📚 API Documentation
- 🔒 Security Audits
- ⚙️ CI/CD Integration
- 🧪 Test Coverage Validation
- 📦 Legacy Monolith Decomposition
- 🔍 Endpoint Surface Analysis

---

## 📄 License

MIT License. See `LICENSE` for details.

---
