"""
File reader tool for reading and searching files
"""

import os
import re
from typing import List, Dict, Any
from pathlib import Path

from .base import BaseTool, ToolResult, PermissionLevel


class FileReaderTool(BaseTool):
    """Tool for reading files and searching content"""
    
    def __init__(self):
        super().__init__(
            name="file_reader",
            description="Read file contents and search in files",
            permission_level=PermissionLevel.READ_ONLY
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "read_file",
            "grep_search",
            "list_directory"
        ]
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute file reader operation"""
        
        operations = {
            'read_file': self._read_file,
            'grep_search': self._grep_search,
            'list_directory': self._list_directory
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
    
    async def _read_file(
        self,
        file_path: str,
        start_line: int = None,
        end_line: int = None,
        max_lines: int = 1000
    ) -> Dict[str, Any]:
        """Read file contents"""
        
        try:
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not path.is_file():
                raise ValueError(f"Not a file: {file_path}")
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            if start_line is not None or end_line is not None:
                start = (start_line - 1) if start_line else 0
                end = end_line if end_line else total_lines
                lines = lines[start:end]
            
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                truncated = True
            else:
                truncated = False
            
            content = ''.join(lines)
            
            return {
                'file_path': str(path),
                'content': content,
                'total_lines': total_lines,
                'lines_returned': len(lines),
                'truncated': truncated
            }
            
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")
    
    async def _grep_search(
        self,
        pattern: str,
        search_path: str,
        file_pattern: str = "*",
        recursive: bool = True,
        case_sensitive: bool = False,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """Search for pattern in files"""
        
        try:
            search_path = Path(search_path).expanduser().resolve()
            
            if not search_path.exists():
                raise FileNotFoundError(f"Path not found: {search_path}")
            
            results = []
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
            
            if search_path.is_file():
                files_to_search = [search_path]
            else:
                if recursive:
                    files_to_search = list(search_path.rglob(file_pattern))
                else:
                    files_to_search = list(search_path.glob(file_pattern))
                
                files_to_search = [f for f in files_to_search if f.is_file()]
            
            for file_path in files_to_search:
                if len(results) >= max_results:
                    break
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if len(results) >= max_results:
                                break
                            
                            if regex.search(line):
                                results.append({
                                    'file': str(file_path),
                                    'line_number': line_num,
                                    'line_content': line.rstrip('\n'),
                                    'match': regex.search(line).group(0)
                                })
                except Exception:
                    continue
            
            return {
                'pattern': pattern,
                'search_path': str(search_path),
                'total_matches': len(results),
                'matches': results,
                'truncated': len(results) >= max_results
            }
            
        except Exception as e:
            raise Exception(f"Failed to search: {str(e)}")
    
    async def _list_directory(
        self,
        directory_path: str,
        show_hidden: bool = False,
        recursive: bool = False,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """List directory contents"""
        
        try:
            path = Path(directory_path).expanduser().resolve()
            
            if not path.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            if not path.is_dir():
                raise ValueError(f"Not a directory: {directory_path}")
            
            items = []
            
            if recursive:
                for item in path.rglob('*'):
                    if not show_hidden and item.name.startswith('.'):
                        continue
                    
                    try:
                        relative = item.relative_to(path)
                        depth = len(relative.parts)
                        if depth > max_depth:
                            continue
                    except ValueError:
                        continue
                    
                    items.append({
                        'path': str(item),
                        'name': item.name,
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': item.stat().st_size if item.is_file() else None
                    })
            else:
                for item in path.iterdir():
                    if not show_hidden and item.name.startswith('.'):
                        continue
                    
                    items.append({
                        'path': str(item),
                        'name': item.name,
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': item.stat().st_size if item.is_file() else None
                    })
            
            return {
                'directory': str(path),
                'total_items': len(items),
                'items': items
            }
            
        except Exception as e:
            raise Exception(f"Failed to list directory: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "file_reader",
                "description": "Read file contents and search in files. Use 'file_operations' for most file tasks instead.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The operation to perform",
                            "enum": ["read_file", "grep_search", "list_directory"]
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read (required for read_file)"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Regex pattern to search for (required for grep_search)"
                        },
                        "search_path": {
                            "type": "string",
                            "description": "Directory path to search in (required for grep_search)"
                        },
                        "directory_path": {
                            "type": "string",
                            "description": "Path to the directory to list (required for list_directory)"
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "First line to read (1-indexed)"
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "Last line to read (inclusive)"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Whether to search/list recursively"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
