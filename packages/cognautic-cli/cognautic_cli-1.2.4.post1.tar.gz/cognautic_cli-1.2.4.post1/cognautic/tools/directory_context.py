"""
Directory context tool for providing AI with current directory information
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import mimetypes

from .base import BaseTool, ToolResult, PermissionLevel


class DirectoryContextTool(BaseTool):
    """Tool for providing AI with directory context and structure information"""
    
    def __init__(self):
        super().__init__(
            name="directory_context",
            description="Get information about current directory structure and contents",
            permission_level=PermissionLevel.READ_ONLY
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "get_current_directory",
            "list_directory_tree",
            "get_directory_summary",
            "get_file_types",
            "get_project_structure"
        ]
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute directory context operation"""
        
        operations = {
            'get_current_directory': self._get_current_directory,
            'list_directory_tree': self._list_directory_tree,
            'get_directory_summary': self._get_directory_summary,
            'get_file_types': self._get_file_types,
            'get_project_structure': self._get_project_structure
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
    
    async def _get_current_directory(self, path: str = None) -> Dict[str, Any]:
        """Get current directory information"""
        target_path = Path(path) if path else Path.cwd()
        
        if not target_path.exists():
            raise FileNotFoundError(f"Directory not found: {target_path}")
        
        if not target_path.is_dir():
            raise ValueError(f"Path is not a directory: {target_path}")
        
        # Get directory contents
        contents = []
        try:
            for item in sorted(target_path.iterdir()):
                try:
                    stat = item.stat()
                    contents.append({
                        'name': item.name,
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': stat.st_size if item.is_file() else None,
                        'modified': stat.st_mtime,
                        'is_hidden': item.name.startswith('.')
                    })
                except (PermissionError, OSError):
                    # Skip items we can't access
                    continue
        except PermissionError:
            raise PermissionError(f"Permission denied accessing: {target_path}")
        
        return {
            'path': str(target_path.absolute()),
            'name': target_path.name,
            'contents': contents,
            'total_items': len(contents),
            'files': len([c for c in contents if c['type'] == 'file']),
            'directories': len([c for c in contents if c['type'] == 'directory'])
        }
    
    async def _list_directory_tree(
        self, 
        path: str = None, 
        max_depth: int = 3,
        include_hidden: bool = False,
        exclude_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """List directory tree structure"""
        target_path = Path(path) if path else Path.cwd()
        
        if not target_path.exists():
            raise FileNotFoundError(f"Directory not found: {target_path}")
        
        if not target_path.is_dir():
            raise ValueError(f"Path is not a directory: {target_path}")
        
        exclude_patterns = exclude_patterns or [
            '__pycache__', '.git', 'node_modules', '.venv', 'venv',
            '.pytest_cache', '.mypy_cache', 'dist', 'build', '.egg-info'
        ]
        
        def should_exclude(item_path: Path) -> bool:
            """Check if path should be excluded"""
            if not include_hidden and item_path.name.startswith('.'):
                return True
            return any(pattern in str(item_path) for pattern in exclude_patterns)
        
        def build_tree(current_path: Path, depth: int = 0) -> Dict[str, Any]:
            """Recursively build directory tree"""
            if depth >= max_depth:
                return None
            
            tree = {
                'name': current_path.name,
                'path': str(current_path.relative_to(target_path)),
                'type': 'directory',
                'children': []
            }
            
            try:
                items = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                for item in items:
                    if should_exclude(item):
                        continue
                    
                    if item.is_dir():
                        subtree = build_tree(item, depth + 1)
                        if subtree:
                            tree['children'].append(subtree)
                    else:
                        tree['children'].append({
                            'name': item.name,
                            'path': str(item.relative_to(target_path)),
                            'type': 'file',
                            'size': item.stat().st_size
                        })
            except PermissionError:
                tree['error'] = 'Permission denied'
            
            return tree
        
        tree = build_tree(target_path)
        
        return {
            'root': str(target_path.absolute()),
            'tree': tree,
            'max_depth': max_depth
        }
    
    async def _get_directory_summary(self, path: str = None) -> Dict[str, Any]:
        """Get comprehensive directory summary"""
        target_path = Path(path) if path else Path.cwd()
        
        if not target_path.exists():
            raise FileNotFoundError(f"Directory not found: {target_path}")
        
        if not target_path.is_dir():
            raise ValueError(f"Path is not a directory: {target_path}")
        
        # Collect statistics
        stats = {
            'total_files': 0,
            'total_directories': 0,
            'total_size': 0,
            'file_types': {},
            'largest_files': [],
            'recent_files': []
        }
        
        all_files = []
        
        def scan_directory(current_path: Path, depth: int = 0):
            """Recursively scan directory"""
            if depth > 5:  # Limit depth to prevent excessive scanning
                return
            
            try:
                for item in current_path.iterdir():
                    # Skip common excluded directories
                    if item.name in ['__pycache__', '.git', 'node_modules', '.venv', 'venv']:
                        continue
                    
                    if item.is_dir():
                        stats['total_directories'] += 1
                        scan_directory(item, depth + 1)
                    elif item.is_file():
                        try:
                            stat = item.stat()
                            stats['total_files'] += 1
                            stats['total_size'] += stat.st_size
                            
                            # Track file type
                            ext = item.suffix.lower() or 'no_extension'
                            stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                            
                            all_files.append({
                                'path': str(item.relative_to(target_path)),
                                'size': stat.st_size,
                                'modified': stat.st_mtime
                            })
                        except (PermissionError, OSError):
                            continue
            except PermissionError:
                pass
        
        scan_directory(target_path)
        
        # Get largest files (top 10)
        all_files.sort(key=lambda x: x['size'], reverse=True)
        stats['largest_files'] = all_files[:10]
        
        # Get most recent files (top 10)
        all_files.sort(key=lambda x: x['modified'], reverse=True)
        stats['recent_files'] = all_files[:10]
        
        return {
            'path': str(target_path.absolute()),
            'summary': stats
        }
    
    async def _get_file_types(self, path: str = None) -> Dict[str, Any]:
        """Get breakdown of file types in directory"""
        target_path = Path(path) if path else Path.cwd()
        
        if not target_path.exists():
            raise FileNotFoundError(f"Directory not found: {target_path}")
        
        if not target_path.is_dir():
            raise ValueError(f"Path is not a directory: {target_path}")
        
        file_types = {}
        
        def scan_for_types(current_path: Path, depth: int = 0):
            """Recursively scan for file types"""
            if depth > 5:
                return
            
            try:
                for item in current_path.iterdir():
                    if item.name in ['__pycache__', '.git', 'node_modules', '.venv', 'venv']:
                        continue
                    
                    if item.is_dir():
                        scan_for_types(item, depth + 1)
                    elif item.is_file():
                        ext = item.suffix.lower() or 'no_extension'
                        if ext not in file_types:
                            file_types[ext] = {
                                'count': 0,
                                'total_size': 0,
                                'files': []
                            }
                        
                        try:
                            size = item.stat().st_size
                            file_types[ext]['count'] += 1
                            file_types[ext]['total_size'] += size
                            file_types[ext]['files'].append(str(item.relative_to(target_path)))
                        except (PermissionError, OSError):
                            continue
            except PermissionError:
                pass
        
        scan_for_types(target_path)
        
        return {
            'path': str(target_path.absolute()),
            'file_types': file_types
        }
    
    async def _get_project_structure(self, path: str = None) -> Dict[str, Any]:
        """Get intelligent project structure analysis"""
        target_path = Path(path) if path else Path.cwd()
        
        if not target_path.exists():
            raise FileNotFoundError(f"Directory not found: {target_path}")
        
        if not target_path.is_dir():
            raise ValueError(f"Path is not a directory: {target_path}")
        
        # Detect project type
        project_indicators = {
            'python': ['setup.py', 'pyproject.toml', 'requirements.txt', 'Pipfile'],
            'node': ['package.json', 'node_modules'],
            'rust': ['Cargo.toml', 'Cargo.lock'],
            'go': ['go.mod', 'go.sum'],
            'java': ['pom.xml', 'build.gradle'],
            'ruby': ['Gemfile', 'Rakefile'],
            'php': ['composer.json'],
            'c/c++': ['CMakeLists.txt', 'Makefile'],
            'web': ['index.html', 'index.htm']
        }
        
        detected_types = []
        key_files = []
        
        try:
            items = list(target_path.iterdir())
            item_names = [item.name for item in items]
            
            for project_type, indicators in project_indicators.items():
                if any(indicator in item_names for indicator in indicators):
                    detected_types.append(project_type)
            
            # Identify key files
            important_files = [
                'README.md', 'README.rst', 'README.txt',
                'LICENSE', 'LICENSE.txt', 'LICENSE.md',
                '.gitignore', '.dockerignore',
                'Dockerfile', 'docker-compose.yml',
                'Makefile', 'CMakeLists.txt'
            ]
            
            for item in items:
                if item.name in important_files and item.is_file():
                    key_files.append(item.name)
        except PermissionError:
            pass
        
        return {
            'path': str(target_path.absolute()),
            'project_name': target_path.name,
            'detected_types': detected_types,
            'key_files': key_files,
            'is_git_repo': (target_path / '.git').exists(),
            'has_tests': any((target_path / name).exists() for name in ['tests', 'test', '__tests__']),
            'has_docs': any((target_path / name).exists() for name in ['docs', 'documentation', 'doc'])
        }

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "directory_context",
                "description": "Get information about current directory structure and contents. Provides tree views, summaries, and project analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The operation to perform",
                            "enum": ["get_current_directory", "list_directory_tree", "get_directory_summary", "get_file_types", "get_project_structure"]
                        },
                        "path": {
                            "type": "string",
                            "description": "Path to the directory (optional, defaults to current directory)"
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "Maximum depth for tree view (optional, default 3)"
                        },
                        "include_hidden": {
                            "type": "boolean",
                            "description": "Whether to include hidden files (optional, default false)"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
