"""
Code navigation tool for smart code analysis - jump to definition, find references, symbol search
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import tokenize
import io

from .base import BaseTool, ToolResult, PermissionLevel


class CodeNavigationTool(BaseTool):
    """Tool for intelligent code navigation and symbol analysis"""
    
    def __init__(self):
        super().__init__(
            name="code_navigation",
            description="Navigate code: jump to definition, find references, search symbols",
            permission_level=PermissionLevel.READ_ONLY
        )
        self.supported_languages = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php'
        }
    
    def get_capabilities(self) -> List[str]:
        return [
            "jump_to_definition",
            "find_references",
            "search_symbols",
            "list_symbols",
            "find_implementations",
            "get_symbol_info"
        ]
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute code navigation operation"""
        
        operations = {
            'jump_to_definition': self._jump_to_definition,
            'find_references': self._find_references,
            'search_symbols': self._search_symbols,
            'list_symbols': self._list_symbols,
            'find_implementations': self._find_implementations,
            'get_symbol_info': self._get_symbol_info
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
    
    async def _jump_to_definition(
        self, 
        symbol: str, 
        file_path: str = None,
        line_number: int = None,
        workspace: str = None
    ) -> Dict[str, Any]:
        """Jump to the definition of a symbol"""
        workspace_path = Path(workspace) if workspace else Path.cwd()
        
        if not workspace_path.exists():
            raise FileNotFoundError(f"Workspace not found: {workspace_path}")
        
        # If file_path is provided, start search there
        if file_path:
            file_path = workspace_path / file_path
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
        
        definitions = []
        
        # Search for definitions in Python files
        for py_file in workspace_path.rglob('*.py'):
            if self._should_skip_file(py_file):
                continue
            
            try:
                defs = self._find_python_definitions(py_file, symbol)
                definitions.extend(defs)
            except Exception:
                continue
        
        # Search in JavaScript/TypeScript files
        for js_file in list(workspace_path.rglob('*.js')) + list(workspace_path.rglob('*.ts')):
            if self._should_skip_file(js_file):
                continue
            
            try:
                defs = self._find_js_definitions(js_file, symbol)
                definitions.extend(defs)
            except Exception:
                continue
        
        return {
            'symbol': symbol,
            'definitions': definitions,
            'count': len(definitions)
        }
    
    async def _find_references(
        self, 
        symbol: str, 
        workspace: str = None,
        include_definitions: bool = True
    ) -> Dict[str, Any]:
        """Find all references to a symbol"""
        workspace_path = Path(workspace) if workspace else Path.cwd()
        
        if not workspace_path.exists():
            raise FileNotFoundError(f"Workspace not found: {workspace_path}")
        
        references = []
        
        # Search in all supported file types
        for ext in self.supported_languages.keys():
            for file_path in workspace_path.rglob(f'*{ext}'):
                if self._should_skip_file(file_path):
                    continue
                
                try:
                    refs = self._find_symbol_in_file(file_path, symbol)
                    references.extend(refs)
                except Exception:
                    continue
        
        return {
            'symbol': symbol,
            'references': references,
            'count': len(references),
            'files': len(set(ref['file'] for ref in references))
        }
    
    async def _search_symbols(
        self, 
        query: str, 
        workspace: str = None,
        symbol_type: str = None,
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """Search for symbols matching a query"""
        workspace_path = Path(workspace) if workspace else Path.cwd()
        
        if not workspace_path.exists():
            raise FileNotFoundError(f"Workspace not found: {workspace_path}")
        
        results = []
        
        # Search in Python files
        for py_file in workspace_path.rglob('*.py'):
            if self._should_skip_file(py_file):
                continue
            
            try:
                symbols = self._extract_python_symbols(py_file)
                for symbol in symbols:
                    if self._matches_query(symbol['name'], query, case_sensitive):
                        if symbol_type is None or symbol['type'] == symbol_type:
                            results.append(symbol)
            except Exception:
                continue
        
        # Search in JavaScript/TypeScript files
        for js_file in list(workspace_path.rglob('*.js')) + list(workspace_path.rglob('*.ts')):
            if self._should_skip_file(js_file):
                continue
            
            try:
                symbols = self._extract_js_symbols(js_file)
                for symbol in symbols:
                    if self._matches_query(symbol['name'], query, case_sensitive):
                        if symbol_type is None or symbol['type'] == symbol_type:
                            results.append(symbol)
            except Exception:
                continue
        
        return {
            'query': query,
            'results': results,
            'count': len(results)
        }
    
    async def _list_symbols(
        self, 
        file_path: str,
        workspace: str = None,
        symbol_type: str = None
    ) -> Dict[str, Any]:
        """List all symbols in a file"""
        workspace_path = Path(workspace) if workspace else Path.cwd()
        target_file = workspace_path / file_path
        
        if not target_file.exists():
            raise FileNotFoundError(f"File not found: {target_file}")
        
        if not target_file.is_file():
            raise ValueError(f"Path is not a file: {target_file}")
        
        ext = target_file.suffix.lower()
        
        if ext == '.py':
            symbols = self._extract_python_symbols(target_file)
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            symbols = self._extract_js_symbols(target_file)
        else:
            # Generic symbol extraction for other languages
            symbols = self._extract_generic_symbols(target_file)
        
        if symbol_type:
            symbols = [s for s in symbols if s['type'] == symbol_type]
        
        return {
            'file': str(target_file.relative_to(workspace_path)),
            'symbols': symbols,
            'count': len(symbols)
        }
    
    async def _find_implementations(
        self, 
        interface_or_class: str,
        workspace: str = None
    ) -> Dict[str, Any]:
        """Find implementations of an interface or subclasses of a class"""
        workspace_path = Path(workspace) if workspace else Path.cwd()
        
        if not workspace_path.exists():
            raise FileNotFoundError(f"Workspace not found: {workspace_path}")
        
        implementations = []
        
        # Search in Python files for class inheritance
        for py_file in workspace_path.rglob('*.py'):
            if self._should_skip_file(py_file):
                continue
            
            try:
                impls = self._find_python_implementations(py_file, interface_or_class)
                implementations.extend(impls)
            except Exception:
                continue
        
        return {
            'interface_or_class': interface_or_class,
            'implementations': implementations,
            'count': len(implementations)
        }
    
    async def _get_symbol_info(
        self, 
        symbol: str,
        file_path: str,
        line_number: int = None,
        workspace: str = None
    ) -> Dict[str, Any]:
        """Get detailed information about a symbol"""
        workspace_path = Path(workspace) if workspace else Path.cwd()
        target_file = workspace_path / file_path
        
        if not target_file.exists():
            raise FileNotFoundError(f"File not found: {target_file}")
        
        ext = target_file.suffix.lower()
        
        if ext == '.py':
            info = self._get_python_symbol_info(target_file, symbol, line_number)
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            info = self._get_js_symbol_info(target_file, symbol, line_number)
        else:
            info = {'symbol': symbol, 'type': 'unknown', 'details': 'Language not fully supported'}
        
        return info
    
    # Helper methods
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during search"""
        skip_dirs = {
            '__pycache__', '.git', 'node_modules', '.venv', 'venv',
            'dist', 'build', '.pytest_cache', '.mypy_cache', 'coverage'
        }
        
        return any(skip_dir in file_path.parts for skip_dir in skip_dirs)
    
    def _matches_query(self, text: str, query: str, case_sensitive: bool) -> bool:
        """Check if text matches query"""
        if not case_sensitive:
            text = text.lower()
            query = query.lower()
        
        return query in text
    
    def _find_python_definitions(self, file_path: Path, symbol: str) -> List[Dict[str, Any]]:
        """Find Python symbol definitions in a file"""
        definitions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == symbol:
                    definitions.append({
                        'file': str(file_path),
                        'line': node.lineno,
                        'column': node.col_offset,
                        'type': 'function',
                        'name': node.name,
                        'context': self._get_context_lines(file_path, node.lineno)
                    })
                elif isinstance(node, ast.ClassDef) and node.name == symbol:
                    definitions.append({
                        'file': str(file_path),
                        'line': node.lineno,
                        'column': node.col_offset,
                        'type': 'class',
                        'name': node.name,
                        'context': self._get_context_lines(file_path, node.lineno)
                    })
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == symbol:
                            definitions.append({
                                'file': str(file_path),
                                'line': node.lineno,
                                'column': node.col_offset,
                                'type': 'variable',
                                'name': symbol,
                                'context': self._get_context_lines(file_path, node.lineno)
                            })
        except Exception:
            pass
        
        return definitions
    
    def _find_js_definitions(self, file_path: Path, symbol: str) -> List[Dict[str, Any]]:
        """Find JavaScript/TypeScript symbol definitions in a file"""
        definitions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Simple regex-based detection for JS/TS
            patterns = [
                (r'^\s*function\s+' + re.escape(symbol) + r'\s*\(', 'function'),
                (r'^\s*const\s+' + re.escape(symbol) + r'\s*=', 'const'),
                (r'^\s*let\s+' + re.escape(symbol) + r'\s*=', 'variable'),
                (r'^\s*var\s+' + re.escape(symbol) + r'\s*=', 'variable'),
                (r'^\s*class\s+' + re.escape(symbol) + r'\s*[{(]', 'class'),
                (r'^\s*interface\s+' + re.escape(symbol) + r'\s*[{]', 'interface'),
                (r'^\s*type\s+' + re.escape(symbol) + r'\s*=', 'type'),
            ]
            
            for line_num, line in enumerate(lines, 1):
                for pattern, symbol_type in patterns:
                    if re.search(pattern, line):
                        definitions.append({
                            'file': str(file_path),
                            'line': line_num,
                            'type': symbol_type,
                            'name': symbol,
                            'context': self._get_context_lines(file_path, line_num)
                        })
        except Exception:
            pass
        
        return definitions
    
    def _find_symbol_in_file(self, file_path: Path, symbol: str) -> List[Dict[str, Any]]:
        """Find all occurrences of a symbol in a file"""
        references = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Use word boundary regex to find exact symbol matches
            pattern = r'\b' + re.escape(symbol) + r'\b'
            
            for line_num, line in enumerate(lines, 1):
                matches = list(re.finditer(pattern, line))
                for match in matches:
                    references.append({
                        'file': str(file_path),
                        'line': line_num,
                        'column': match.start(),
                        'text': line.strip(),
                        'context': self._get_context_lines(file_path, line_num, context_size=2)
                    })
        except Exception:
            pass
        
        return references
    
    def _extract_python_symbols(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract all symbols from a Python file"""
        symbols = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    symbols.append({
                        'name': node.name,
                        'type': 'function',
                        'line': node.lineno,
                        'file': str(file_path),
                        'signature': self._get_function_signature(node)
                    })
                elif isinstance(node, ast.ClassDef):
                    symbols.append({
                        'name': node.name,
                        'type': 'class',
                        'line': node.lineno,
                        'file': str(file_path),
                        'bases': [self._get_name(base) for base in node.bases]
                    })
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            symbols.append({
                                'name': target.id,
                                'type': 'variable',
                                'line': node.lineno,
                                'file': str(file_path)
                            })
        except Exception:
            pass
        
        return symbols
    
    def _extract_js_symbols(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract all symbols from a JavaScript/TypeScript file"""
        symbols = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            patterns = [
                (r'^\s*function\s+(\w+)\s*\(', 'function'),
                (r'^\s*const\s+(\w+)\s*=', 'const'),
                (r'^\s*let\s+(\w+)\s*=', 'variable'),
                (r'^\s*var\s+(\w+)\s*=', 'variable'),
                (r'^\s*class\s+(\w+)\s*[{(]', 'class'),
                (r'^\s*interface\s+(\w+)\s*[{]', 'interface'),
                (r'^\s*type\s+(\w+)\s*=', 'type'),
                (r'^\s*export\s+(?:const|let|var)\s+(\w+)', 'export'),
                (r'^\s*export\s+function\s+(\w+)', 'export_function'),
                (r'^\s*export\s+class\s+(\w+)', 'export_class'),
            ]
            
            for line_num, line in enumerate(lines, 1):
                for pattern, symbol_type in patterns:
                    match = re.search(pattern, line)
                    if match:
                        symbols.append({
                            'name': match.group(1),
                            'type': symbol_type,
                            'line': line_num,
                            'file': str(file_path)
                        })
        except Exception:
            pass
        
        return symbols
    
    def _extract_generic_symbols(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract symbols from files using generic patterns"""
        symbols = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Generic patterns for common symbol definitions
            patterns = [
                (r'^\s*def\s+(\w+)', 'function'),
                (r'^\s*class\s+(\w+)', 'class'),
                (r'^\s*func\s+(\w+)', 'function'),  # Go
                (r'^\s*fn\s+(\w+)', 'function'),    # Rust
                (r'^\s*public\s+(?:static\s+)?(?:void|int|String|boolean)\s+(\w+)', 'method'),  # Java
            ]
            
            for line_num, line in enumerate(lines, 1):
                for pattern, symbol_type in patterns:
                    match = re.search(pattern, line)
                    if match:
                        symbols.append({
                            'name': match.group(1),
                            'type': symbol_type,
                            'line': line_num,
                            'file': str(file_path)
                        })
        except Exception:
            pass
        
        return symbols
    
    def _find_python_implementations(self, file_path: Path, base_class: str) -> List[Dict[str, Any]]:
        """Find Python classes that inherit from a base class"""
        implementations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        base_name = self._get_name(base)
                        if base_name == base_class:
                            implementations.append({
                                'file': str(file_path),
                                'line': node.lineno,
                                'class': node.name,
                                'base': base_class,
                                'context': self._get_context_lines(file_path, node.lineno)
                            })
        except Exception:
            pass
        
        return implementations
    
    def _get_python_symbol_info(
        self, 
        file_path: Path, 
        symbol: str, 
        line_number: int = None
    ) -> Dict[str, Any]:
        """Get detailed information about a Python symbol"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == symbol:
                    return {
                        'symbol': symbol,
                        'type': 'function',
                        'line': node.lineno,
                        'signature': self._get_function_signature(node),
                        'docstring': ast.get_docstring(node),
                        'decorators': [self._get_name(d) for d in node.decorator_list],
                        'arguments': [arg.arg for arg in node.args.args]
                    }
                elif isinstance(node, ast.ClassDef) and node.name == symbol:
                    return {
                        'symbol': symbol,
                        'type': 'class',
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'bases': [self._get_name(base) for base in node.bases],
                        'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    }
        except Exception:
            pass
        
        return {'symbol': symbol, 'type': 'unknown'}
    
    def _get_js_symbol_info(
        self, 
        file_path: Path, 
        symbol: str, 
        line_number: int = None
    ) -> Dict[str, Any]:
        """Get detailed information about a JavaScript/TypeScript symbol"""
        # Basic implementation - could be enhanced with proper JS parser
        return {
            'symbol': symbol,
            'type': 'unknown',
            'file': str(file_path),
            'note': 'Full JS/TS parsing requires additional parser library'
        }
    
    def _get_context_lines(
        self, 
        file_path: Path, 
        line_number: int, 
        context_size: int = 3
    ) -> List[str]:
        """Get context lines around a specific line"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start = max(0, line_number - context_size - 1)
            end = min(len(lines), line_number + context_size)
            
            return [line.rstrip() for line in lines[start:end]]
        except Exception:
            return []
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Get function signature from AST node"""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        
        return f"{node.name}({', '.join(args)})"
    
    def _get_name(self, node) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "code_navigation",
                "description": "Navigate code: jump to definition, find references, search symbols, and analyze structure. Use 'code_analysis' for deep analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The operation to perform",
                            "enum": ["jump_to_definition", "find_references", "search_symbols", "list_symbols", "find_implementations", "get_symbol_info"]
                        },
                        "symbol": {
                            "type": "string",
                            "description": "The symbol to navigate (required for jump_to_definition, find_references, get_symbol_info)"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query for symbol search (required for search_symbols)"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to analyze (required for list_symbols, get_symbol_info)"
                        },
                        "workspace": {
                            "type": "string",
                            "description": "Base directory for operation (optional, defaults to current directory)"
                        },
                        "symbol_type": {
                            "type": "string",
                            "description": "Filter by symbol type (class, function, variable, etc.)"
                        },
                        "interface_or_class": {
                            "type": "string",
                            "description": "Interface or class name to find implementations for"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
