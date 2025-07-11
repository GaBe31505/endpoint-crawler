# Spring Boot Endpoint Crawler
Simple python script that analyzes Spring Boot source code repositories to automatically discover and catalog all REST endpoints.

## 🚀 Features

- **Endpoint Discovery**: Finds all REST endpoints using Spring Boot annotations
- **Multi-Repository Support**: Analyze multiple repositories simultaneously
- **Complete URL Construction**: Combines base paths, class-level mappings, and server context paths
- **Parameter Detection**: Identifies path variables and request parameters
- **Multiple Output Formats**: JSON, CSV, Markdown, and plain text reports
- **Configuration Analysis**: Reads application properties and YAML files for context paths
- **Detailed Reporting**: Includes controller classes, method names, file locations, and line numbers

## 📋 Requirements

- Python 3.6+
- Spring Boot projects with standard annotation patterns

## 🛠️ Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/springboot-endpoint-crawler.git
cd springboot-endpoint-crawler
```

2. Make the script executable:
```bash
chmod +x springboot_crawler.py
```

## 🔧 Usage

### Basic Usage

Analyze a single Spring Boot repository:
```bash
python3 springboot_crawler.py /path/to/springboot/repo
```

### Multiple Repositories

Analyze multiple repositories at once:
```bash
python3 springboot_crawler.py /path/to/repo1 /path/to/repo2 /path/to/repo3
```

### Output Formats

Generate reports in different formats:
```bash
# JSON output (default)
python3 springboot_crawler.py /path/to/repo -f json -o endpoints.json

# CSV format
python3 springboot_crawler.py /path/to/repo -f csv -o endpoints.csv

# Markdown format
python3 springboot_crawler.py /path/to/repo -f markdown -o endpoints.md

# Plain text format
python3 springboot_crawler.py /path/to/repo -f text -o endpoints.txt
```

### Command Line Options

```bash
python3 springboot_crawler.py [OPTIONS] PATHS...

Arguments:
  PATHS...                One or more root paths to crawl

Options:
  -o, --output PATH       Output file path
  -f, --format FORMAT     Output format: json, csv, markdown, text (default: json)
  -v, --verbose          Enable verbose logging
  -h, --help             Show help message
```

## 📊 Supported Annotations

The crawler detects the following Spring Boot annotations:

- `@RequestMapping` - Generic request mapping
- `@GetMapping` - HTTP GET requests
- `@PostMapping` - HTTP POST requests
- `@PutMapping` - HTTP PUT requests
- `@DeleteMapping` - HTTP DELETE requests
- `@PatchMapping` - HTTP PATCH requests
- `@HeadMapping` - HTTP HEAD requests
- `@OptionsMapping` - HTTP OPTIONS requests

## 🔍 What It Finds

The crawler identifies and reports:

- **Complete URL paths** including context paths and base paths
- **HTTP methods** (GET, POST, PUT, DELETE, etc.)
- **Controller classes** and method names
- **File locations** and line numbers
- **Path variables** (`@PathVariable`)
- **Request parameters** (`@RequestParam`)
- **Server context paths** from configuration files

## 📄 Sample Output

### JSON Format
```json
{
  "total_endpoints": 12,
  "endpoints": [
    {
      "method": "GET",
      "path": "/api/v1/users/{id}",
      "controller": "UserController",
      "method_name": "getUser",
      "file_path": "/src/main/java/com/example/UserController.java",
      "line_number": 45,
      "parameters": ["id"]
    }
  ]
}
```

### Markdown Format
```markdown
# Spring Boot Endpoints Report
Total endpoints found: 12

## Endpoints
| Method | Path | Controller | Method Name | File | Line |
|--------|------|------------|-------------|------|------|
| GET | /api/v1/users/{id} | UserController | getUser | UserController.java | 45 |
| POST | /api/v1/users | UserController | createUser | UserController.java | 52 |
```

## 🏗️ Project Structure

```
springboot-endpoint-crawler/
├── springboot_crawler.py    # Main crawler script
├── README.md               # This file
├── LICENSE                 # License file
└── examples/               # Example output files
    ├── sample_output.json
    ├── sample_output.csv
    └── sample_output.md
```

## 🎯 Use Cases

- **API Documentation**: Generate comprehensive endpoint inventories
- **Security Audits**: Identify all exposed endpoints across microservices
- **DevOps**: Automate endpoint discovery in CI/CD pipelines
- **Code Reviews**: Understand API surface area changes
- **Migration Planning**: Catalog endpoints before refactoring
- **Testing**: Ensure comprehensive API test coverage

## 🔧 Configuration Support

The crawler reads configuration from:
- `application.yml` / `application.yaml`
- `application.properties`
- Environment-specific config files

It extracts:
- Server context paths (`server.servlet.context-path`)
- Port configurations
- Base URL configurations

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

