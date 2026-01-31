"""
Codebase Indexer - Automatic indexing of codebase for better AI context
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import ast
import re


@dataclass
class FileIndex:
    """Index entry for a single file"""
    path: str
    relative_path: str
    size: int
    hash: str
    language: str
    symbols: List[Dict[str, str]]  # functions, classes, variables
    imports: List[str]
    docstrings: List[str]
    last_modified: float
    lines_of_code: int


@dataclass
class CodebaseIndex:
    """Complete codebase index"""
    root_path: str
    total_files: int
    total_lines: int
    total_size: int
    languages: Dict[str, int]  # language -> file count
    files: Dict[str, FileIndex]  # relative_path -> FileIndex
    indexed_at: str
    index_version: str = "1.0.0"


class CodebaseIndexer:
    """Indexes codebase for better AI context"""
    
    # File extensions to index
    SUPPORTED_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.m': 'objective-c',
        '.sh': 'shell',
        '.bash': 'shell',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.xml': 'xml',
        '.md': 'markdown',
        '.txt': 'text',
    }
    
    # Directories to ignore
    IGNORE_DIRS = {
        '__pycache__', '.git', '.svn', '.hg', 'node_modules', 'venv', 'env',
        '.venv', '.env', 'dist', 'build', 'target', '.idea', '.vscode',
        '.pytest_cache', '.mypy_cache', '.tox', 'coverage', '.coverage',
        'htmlcov', '.eggs', '*.egg-info', '.gradle', 'bin', 'obj',
        'vendor', 'bower_components', '.next', '.nuxt', 'out', '.cache',
    }
    
    # Files to ignore
    IGNORE_FILES = {
        '.DS_Store', 'Thumbs.db', '.gitignore', '.dockerignore',
        'package-lock.json', 'yarn.lock', 'poetry.lock', 'Pipfile.lock',
    }
    
    def __init__(self, root_path: str, cache_dir: Optional[str] = None):
        """Initialize indexer
        
        Args:
            root_path: Root directory to index
            cache_dir: Directory to store index cache (default: ~/.cognautic/cache/index)
        """
        self.root_path = Path(root_path).resolve()
        
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / '.cognautic' / 'cache' / 'index'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / f"{self._get_path_hash()}.json"
    
    def _get_path_hash(self) -> str:
        """Get hash of root path for cache filename"""
        return hashlib.md5(str(self.root_path).encode()).hexdigest()[:16]
    
    def _should_ignore_dir(self, dir_name: str) -> bool:
        """Check if directory should be ignored"""
        return dir_name in self.IGNORE_DIRS or dir_name.startswith('.')
    
    def _should_ignore_file(self, file_name: str) -> bool:
        """Check if file should be ignored"""
        return file_name in self.IGNORE_FILES or file_name.startswith('.')
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _count_lines(self, content: str) -> int:
        """Count non-empty lines of code"""
        lines = content.split('\n')
        return sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
    
    def _extract_python_symbols(self, content: str, file_path: str) -> Tuple[List[Dict], List[str], List[str]]:
        """Extract symbols from Python file"""
        symbols = []
        imports = []
        docstrings = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Extract functions
                if isinstance(node, ast.FunctionDef):
                    symbols.append({
                        'type': 'function',
                        'name': node.name,
                        'line': node.lineno,
                        'args': [arg.arg for arg in node.args.args]
                    })
                    # Extract docstring
                    if ast.get_docstring(node):
                        docstrings.append(ast.get_docstring(node))
                
                # Extract classes
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    symbols.append({
                        'type': 'class',
                        'name': node.name,
                        'line': node.lineno,
                        'methods': methods
                    })
                    # Extract docstring
                    if ast.get_docstring(node):
                        docstrings.append(ast.get_docstring(node))
                
                # Extract imports
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # Extract module docstring
            module_docstring = ast.get_docstring(tree)
            if module_docstring:
                docstrings.append(module_docstring)
        
        except Exception as e:
            # If parsing fails, return empty lists
            pass
        
        return symbols, imports, docstrings
    
    def _extract_javascript_symbols(self, content: str) -> Tuple[List[Dict], List[str]]:
        """Extract symbols from JavaScript/TypeScript file using regex"""
        symbols = []
        imports = []
        
        # Extract function declarations
        func_pattern = r'(?:function|const|let|var)\s+(\w+)\s*(?:=\s*)?(?:async\s*)?\(([^)]*)\)'
        for match in re.finditer(func_pattern, content):
            symbols.append({
                'type': 'function',
                'name': match.group(1),
                'args': [arg.strip() for arg in match.group(2).split(',') if arg.strip()]
            })
        
        # Extract class declarations
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            symbols.append({
                'type': 'class',
                'name': match.group(1)
            })
        
        # Extract imports
        import_pattern = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(1))
        
        require_pattern = r'require\([\'"]([^\'"]+)[\'"]\)'
        for match in re.finditer(require_pattern, content):
            imports.append(match.group(1))
        
        return symbols, imports
    
    def _index_file(self, file_path: Path) -> Optional[FileIndex]:
        """Index a single file"""
        try:
            # Get file info
            stat = file_path.stat()
            relative_path = str(file_path.relative_to(self.root_path))
            extension = file_path.suffix.lower()
            language = self.SUPPORTED_EXTENSIONS.get(extension, 'unknown')
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Skip binary files
                return None
            
            # Extract symbols based on language
            symbols = []
            imports = []
            docstrings = []
            
            if language == 'python':
                symbols, imports, docstrings = self._extract_python_symbols(content, str(file_path))
            elif language in ('javascript', 'typescript'):
                symbols, imports = self._extract_javascript_symbols(content)
            
            # Create index entry
            return FileIndex(
                path=str(file_path),
                relative_path=relative_path,
                size=stat.st_size,
                hash=self._get_file_hash(file_path),
                language=language,
                symbols=symbols,
                imports=imports,
                docstrings=docstrings,
                last_modified=stat.st_mtime,
                lines_of_code=self._count_lines(content)
            )
        
        except Exception as e:
            return None
    
    def index(self, progress_callback=None) -> CodebaseIndex:
        """Index the codebase with progress tracking
        
        Args:
            progress_callback: Callback function(current, total, file_path) for progress updates
        
        Returns:
            CodebaseIndex object
        """
        # First pass: count total files
        total_files = 0
        files_to_index = []
        
        for root, dirs, files in os.walk(self.root_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
            
            for file in files:
                if self._should_ignore_file(file):
                    continue
                
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    files_to_index.append(file_path)
                    total_files += 1
        
        # Second pass: index files with progress
        indexed_files = {}
        total_lines = 0
        total_size = 0
        languages = {}
        
        for i, file_path in enumerate(files_to_index):
            # Report progress
            if progress_callback:
                progress_callback(i + 1, total_files, str(file_path.relative_to(self.root_path)))
            
            # Index file
            file_index = self._index_file(file_path)
            if file_index:
                indexed_files[file_index.relative_path] = file_index
                total_lines += file_index.lines_of_code
                total_size += file_index.size
                languages[file_index.language] = languages.get(file_index.language, 0) + 1
        
        # Create codebase index
        index = CodebaseIndex(
            root_path=str(self.root_path),
            total_files=len(indexed_files),
            total_lines=total_lines,
            total_size=total_size,
            languages=languages,
            files=indexed_files,
            indexed_at=datetime.now().isoformat()
        )
        
        return index
    
    def save_index(self, index: CodebaseIndex):
        """Save index to cache"""
        try:
            # Convert to dict
            index_dict = asdict(index)
            
            # Save to file
            with open(self.index_file, 'w') as f:
                json.dump(index_dict, f, indent=2)
        
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def load_index(self) -> Optional[CodebaseIndex]:
        """Load index from cache"""
        try:
            if not self.index_file.exists():
                return None
            
            with open(self.index_file, 'r') as f:
                data = json.load(f)
            
            # Convert file indices back to FileIndex objects
            files = {}
            for path, file_data in data['files'].items():
                files[path] = FileIndex(**file_data)
            
            data['files'] = files
            
            return CodebaseIndex(**data)
        
        except Exception as e:
            return None
    
    def needs_reindex(self) -> bool:
        """Check if codebase needs reindexing"""
        index = self.load_index()
        if not index:
            return True
        
        # Check if any files have been modified
        for file_index in index.files.values():
            file_path = Path(file_index.path)
            if not file_path.exists():
                return True
            
            stat = file_path.stat()
            if stat.st_mtime > file_index.last_modified:
                return True
        
        return False
    
    def search(self, query: str, index: Optional[CodebaseIndex] = None) -> List[Dict]:
        """Search index for query
        
        Args:
            query: Search query (symbol name, file name, etc.)
            index: CodebaseIndex to search (loads from cache if None)
        
        Returns:
            List of matching results
        """
        if index is None:
            index = self.load_index()
            if not index:
                return []
        
        results = []
        query_lower = query.lower()
        
        for file_index in index.files.values():
            # Search in file path
            if query_lower in file_index.relative_path.lower():
                results.append({
                    'type': 'file',
                    'path': file_index.relative_path,
                    'language': file_index.language,
                    'lines': file_index.lines_of_code
                })
            
            # Search in symbols
            for symbol in file_index.symbols:
                if query_lower in symbol['name'].lower():
                    results.append({
                        'type': 'symbol',
                        'symbol_type': symbol['type'],
                        'name': symbol['name'],
                        'file': file_index.relative_path,
                        'line': symbol.get('line', 0)
                    })
            
            # Search in imports
            for imp in file_index.imports:
                if query_lower in imp.lower():
                    results.append({
                        'type': 'import',
                        'name': imp,
                        'file': file_index.relative_path
                    })
        
        return results
    
    def get_stats(self, index: Optional[CodebaseIndex] = None) -> Dict:
        """Get codebase statistics
        
        Args:
            index: CodebaseIndex to analyze (loads from cache if None)
        
        Returns:
            Dictionary of statistics
        """
        if index is None:
            index = self.load_index()
            if not index:
                return {}
        
        return {
            'total_files': index.total_files,
            'total_lines': index.total_lines,
            'total_size': index.total_size,
            'languages': index.languages,
            'indexed_at': index.indexed_at,
            'root_path': index.root_path
        }
