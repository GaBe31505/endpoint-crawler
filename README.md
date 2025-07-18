# 🕵️ Endpoint Crawler

A comprehensive Python-based tool to discover REST/API endpoints across multiple frameworks and packaging formats, including:

- ✅ **Spring Boot** (`@RequestMapping`, `@GetMapping`, etc.)
- ✅ **Servlets** (`@WebServlet`)
- ✅ **Struts 1.x / 2.x**
- ✅ **JAX-RS / Jersey**
- ✅ **Freemarker Templates (`.ftl`)**
- ✅ **JSP Tags / Includes (`.jsp`, `.tld`)**
- ✅ **Web XML / Legacy Config Files**
- ✅ **Lightning Web Components (LWC)**
- ✅ **YAML / Properties config** (`server.servlet.context-path`)
- ✅ **Supports `.zip`, `.war`, and directory scanning**

---

## 🚀 Features

- **Multi-Framework Endpoint Discovery**
- **Full Path Resolution**: Combines base path + method path
- **Deduplicated Results by Default**
- **Flag to Show Raw Entries** (`--raw`)
- **Color-Coded Severity in CLI**
- **Support for Archives**: `.zip` and `.war`
- **Detailed Reporting**: Includes line number, file, controller class, method name, etc.
- **Output Formats**: `json`, `csv`, `markdown`, `postman`, `text`
- **Module Inference**: Auto-detects app/module from file paths
- **Encoding-Resilient**: Fallback-safe file reading

---

## 📋 Requirements

- Python 3.7+
- No external dependencies

---

## 📁 Directory Structure

```
endpoint-crawler/
├── crawler.py        # Main script
└── helpers/
    ├── file_utils.py          # Safe file reading
    └── export_utils.py        # Output formatting logic
```

---

## 🔧 Usage

### 🔹 Scan Project Directory

```bash
python crawler.py /path/to/project
```

### 🔹 Scan Multiple Inputs (folders or archives)

```bash
python crawler.py ./service1 ./legacy.zip ./api.war
```

### 🔹 Output Formats

```bash
# JSON (default)
python crawler.py ./src -f json -o endpoints.json

# CSV
python crawler.py ./src -f csv -o endpoints.csv

# Markdown
python crawler.py ./src -f markdown -o report.md

# Plain text
python crawler.py ./src -f text -o summary.txt

# Postman Collection
python crawler.py ./src -f postman -o endpoints.postman.json
```

### 🔹 CLI Output

If no `-o` file is specified, a color-coded CLI summary will be printed:

```bash
[INFO] Detected Endpoints:

- GET    /api/users                          
  ↳ Controller: UserController       Line: 42   Source: SPRING_ANNOTATION       Severity: HIGH
```

Color key:
- 🟥 High (`DELETE`, `PATCH`, unauthenticated)
- 🟨 Medium (`POST`)
- 🟩 Low (`GET`, etc.)

---

## ⚙️ Optional Flags

```bash
--raw             Show all raw endpoint entries without deduplication
-f, --format      Output format: json, csv, markdown, text, postman
-o, --output      Write to output file instead of stdout
```

By default, deduplication merges endpoints with the same path + method and aggregates sources.

---

## 📊 Supported Annotations

### Spring Boot
- `@RequestMapping`
- `@GetMapping`, `@PostMapping`, etc.
- Class-level and method-level combinations
- Constants inside annotations (if resolvable)

### Legacy & Other
- `@WebServlet`
- Struts 1.x `<action path="...">` in XML
- Struts 2 `@Action`, `@Namespace`, `@Result`
- JAX-RS `@Path`, `@GET`, `@POST`
- `web.xml` `<url-pattern>`
- JSP `<jsp:include>`, `action="/some.jsp"`
- Freemarker `href="/some.ftl"` or `action=...`
- Salesforce LWC decorators (experimental)

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
    "parameters": "",
    "source_type": "SPRING_ANNOTATION",
    "severity": "high"
  }
]
```

---

## 🧠 Use Cases

- 🔒 Security Testing & Attack Surface Analysis
- 🧪 API Test Coverage Validation
- 📚 Documentation Generation
- 📦 Legacy Monolith Decomposition
- ⚙️ CI/CD Integration & Change Auditing

---

## 📄 License

MIT License. See `LICENSE` for details.

---
