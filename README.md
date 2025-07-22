# 🕵️ Endpoint Crawler

A comprehensive Python-based tool to discover REST/API endpoints across multiple frameworks and packaging formats.

---

## ✅ Supported Technologies

- **Spring Boot** (`@RequestMapping`, `@GetMapping`, etc.)
- **Servlets** (`@WebServlet`)
- **Struts 1.x / 2.x**
- **JAX-RS** (`@Path`)
- **Freemarker Templates** (`*.ftl`)
- **JSP Includes / Taglibs** (`.jsp`, `.tag`, `.tld`)
- **web.xml / struts-config.xml** mappings
- **Lightning Web Components (LWC)** / Salesforce Apex
- **Java Constants** used in mapping
- **Express.js** (Node.js)
- **Angular (JS and TS)**
- **YAML/Properties config** (`server.servlet.context-path`)
- **Custom DispatcherServlet / HandlerMappings**
- **SOA / EJB / Remote Interfaces**
- Supports `.zip`, `.war`, and directory scanning

---

## 🚀 Features

- ✅ Endpoint Discovery across legacy and modern Java apps
- ✅ Multi-Repository & Archive Support: folders, `.zip`, and `.war`
- ✅ Base Path + Method Path + Context Path merging
- ✅ Java Constant Resolution
- ✅ Color-coded CLI Output by Severity
- ✅ CLI Output Grouped by Module (with section headers)
- ✅ Deduplication of endpoints across files (default)
- ✅ `--raw` flag to disable deduplication and view raw results
- ✅ Output Formats: JSON, CSV, Markdown, Postman, Plain Text
- ✅ Encodes line numbers, controller class, and source type
- ✅ No external dependencies

---

## 📁 Directory Structure

```
endpoint-crawler/
├── endpoint_crawler.py        # Main CLI
└── helpers/
    ├── file_utils.py          # File reading with encoding fallback
    └── export_utils.py        # Export handlers for all formats
```

---

## 🔧 Usage

### 🔹 Basic Usage

```bash
python endpoint_crawler.py /path/to/project
```

### 🔹 Output to File

```bash
python endpoint_crawler.py ./src -f json -o endpoints.json
```

### 🔹 Show Raw Output (disable deduplication)

```bash
python endpoint_crawler.py ./src --raw
```

---

## 🖥️ Pretty CLI Output

When `-o` is not used, output is shown in the terminal:

```
[INFO] Detected Endpoints:

📦 Module: user-service (3 endpoints)
─────────────────────────────────────
🟥 DELETE /api/v1/users/{id}
    ├─ Controller: UserController
    ├─ Line:       88
    ├─ Source:     SPRING_ANNOTATION
    └─ Severity:   HIGH

🟨 POST   /api/v1/users
    ├─ Controller: UserController
    ├─ Line:       42
    ├─ Source:     SPRING_ANNOTATION
    └─ Severity:   MEDIUM
```

---

## 📤 Export Formats

```bash
# JSON
python endpoint_crawler.py ./src -f json -o endpoints.json

# CSV
python endpoint_crawler.py ./src -f csv -o endpoints.csv

# Markdown
python endpoint_crawler.py ./src -f markdown -o endpoints.md

# Plain text
python endpoint_crawler.py ./src -f text -o summary.txt

# Postman Collection
python endpoint_crawler.py ./src -f postman -o endpoints.postman.json
```

---

## 📊 Sample Output (JSON)

```json
[
  {
    "method": "GET",
    "full_path": "/api/v1/users",
    "controller_class": "UserController",
    "method_name": "getUsers",
    "file_path": "/src/UserController.java",
    "line_number": 42,
    "parameters": [],
    "severity": "low",
    "source_type": "SPRING_ANNOTATION"
  }
]
```

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