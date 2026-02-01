"""
Code analysis tool for understanding code structure
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import json

from .base import BaseTool, ToolResult, PermissionLevel


class CodeAnalysisTool(BaseTool):
    """Tool for analyzing and understanding code structure"""
    
    def __init__(self):
        super().__init__(
            name="code_analysis",
            description="Analyze and understand code structure",
            permission_level=PermissionLevel.READ_ONLY
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "parse_ast",
            "analyze_dependencies",
            "find_functions",
            "find_classes",
            "get_code_metrics"
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "code_analysis",
                "description": "Analyze and understand code structure",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The operation to perform",
                            "enum": self.get_capabilities()
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to analyze"
                        },
                        "project_path": {
                            "type": "string",
                            "description": "Path to the project directory"
                        },
                        "function_name": {
                            "type": "string",
                            "description": "Name of the function to find"
                        },
                        "class_name": {
                            "type": "string",
                            "description": "Name of the class to find"
                        },
                        "include_methods": {
                            "type": "boolean",
                            "description": "Whether to include class methods in function search"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute code analysis operation"""
        
        operations = {
            'parse_ast': self._parse_ast,
            'analyze_dependencies': self._analyze_dependencies,
            'find_functions': self._find_functions,
            'find_classes': self._find_classes,
            'get_code_metrics': self._get_code_metrics
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation: {operation}"
            )
        
        try:
            result = await operations[operation](**kwargs)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _parse_ast(self, file_path: str) -> Dict[str, Any]:
        """Parse Python file and return AST information"""
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path.suffix != '.py':
            raise ValueError(f"File is not a Python file: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in Python file: {str(e)}")
        
        # Extract information from AST
        info = {
            'file_path': str(path),
            'imports': [],
            'functions': [],
            'classes': [],
            'variables': [],
            'docstring': ast.get_docstring(tree)
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    info['imports'].append({
                        'type': 'import',
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
            
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    info['imports'].append({
                        'type': 'from_import',
                        'module': node.module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
            
            elif isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node),
                    'decorators': [ast.unparse(dec) for dec in node.decorator_list],
                    'is_async': False
                }
                info['functions'].append(func_info)
            
            elif isinstance(node, ast.AsyncFunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node),
                    'decorators': [ast.unparse(dec) for dec in node.decorator_list],
                    'is_async': True
                }
                info['functions'].append(func_info)
            
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'bases': [ast.unparse(base) for base in node.bases],
                    'docstring': ast.get_docstring(node),
                    'decorators': [ast.unparse(dec) for dec in node.decorator_list],
                    'methods': []
                }
                
                # Find methods in the class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_info = {
                            'name': item.name,
                            'line': item.lineno,
                            'args': [arg.arg for arg in item.args.args],
                            'is_async': isinstance(item, ast.AsyncFunctionDef)
                        }
                        class_info['methods'].append(method_info)
                
                info['classes'].append(class_info)
            
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        info['variables'].append({
                            'name': target.id,
                            'line': node.lineno,
                            'type': 'assignment'
                        })
        
        return info
    
    async def _analyze_dependencies(self, project_path: str) -> Dict[str, Any]:
        """Analyze project dependencies"""
        
        path = Path(project_path)
        if not path.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")
        
        dependencies = {
            'project_path': str(path),
            'requirements_files': [],
            'package_files': [],
            'imports': set(),
            'external_packages': set(),
            'internal_modules': set()
        }
        
        # Find requirements files
        req_files = ['requirements.txt', 'requirements-dev.txt', 'Pipfile', 'pyproject.toml', 'setup.py']
        for req_file in req_files:
            req_path = path / req_file
            if req_path.exists():
                dependencies['requirements_files'].append(str(req_path))
        
        # Find package files
        for package_file in path.rglob('*.py'):
            if not any(part.startswith('.') for part in package_file.parts):
                dependencies['package_files'].append(str(package_file))
                
                # Analyze imports in each file
                try:
                    ast_info = await self._parse_ast(str(package_file))
                    for imp in ast_info['imports']:
                        if imp['type'] == 'import':
                            dependencies['imports'].add(imp['name'])
                        elif imp['type'] == 'from_import' and imp['module']:
                            dependencies['imports'].add(imp['module'])
                except Exception:
                    continue
        
        # Categorize imports
        stdlib_modules = self._get_stdlib_modules()
        
        for imp in dependencies['imports']:
            root_module = imp.split('.')[0]
            if root_module in stdlib_modules:
                continue  # Skip standard library
            elif any(root_module in str(f) for f in dependencies['package_files']):
                dependencies['internal_modules'].add(imp)
            else:
                dependencies['external_packages'].add(imp)
        
        # Convert sets to lists for JSON serialization
        dependencies['imports'] = list(dependencies['imports'])
        dependencies['external_packages'] = list(dependencies['external_packages'])
        dependencies['internal_modules'] = list(dependencies['internal_modules'])
        
        return dependencies
    
    async def _find_functions(
        self,
        project_path: str,
        function_name: str = None,
        include_methods: bool = True
    ) -> List[Dict[str, Any]]:
        """Find functions in a project"""
        
        path = Path(project_path)
        if not path.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")
        
        functions = []
        
        for py_file in path.rglob('*.py'):
            if any(part.startswith('.') for part in py_file.parts):
                continue
            
            try:
                ast_info = await self._parse_ast(str(py_file))
                
                # Add standalone functions
                for func in ast_info['functions']:
                    if not function_name or function_name.lower() in func['name'].lower():
                        func['file'] = str(py_file)
                        func['type'] = 'function'
                        functions.append(func)
                
                # Add class methods if requested
                if include_methods:
                    for cls in ast_info['classes']:
                        for method in cls['methods']:
                            if not function_name or function_name.lower() in method['name'].lower():
                                method['file'] = str(py_file)
                                method['class'] = cls['name']
                                method['type'] = 'method'
                                functions.append(method)
                
            except Exception:
                continue
        
        return functions
    
    async def _find_classes(
        self,
        project_path: str,
        class_name: str = None
    ) -> List[Dict[str, Any]]:
        """Find classes in a project"""
        
        path = Path(project_path)
        if not path.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")
        
        classes = []
        
        for py_file in path.rglob('*.py'):
            if any(part.startswith('.') for part in py_file.parts):
                continue
            
            try:
                ast_info = await self._parse_ast(str(py_file))
                
                for cls in ast_info['classes']:
                    if not class_name or class_name.lower() in cls['name'].lower():
                        cls['file'] = str(py_file)
                        classes.append(cls)
                
            except Exception:
                continue
        
        return classes
    
    async def _get_code_metrics(self, project_path: str) -> Dict[str, Any]:
        """Get code metrics for a project"""
        
        path = Path(project_path)
        if not path.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")
        
        metrics = {
            'project_path': str(path),
            'total_files': 0,
            'python_files': 0,
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'functions': 0,
            'classes': 0,
            'imports': 0,
            'files_by_extension': {},
            'largest_files': []
        }
        
        file_sizes = []
        
        for file_path in path.rglob('*'):
            if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
                metrics['total_files'] += 1
                
                # Count by extension
                ext = file_path.suffix.lower()
                metrics['files_by_extension'][ext] = metrics['files_by_extension'].get(ext, 0) + 1
                
                # Analyze Python files
                if ext == '.py':
                    metrics['python_files'] += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        file_lines = len(lines)
                        file_code_lines = 0
                        file_comment_lines = 0
                        file_blank_lines = 0
                        
                        for line in lines:
                            stripped = line.strip()
                            if not stripped:
                                file_blank_lines += 1
                            elif stripped.startswith('#'):
                                file_comment_lines += 1
                            else:
                                file_code_lines += 1
                        
                        metrics['total_lines'] += file_lines
                        metrics['code_lines'] += file_code_lines
                        metrics['comment_lines'] += file_comment_lines
                        metrics['blank_lines'] += file_blank_lines
                        
                        file_sizes.append({
                            'file': str(file_path),
                            'lines': file_lines,
                            'code_lines': file_code_lines
                        })
                        
                        # Count functions and classes
                        try:
                            ast_info = await self._parse_ast(str(file_path))
                            metrics['functions'] += len(ast_info['functions'])
                            metrics['classes'] += len(ast_info['classes'])
                            metrics['imports'] += len(ast_info['imports'])
                        except Exception:
                            pass
                            
                    except Exception:
                        continue
        
        # Get largest files
        file_sizes.sort(key=lambda x: x['lines'], reverse=True)
        metrics['largest_files'] = file_sizes[:10]
        
        return metrics
    
    def _get_stdlib_modules(self) -> set:
        """Get set of Python standard library modules"""
        # This is a simplified list of common stdlib modules
        # In a full implementation, you might want to use a more comprehensive approach
        return {
            'os', 'sys', 'json', 'datetime', 'time', 'random', 'math', 'collections',
            'itertools', 'functools', 'operator', 're', 'string', 'io', 'pathlib',
            'urllib', 'http', 'email', 'html', 'xml', 'csv', 'sqlite3', 'pickle',
            'hashlib', 'hmac', 'secrets', 'uuid', 'base64', 'binascii', 'struct',
            'codecs', 'unicodedata', 'stringprep', 'readline', 'rlcompleter',
            'subprocess', 'threading', 'multiprocessing', 'concurrent', 'queue',
            'sched', 'asyncio', 'socket', 'ssl', 'select', 'selectors', 'signal',
            'mmap', 'ctypes', 'array', 'weakref', 'types', 'copy', 'pprint',
            'reprlib', 'enum', 'numbers', 'cmath', 'decimal', 'fractions',
            'statistics', 'logging', 'getopt', 'argparse', 'fileinput', 'filecmp',
            'tempfile', 'glob', 'fnmatch', 'linecache', 'shutil', 'macpath'
        }
