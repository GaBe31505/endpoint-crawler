# 🕵️ Enhanced Endpoint Crawler

A Python-based static analysis tool that uncovers REST and legacy web endpoints across Java, XML, JSP, and template-based applications. Ideal for decomposing monoliths, auditing APIs, and generating endpoint inventories.

---

## ✅ Supported Technologies

- **Spring Boot**: `@RequestMapping`, `@GetMapping`, etc.
- **Servlets**: `@WebServlet`
- **Struts 1.x / 2.x**: via `struts-config.xml` or annotations
- **JAX-RS**: `@Path(...)` and HTTP method annotations
- **web.xml**: `<url-pattern>...</url-pattern>`
- **JSP**: `href`, `action`, and `<jsp:include>` patterns
- **Freemarker Templates**: `.ftl` file routes and links

---

## 🚀 Features

- 🔍 **Comprehensive Endpoint Discovery** across Java, XML, and HTML template files  
- 🧩 **Modern + Legacy Coverage**: Monoliths, microservices, and mixed-mode systems  
- 📂 **Module-Based Grouping**: Results grouped by inferred module name  
- ⚠️ **Severity Analysis**: Flags potentially sensitive endpoints like `DELETE`, `PATCH`, or unauthenticated routes  
- 🧱 **Route Composition**: Combines class-level and method-level Spring mappings  
- 📦 **Output Formats**: `json`, `csv`, `markdown`, `text`, `postman`  
- 🛠 **Safe File Parsing**: UTF-8, ISO-8859-1, cp1252, and more  

---

## 📋 Requirements

- Python 3.7+
- No external dependencies

---

## 📁 Project Structure

```
enhanced_endpoint_crawler/
├── crawler.py                 # Main scanner
└── helpers/
    ├── file_utils.py          # Encoding-resilient file reader
    └── export_utils.py        # Output format generators
```

---

## 🔧 Usage

### Scan a Directory or Archive
```bash
python crawler.py ./src
python crawler.py ./project.zip
```

### Output to CSV or Markdown
```bash
python crawler.py ./src -f csv -o endpoints.csv
python crawler.py ./src -f markdown -o endpoints.md
```

### Grouped Markdown Output
Markdown is grouped by module and sorted by controller class.

---

## 🧠 Output Fields

| Field            | Description                                           |
|------------------|-------------------------------------------------------|
| `method`         | HTTP method (`GET`, `POST`, etc.)                    |
| `path`           | Endpoint path from method-level annotation           |
| `base_path`      | Class-level base mapping (if any)                    |
| `full_path`      | Combined `base_path + path`                          |
| `controller_class` | Name of the controller or source file              |
| `method_name`    | Method name if detected (`"unknown"` for now)        |
| `file_path`      | Source file with relative or absolute path           |
| `line_number`    | Approximate line where it was found                  |
| `parameters`     | Placeholder (can be extended)                        |
| `source_type`    | `SPRING_ANNOTATION`, `STRUTS_XML`, etc.              |
| `severity`       | `low`, `medium`, or `high` based on risk             |
| `module`         | Inferred from file structure (`apps/foo/`)           |

---

## 🧪 Postman Collection Export

```bash
python crawler.py ./src -f postman -o postman_collection.json
```

Use `{{baseUrl}}` in your environment for testing.

---

## 🧠 Use Cases

- 📚 API Inventory & Documentation
- 🔐 Security Surface Mapping
- 🛠 Refactor Legacy Systems
- 🧪 Test Coverage Analysis
- 🧼 Dead Code & Orphaned Endpoint Detection

---

## 📄 License

MIT License. See `LICENSE` for details.
