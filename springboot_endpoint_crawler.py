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
        self.spring_mapping_annotations = {
            'RequestMapping': 'ANY',
            'GetMapping': 'GET',
            'PostMapping': 'POST',
            'PutMapping': 'PUT',
            'DeleteMapping': 'DELETE',
            'PatchMapping': 'PATCH',
            'HeadMapping': 'HEAD',
            'OptionsMapping': 'OPTIONS'
        }
        
        # JAX-RS annotations
        self.jaxrs_annotations = {
            'GET': 'GET',
            'POST': 'POST',
            'PUT': 'PUT',
            'DELETE': 'DELETE',
            'PATCH': 'PATCH',
            'HEAD': 'HEAD',
            'OPTIONS': 'OPTIONS'
        }
        
        # Struts annotations
        self.struts_annotations = {
            'Action': 'ANY',
            'Actions': 'ANY',
            'Result': 'ANY',
            'Results': 'ANY'
        }
        
        # Combine all annotations
        self.all_annotations = {
            **self.spring_mapping_annotations,
            **self.jaxrs_annotations,
            **self.struts_annotations
        }
        
        # Patterns for finding endpoints
        self.spring_annotation_pattern = re.compile(
            r'@(' + '|'.join(self.spring_mapping_annotations.keys()) + r')\s*(?:\((.*?)\))?',
            re.DOTALL
        )
        
        self.jaxrs_annotation_pattern = re.compile(
            r'@(' + '|'.join(self.jaxrs_annotations.keys()) + r')\s*(?:\((.*?)\))?',
            re.DOTALL
        )
        
        self.struts_annotation_pattern = re.compile(
            r'@(' + '|'.join(self.struts_annotations.keys()) + r')\s*(?:\((.*?)\))?',
            re.DOTALL
        )
        
        # JAX-RS @Path annotation
        self.jaxrs_path_pattern = re.compile(r'@Path\s*\(\s*["\']([^"\']+)["\']\s*\)', re.DOTALL)
        
        # Struts namespace and action patterns
        self.struts_namespace_pattern = re.compile(r'@Namespace\s*\(\s*["\']([^"\']+)["\']\s*\)', re.DOTALL)
        self.struts_action_value_pattern = re.compile(r'value\s*=\s*["\']([^"\']+)["\']', re.DOTALL)
        
        # Servlet annotation pattern
        self.servlet_pattern = re.compile(r'@WebServlet\s*\([^)]*urlPatterns\s*=\s*[{"]([^}"\']+)["}][^)]*\)', re.DOTALL)
        
        # General class annotation patterns
        self.controller_patterns = [
            re.compile(r'@(RestController|Controller|RequestMapping)\s*(?:\((.*?)\))?', re.DOTALL),
            re.compile(r'@Path\s*\(\s*["\']([^"\']+)["\']\s*\)', re.DOTALL),
            re.compile(r'@Namespace\s*\(\s*["\']([^"\']+)["\']\s*\)', re.DOTALL),
            re.compile(r'@WebServlet', re.DOTALL)
        ]
        
        self.method_pattern = re.compile(
            r'(public|private|protected)?\s*[\w<>\[\],\s]*\s+(\w+)\s*\([^)]*\)\s*(?:throws[^{]*)?{',
            re.MULTILINE
        )
        
        # Path value extraction patterns
        self.path_pattern = re.compile(r'(?:value\s*=\s*|path\s*=\s*)?["\']([^"\']+)["\']')
        self.method_attr_pattern = re.compile(r'method\s*=\s*RequestMethod\.(\w+)')
        
    def _read_file_safely(self, file_path: Path) -> Optional[str]:
        """Safely read file content with multiple encoding attempts"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    logger.debug(f"Successfully read {file_path} with {encoding} encoding")
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error reading file {file_path} with {encoding}: {e}")
                continue
        
        # If all encodings fail, try binary read and decode with error handling
        try:
            with open(file_path, 'rb') as f:
                raw_content = f.read()
                # Try to decode with error handling
                content = raw_content.decode('utf-8', errors='replace')
                logger.warning(f"Read {file_path} with UTF-8 and replaced invalid characters")
                return content
        except Exception as e:
            logger.error(f"Failed to read file {file_path} with any encoding: {e}")
            return None
        
    def find_java_files(self, root_paths: List[str]) -> None:
        """Find all Java files in the given root paths"""
        for root_path in root_paths:
            root = Path(root_path)
            if not root.exists():
                logger.warning(f"Path does not exist: {root_path}")
                continue
            
            logger.info(f"Scanning directory: {root_path}")
            
            try:
                # Find Java files
                java_files = []
                for java_file in root.rglob("*.java"):
                    try:
                        # Quick check if file is readable
                        if java_file.is_file() and java_file.stat().st_size > 0:
                            java_files.append(java_file)
                    except (OSError, PermissionError) as e:
                        logger.warning(f"Cannot access file {java_file}: {e}")
                        continue
                
                self.java_files.extend(java_files)
                
                # Find configuration files (expanded for legacy apps)
                config_files = []
                config_patterns = [
                    "*.yml", "*.yaml", "*.properties", "*.xml",  # Standard config
                    "web.xml", "struts.xml", "struts-config.xml",  # Legacy config
                    "faces-config.xml", "persistence.xml",  # JEE config
                    "application.xml", "ejb-jar.xml"  # More JEE config
                ]
                
                for pattern in config_patterns:
                    for config_file in root.rglob(pattern):
                        try:
                            if config_file.is_file() and config_file.stat().st_size > 0:
                                config_files.append(config_file)
                        except (OSError, PermissionError) as e:
                            logger.warning(f"Cannot access config file {config_file}: {e}")
                            continue
                
                self.yaml_files.extend(config_files)
                logger.info(f"Found {len(java_files)} Java files and {len(config_files)} config files in {root_path}")
                
            except Exception as e:
                logger.error(f"Error scanning directory {root_path}: {e}")
                continue
        
        logger.info(f"Total: {len(self.java_files)} Java files and {len(self.yaml_files)} config files")
    
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
        content = self._read_file_safely(file_path)
        if content is None:
            return
        
    def is_web_component(self, content: str) -> bool:
        """Check if the file contains web components (controllers, servlets, etc.)"""
        web_indicators = [
            # Spring
            '@RestController', '@Controller', '@RequestMapping',
            '@GetMapping', '@PostMapping', '@PutMapping', '@DeleteMapping',
            # JAX-RS
            '@Path', '@GET', '@POST', '@PUT', '@DELETE', '@PATCH',
            # Struts
            '@Action', '@Actions', '@Namespace', '@Result',
            # Servlets
            '@WebServlet', 'extends HttpServlet',
            # JSF
            '@ManagedBean', '@Named', '@RequestScoped', '@SessionScoped',
            # Legacy patterns
            'implements Action', 'extends ActionSupport',
            'implements Controller', 'extends AbstractController'
        ]
        
        return any(indicator in content for indicator in web_indicators)
    def analyze_java_file(self, file_path: Path) -> None:
        """Analyze a single Java file for endpoints"""
        content = self._read_file_safely(file_path)
        if content is None:
            return
        
        # Check if this file contains web components
        if not self.is_web_component(content):
            return
            
        logger.debug(f"Analyzing web component: {file_path}")
        
        # Extract class name
        class_match = re.search(r'class\s+(\w+)', content)
        class_name = class_match.group(1) if class_match else "Unknown"
        
        # Try different framework patterns
        self._analyze_spring_endpoints(content, class_name, file_path)
        self._analyze_jaxrs_endpoints(content, class_name, file_path)
        self._analyze_struts_endpoints(content, class_name, file_path)
        self._analyze_servlet_endpoints(content, class_name, file_path)
        self._analyze_legacy_patterns(content, class_name, file_path)
    
    def _analyze_spring_endpoints(self, content: str, class_name: str, file_path: Path) -> None:
        """Analyze Spring Boot/MVC endpoints"""
        # Extract base path from class-level annotations
        base_path = self.extract_class_base_path(content)
        
        # Find all Spring mapping annotations
        for match in self.spring_annotation_pattern.finditer(content):
            annotation_name = match.group(1)
            annotation_content = match.group(2) or ""
            
            # Determine HTTP method
            if annotation_name in self.spring_mapping_annotations:
                http_method = self.spring_mapping_annotations[annotation_name]
            else:
                continue
                
            # Extract path and method from annotation
            path, method_override = self.extract_path_from_annotation(annotation_content)
            
            # Use method override if specified (for @RequestMapping)
            if method_override:
                http_method = method_override
            
            # Find the method this annotation belongs to
            method_name = self._find_method_name(content, match.end())
            if method_name:
                line_number = content[:match.start()].count('\n') + 1
                parameters = self._extract_method_parameters(content, match.end())
                
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
                logger.debug(f"Found Spring endpoint: {http_method} {endpoint.full_path}")
    
    def _analyze_jaxrs_endpoints(self, content: str, class_name: str, file_path: Path) -> None:
        """Analyze JAX-RS endpoints"""
        # Extract base path from @Path annotation on class
        base_path = ""
        class_path_match = self.jaxrs_path_pattern.search(content.split('class')[0] if 'class' in content else content)
        if class_path_match:
            base_path = class_path_match.group(1)
        
        # Find all JAX-RS HTTP method annotations
        for match in self.jaxrs_annotation_pattern.finditer(content):
            annotation_name = match.group(1)
            http_method = self.jaxrs_annotations.get(annotation_name, 'ANY')
            
            # Look for @Path annotation near this method
            method_start = match.end()
            method_section = content[method_start:method_start + 500]
            
            path = ""
            path_match = self.jaxrs_path_pattern.search(method_section)
            if path_match:
                path = path_match.group(1)
            
            method_name = self._find_method_name(content, method_start)
            if method_name:
                line_number = content[:match.start()].count('\n') + 1
                parameters = self._extract_jaxrs_parameters(content, match.end())
                
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
                logger.debug(f"Found JAX-RS endpoint: {http_method} {endpoint.full_path}")
    
    def _analyze_struts_endpoints(self, content: str, class_name: str, file_path: Path) -> None:
        """Analyze Struts 2 endpoints"""
        # Extract namespace from @Namespace annotation
        base_path = ""
        namespace_match = self.struts_namespace_pattern.search(content)
        if namespace_match:
            base_path = namespace_match.group(1)
        
        # Find @Action annotations
        for match in self.struts_annotation_pattern.finditer(content):
            annotation_name = match.group(1)
            annotation_content = match.group(2) or ""
            
            if annotation_name in ['Action', 'Actions']:
                # Extract action value
                action_match = self.struts_action_value_pattern.search(annotation_content)
                if action_match:
                    action_path = action_match.group(1)
                    
                    method_name = self._find_method_name(content, match.end())
                    if method_name:
                        line_number = content[:match.start()].count('\n') + 1
                        
                        endpoint = Endpoint(
                            path=action_path,
                            method='ANY',  # Struts actions can handle any HTTP method
                            controller_class=class_name,
                            method_name=method_name,
                            file_path=str(file_path),
                            line_number=line_number,
                            base_path=base_path,
                            parameters=[]
                        )
                        self.endpoints.append(endpoint)
                        logger.debug(f"Found Struts endpoint: {endpoint.full_path}")
    
    def _analyze_servlet_endpoints(self, content: str, class_name: str, file_path: Path) -> None:
        """Analyze Servlet endpoints"""
        # Find @WebServlet annotations
        for match in self.servlet_pattern.finditer(content):
            url_pattern = match.group(1)
            
            # Servlets typically handle multiple HTTP methods
            for method in ['GET', 'POST', 'PUT', 'DELETE']:
                method_name = f"do{method.capitalize()}"
                if method_name in content:
                    line_number = content[:match.start()].count('\n') + 1
                    
                    endpoint = Endpoint(
                        path=url_pattern,
                        method=method,
                        controller_class=class_name,
                        method_name=method_name,
                        file_path=str(file_path),
                        line_number=line_number,
                        base_path="",
                        parameters=[]
                    )
                    self.endpoints.append(endpoint)
                    logger.debug(f"Found Servlet endpoint: {method} {endpoint.full_path}")
    
    def _analyze_legacy_patterns(self, content: str, class_name: str, file_path: Path) -> None:
        """Analyze legacy framework patterns"""
        # Spring MVC legacy patterns
        if 'implements Controller' in content or 'extends AbstractController' in content:
            # Look for handleRequest method
            if 'handleRequest' in content:
                endpoint = Endpoint(
                    path=f"/{class_name.lower()}",  # Common convention
                    method='ANY',
                    controller_class=class_name,
                    method_name='handleRequest',
                    file_path=str(file_path),
                    line_number=1,  # Approximate
                    base_path="",
                    parameters=[]
                )
                self.endpoints.append(endpoint)
                logger.debug(f"Found legacy Controller endpoint: {endpoint.full_path}")
        
        # Struts 1 Action patterns
        if 'implements Action' in content or 'extends ActionSupport' in content:
            if 'execute' in content:
                endpoint = Endpoint(
                    path=f"/{class_name.replace('Action', '').lower()}",
                    method='ANY',
                    controller_class=class_name,
                    method_name='execute',
                    file_path=str(file_path),
                    line_number=1,
                    base_path="",
                    parameters=[]
                )
                self.endpoints.append(endpoint)
                logger.debug(f"Found Struts Action endpoint: {endpoint.full_path}")
    
    def _find_method_name(self, content: str, start_pos: int) -> Optional[str]:
        """Find the method name following an annotation"""
        method_search = content[start_pos:start_pos + 1000]
        method_match = self.method_pattern.search(method_search)
        return method_match.group(2) if method_match else None
    
    def _extract_method_parameters(self, content: str, start_pos: int) -> List[str]:
        """Extract method parameters from Spring annotations"""
        method_section = content[start_pos:start_pos + 1000]
        return self.extract_method_parameters(method_section)
    
    def _extract_jaxrs_parameters(self, content: str, start_pos: int) -> List[str]:
        """Extract JAX-RS parameters"""
        parameters = []
        method_section = content[start_pos:start_pos + 1000]
        
        # Look for @PathParam annotations
        path_param_pattern = re.compile(r'@PathParam\s*\(\s*["\']([^"\']+)["\']\s*\)')
        path_params = path_param_pattern.findall(method_section)
        parameters.extend(path_params)
        
        # Look for @QueryParam annotations
        query_param_pattern = re.compile(r'@QueryParam\s*\(\s*["\']([^"\']+)["\']\s*\)')
        query_params = query_param_pattern.findall(method_section)
        parameters.extend([f"{p}(query)" for p in query_params])
        
        return parameters
    
    def get_server_context_path(self) -> str:
        """Extract server context path from configuration files"""
        context_path = ""
        
        for config_file in self.yaml_files:
            content = self._read_file_safely(config_file)
            if content is None:
                continue
                
            try:
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
                logger.error(f"Error processing config file {config_file}: {e}")
                
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
