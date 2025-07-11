#!/usr/bin/env python3
"""
Spring Boot Endpoint Crawler
Analyzes Spring Boot source code to find all REST endpoints and their mappings.
Supports multiple repositories and various Spring Boot annotation patterns.
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Endpoint:
    """Represents a discovered endpoint"""
    path: str
    method: str
    controller_class: str
    method_name: str
    file_path: str
    line_number: int
    base_path: str = ""
    full_path: str = ""
    parameters: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        # Construct full path
        base = self.base_path.rstrip('/')
        path = self.path.lstrip('/')
        self.full_path = f"{base}/{path}" if base else f"/{path}"
        # Clean up double slashes
        self.full_path = re.sub(r'/+', '/', self.full_path)
        if not self.full_path.startswith('/'):
            self.full_path = '/' + self.full_path

class SpringBootEndpointCrawler:
    """Main crawler class for analyzing Spring Boot endpoints"""
    
    def __init__(self):
        self.endpoints: List[Endpoint] = []
        self.java_files: List[Path] = []
        self.yaml_files: List[Path] = []
        
        # Spring Boot mapping annotations
        self.mapping_annotations = {
            'RequestMapping': 'ANY',
            'GetMapping': 'GET',
            'PostMapping': 'POST',
            'PutMapping': 'PUT',
            'DeleteMapping': 'DELETE',
            'PatchMapping': 'PATCH',
            'HeadMapping': 'HEAD',
            'OptionsMapping': 'OPTIONS'
        }
        
        # Patterns for finding endpoints
        self.annotation_pattern = re.compile(
            r'@(' + '|'.join(self.mapping_annotations.keys()) + r')\s*(?:\((.*?)\))?',
            re.DOTALL
        )
        
        self.class_annotation_pattern = re.compile(
            r'@(RestController|Controller|RequestMapping)\s*(?:\((.*?)\))?',
            re.DOTALL
        )
        
        self.method_pattern = re.compile(
            r'(public|private|protected)?\s*[\w<>\[\],\s]*\s+(\w+)\s*\([^)]*\)\s*(?:throws[^{]*)?{',
            re.MULTILINE
        )
        
        # Path value extraction patterns
        self.path_pattern = re.compile(r'(?:value\s*=\s*|path\s*=\s*)?["\']([^"\']+)["\']')
        self.method_attr_pattern = re.compile(r'method\s*=\s*RequestMethod\.(\w+)')
        
    def find_java_files(self, root_paths: List[str]) -> None:
        """Find all Java files in the given root paths"""
        for root_path in root_paths:
            root = Path(root_path)
            if not root.exists():
                logger.warning(f"Path does not exist: {root_path}")
                continue
                
            # Find Java files
            java_files = list(root.rglob("*.java"))
            self.java_files.extend(java_files)
            
            # Find YAML/Properties files for configuration
            yaml_files = list(root.rglob("*.yml")) + list(root.rglob("*.yaml")) + list(root.rglob("*.properties"))
            self.yaml_files.extend(yaml_files)
            
        logger.info(f"Found {len(self.java_files)} Java files and {len(self.yaml_files)} config files")
    
    def extract_path_from_annotation(self, annotation_content: str) -> Tuple[str, Optional[str]]:
        """Extract path and method from annotation content"""
        if not annotation_content:
            return "", None
            
        # Clean up the annotation content
        annotation_content = annotation_content.strip()
        
        # Look for path/value
        path_match = self.path_pattern.search(annotation_content)
        path = path_match.group(1) if path_match else ""
        
        # Look for method specification (for @RequestMapping)
        method_match = self.method_attr_pattern.search(annotation_content)
        method = method_match.group(1) if method_match else None
        
        return path, method
    
    def extract_class_base_path(self, file_content: str) -> str:
        """Extract base path from class-level annotations"""
        lines = file_content.split('\n')
        class_found = False
        
        for i, line in enumerate(lines):
            # Look for class-level annotations
            if '@RequestMapping' in line:
                # Extract the annotation content
                annotation_content = line
                if '(' in line and ')' not in line:
                    # Multi-line annotation
                    j = i + 1
                    while j < len(lines) and ')' not in lines[j]:
                        annotation_content += lines[j]
                        j += 1
                    if j < len(lines):
                        annotation_content += lines[j]
                
                # Extract path
                path, _ = self.extract_path_from_annotation(annotation_content)
                if path:
                    return path
                    
            # Check if we've reached the class declaration
            if re.search(r'class\s+\w+', line):
                break
                
        return ""
    
    def extract_method_parameters(self, method_signature: str) -> List[str]:
        """Extract path parameters from method signature"""
        parameters = []
        
        # Look for @PathVariable annotations
        path_var_pattern = re.compile(r'@PathVariable(?:\([^)]*\))?\s+\w+\s+(\w+)')
        path_vars = path_var_pattern.findall(method_signature)
        parameters.extend(path_vars)
        
        # Look for @RequestParam annotations
        request_param_pattern = re.compile(r'@RequestParam(?:\([^)]*\))?\s+\w+\s+(\w+)')
        request_params = request_param_pattern.findall(method_signature)
        parameters.extend([f"{p}(param)" for p in request_params])
        
        return parameters
    
    def analyze_java_file(self, file_path: Path) -> None:
        """Analyze a single Java file for endpoints"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return
        
        # Check if this is a controller class
        if not (re.search(r'@RestController|@Controller', content)):
            return
            
        logger.debug(f"Analyzing controller: {file_path}")
        
        # Extract class name
        class_match = re.search(r'class\s+(\w+)', content)
        class_name = class_match.group(1) if class_match else "Unknown"
        
        # Extract base path from class-level annotations
        base_path = self.extract_class_base_path(content)
        
        # Split content into lines for line number tracking
        lines = content.split('\n')
        
        # Find all mapping annotations
        for match in self.annotation_pattern.finditer(content):
            annotation_name = match.group(1)
            annotation_content = match.group(2) or ""
            
            # Determine HTTP method
            if annotation_name in self.mapping_annotations:
                http_method = self.mapping_annotations[annotation_name]
            else:
                continue
                
            # Extract path and method from annotation
            path, method_override = self.extract_path_from_annotation(annotation_content)
            
            # Use method override if specified (for @RequestMapping)
            if method_override:
                http_method = method_override
            
            # Find the method this annotation belongs to
            method_start = match.end()
            method_search = content[method_start:method_start + 1000]  # Look ahead
            method_match = self.method_pattern.search(method_search)
            
            if method_match:
                method_name = method_match.group(2)
                
                # Find line number
                line_number = content[:match.start()].count('\n') + 1
                
                # Extract method parameters
                full_method = content[method_start:method_start + method_match.end()]
                parameters = self.extract_method_parameters(full_method)
                
                # Create endpoint
                endpoint = Endpoint(
                    path=path,
                    method=http_method,
                    controller_class=class_name,
                    method_name=method_name,
                    file_path=str(file_path),
                    line_number=line_number,
                    base_path=base_path,
                    parameters=parameters
                )
                
                self.endpoints.append(endpoint)
                logger.debug(f"Found endpoint: {http_method} {endpoint.full_path}")
    
    def get_server_context_path(self) -> str:
        """Extract server context path from configuration files"""
        context_path = ""
        
        for config_file in self.yaml_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for server.servlet.context-path in YAML
                yaml_match = re.search(r'server:\s*\n\s*servlet:\s*\n\s*context-path:\s*([^\n]+)', content)
                if yaml_match:
                    context_path = yaml_match.group(1).strip().strip('"\'')
                    break
                    
                # Look for server.servlet.context-path in properties
                props_match = re.search(r'server\.servlet\.context-path\s*=\s*([^\n]+)', content)
                if props_match:
                    context_path = props_match.group(1).strip().strip('"\'')
                    break
                    
            except Exception as e:
                logger.error(f"Error reading config file {config_file}: {e}")
                
        return context_path
    
    def crawl(self, root_paths: List[str]) -> List[Endpoint]:
        """Main crawling method"""
        logger.info(f"Starting crawl of paths: {root_paths}")
        
        # Find all Java files
        self.find_java_files(root_paths)
        
        # Analyze each Java file
        for java_file in self.java_files:
            self.analyze_java_file(java_file)
        
        # Get server context path
        context_path = self.get_server_context_path()
        
        # Update endpoints with context path
        if context_path:
            for endpoint in self.endpoints:
                endpoint.full_path = f"{context_path.rstrip('/')}{endpoint.full_path}"
        
        logger.info(f"Found {len(self.endpoints)} endpoints")
        return self.endpoints
    
    def generate_report(self, output_format: str = 'json') -> str:
        """Generate a report of all discovered endpoints"""
        if output_format.lower() == 'json':
            return self._generate_json_report()
        elif output_format.lower() == 'csv':
            return self._generate_csv_report()
        elif output_format.lower() == 'markdown':
            return self._generate_markdown_report()
        else:
            return self._generate_text_report()
    
    def _generate_json_report(self) -> str:
        """Generate JSON report"""
        endpoints_data = []
        for endpoint in self.endpoints:
            endpoints_data.append({
                'method': endpoint.method,
                'path': endpoint.full_path,
                'controller': endpoint.controller_class,
                'method_name': endpoint.method_name,
                'file_path': endpoint.file_path,
                'line_number': endpoint.line_number,
                'parameters': endpoint.parameters
            })
        
        return json.dumps({
            'total_endpoints': len(self.endpoints),
            'endpoints': endpoints_data
        }, indent=2)
    
    def _generate_csv_report(self) -> str:
        """Generate CSV report"""
        lines = ['Method,Path,Controller,Method Name,File Path,Line Number,Parameters']
        for endpoint in self.endpoints:
            params = ';'.join(endpoint.parameters) if endpoint.parameters else ''
            lines.append(f'{endpoint.method},{endpoint.full_path},{endpoint.controller_class},{endpoint.method_name},{endpoint.file_path},{endpoint.line_number},"{params}"')
        return '\n'.join(lines)
    
    def _generate_markdown_report(self) -> str:
        """Generate Markdown report"""
        lines = [
            '# Spring Boot Endpoints Report',
            f'Total endpoints found: {len(self.endpoints)}',
            '',
            '## Endpoints',
            '| Method | Path | Controller | Method Name | File | Line |',
            '|--------|------|------------|-------------|------|------|'
        ]
        
        for endpoint in self.endpoints:
            file_name = os.path.basename(endpoint.file_path)
            lines.append(f'| {endpoint.method} | {endpoint.full_path} | {endpoint.controller_class} | {endpoint.method_name} | {file_name} | {endpoint.line_number} |')
        
        return '\n'.join(lines)
    
    def _generate_text_report(self) -> str:
        """Generate plain text report"""
        lines = [
            'Spring Boot Endpoints Report',
            '=' * 30,
            f'Total endpoints found: {len(self.endpoints)}',
            ''
        ]
        
        # Group by controller
        controllers = {}
        for endpoint in self.endpoints:
            if endpoint.controller_class not in controllers:
                controllers[endpoint.controller_class] = []
            controllers[endpoint.controller_class].append(endpoint)
        
        for controller, endpoints in controllers.items():
            lines.append(f'Controller: {controller}')
            lines.append('-' * (len(controller) + 12))
            for endpoint in endpoints:
                params_str = f" (params: {', '.join(endpoint.parameters)})" if endpoint.parameters else ""
                lines.append(f'  {endpoint.method:<8} {endpoint.full_path}{params_str}')
                lines.append(f'           -> {endpoint.method_name}() [{os.path.basename(endpoint.file_path)}:{endpoint.line_number}]')
            lines.append('')
        
        return '\n'.join(lines)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Crawl Spring Boot repositories for REST endpoints')
    parser.add_argument('paths', nargs='+', help='Root paths to crawl (can be multiple repositories)')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-f', '--format', choices=['json', 'csv', 'markdown', 'text'], 
                       default='json', help='Output format (default: json)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create crawler and run
    crawler = SpringBootEndpointCrawler()
    endpoints = crawler.crawl(args.paths)
    
    # Generate report
    report = crawler.generate_report(args.format)
    
    # Output report
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Report saved to {args.output}")
    else:
        print(report)
    
    # Summary
    logger.info(f"Crawl completed. Found {len(endpoints)} endpoints across {len(crawler.java_files)} Java files.")

if __name__ == '__main__':
    main()
