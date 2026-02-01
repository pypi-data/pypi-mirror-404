"""
File operations tool for Cognautic CLI
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
import fnmatch

from .base import BaseTool, ToolResult, PermissionLevel


class FileOperationsTool(BaseTool):
    """Tool for file and directory operations"""
    
    def __init__(self):
        super().__init__(
            name="file_operations",
            description="Read, write, create, delete, and modify files and directories",
            permission_level=PermissionLevel.SAFE_OPERATIONS
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "read_file",
            "read_file_lines",
            "write_file",
            "write_file_lines",
            "create_file",
            "create_directory",
            "delete_file",
            "list_directory",
            "search_files",
            "copy_file",
            "move_file"
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "file_operations",
                "description": "Read, write, create, delete, and modify files and directories",
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
                            "description": "Path to the file"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        },
                        "dir_path": {
                            "type": "string",
                            "description": "Path to the directory"
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Start line for partial read/write (1-indexed)"
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "End line for partial read/write (1-indexed)"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Whether to perform operation recursively"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern for file search"
                        },
                        "source": {
                            "type": "string",
                            "description": "Source path for copy/move"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination path for copy/move"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute file operation"""
        
        operations = {
            'read_file': self._read_file,
            'read_file_lines': self._read_file_lines,
            'write_file': self._write_file,
            'write_file_lines': self._write_file_lines,
            'create_file': self._create_file,
            'create_directory': self._create_directory,
            'delete_file': self._delete_file,
            'list_directory': self._list_directory,
            'search_files': self._search_files,
            'copy_file': self._copy_file,
            'move_file': self._move_file
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
    
    async def _read_file(self, file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """Read content from a file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        with open(path, 'r', encoding=encoding) as f:
            content = f.read()
        
        return {
            'content': content,
            'file_path': str(path),
            'size': len(content)
        }
    
    async def _read_file_lines(self, file_path: str, start_line: int = 1, end_line: int = None, encoding: str = 'utf-8') -> Dict[str, Any]:
        """Read specific lines from a file (1-indexed)"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        with open(path, 'r', encoding=encoding) as f:
            all_lines = f.readlines()
        
        total_lines = len(all_lines)
        
        # Validate line numbers (1-indexed)
        if start_line < 1:
            start_line = 1
        if end_line is None or end_line > total_lines:
            end_line = total_lines
        
        # Convert to 0-indexed for slicing
        start_idx = start_line - 1
        end_idx = end_line
        
        selected_lines = all_lines[start_idx:end_idx]
        content = ''.join(selected_lines)
        
        return {
            'content': content,
            'file_path': str(path),
            'start_line': start_line,
            'end_line': end_line,
            'total_lines': total_lines,
            'lines_read': len(selected_lines)
        }
    
    async def _write_file(
        self, 
        file_path: str, 
        content: str, 
        encoding: str = 'utf-8',
        create_dirs: bool = True,
        append: bool = False
    ) -> Dict[str, Any]:
        """Write content to a file (supports large files)"""
        path = Path(file_path)
        existed_before = path.exists()
        
        # Get old content if file exists
        old_content = None
        if path.exists() and not append:
            with open(path, 'r', encoding=encoding) as f:
                old_content = f.read()

        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle large content by writing in chunks
        mode = 'a' if append else 'w'
        with open(path, mode, encoding=encoding) as f:
            # Write in chunks to handle large files efficiently
            chunk_size = 1024 * 1024  # 1MB chunks
            for i in range(0, len(content), chunk_size):
                f.write(content[i:i + chunk_size])
        
        return {
            'file_path': str(path),
            'size': path.stat().st_size,
            'created': not existed_before,
            'old_content': old_content,
            'new_content': content if not append else old_content + content if old_content else content
        }
    
    async def _write_file_lines(
        self, 
        file_path: str, 
        content: str,
        start_line: int = 1,
        end_line: int = None,
        encoding: str = 'utf-8',
        create_dirs: bool = True
    ) -> Dict[str, Any]:
        """Replace specific lines in a file (1-indexed)"""
        path = Path(file_path)
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing file if it exists to capture old content
        if path.exists():
            with open(path, 'r', encoding=encoding) as f:
                all_lines = f.readlines()
            old_content = ''.join(all_lines)
        else:
            all_lines = []
            old_content = None
        
        total_lines = len(all_lines)
        
        # Validate line numbers (1-indexed)
        if start_line < 1:
            start_line = 1
        if end_line is None:
            end_line = start_line
        
        # Convert to 0-indexed for slicing
        start_idx = start_line - 1
        end_idx = end_line
        
        # Ensure content ends with newline if it doesn't
        new_content = content
        if new_content and not new_content.endswith('\n'):
            new_content += '\n'
        
        # Split new content into lines
        new_lines = new_content.split('\n')
        # Remove empty last line if content ended with newline
        if new_lines and new_lines[-1] == '':
            new_lines.pop()
        # Add newlines back
        new_lines = [line + '\n' for line in new_lines]
        
        # If file is empty or we're appending beyond end
        if start_idx >= total_lines:
            # Pad with empty lines if needed
            while len(all_lines) < start_idx:
                all_lines.append('\n')
            all_lines.extend(new_lines)
        else:
            # Replace the specified range
            all_lines[start_idx:end_idx] = new_lines
        
        # Write back to file
        with open(path, 'w', encoding=encoding) as f:
            f.writelines(all_lines)
        
        new_file_content = ''.join(all_lines)
        
        return {
            'file_path': str(path),
            'start_line': start_line,
            'end_line': start_line + len(new_lines) - 1,
            'lines_written': len(new_lines),
            'total_lines': len(all_lines),
            'old_content': old_content,
            'new_content': new_file_content
        }
    
    async def _create_file(self, file_path: str, content: str = "", encoding: str = 'utf-8') -> Dict[str, Any]:
        """Create a new file with content (alias for write_file)"""
        return await self._write_file(file_path, content, encoding, create_dirs=True)
    
    async def _create_directory(self, dir_path: str = None, path: str = None, parents: bool = True) -> Dict[str, Any]:
        """Create a directory (accepts either dir_path or path parameter)"""
        # Accept both dir_path and path for flexibility
        directory_path = dir_path or path
        if not directory_path:
            raise ValueError("Either 'dir_path' or 'path' parameter is required")
        
        dir_obj = Path(directory_path)
        dir_obj.mkdir(parents=parents, exist_ok=True)
        
        return {
            'directory_path': str(dir_obj),
            'created': True
        }
    
    async def _delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete a file or directory"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {file_path}")
        
        if path.is_file():
            path.unlink()
            return {'deleted': str(path), 'type': 'file'}
        elif path.is_dir():
            shutil.rmtree(path)
            return {'deleted': str(path), 'type': 'directory'}
        else:
            raise ValueError(f"Unknown path type: {file_path}")
    
    async def _list_directory(
        self, 
        dir_path: str, 
        recursive: bool = False,
        include_hidden: bool = False
    ) -> List[Dict[str, Any]]:
        """List contents of a directory"""
        path = Path(dir_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")
        
        items = []
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for item in path.glob(pattern):
            if not include_hidden and item.name.startswith('.'):
                continue
            
            item_info = {
                'name': item.name,
                'path': str(item),
                'type': 'directory' if item.is_dir() else 'file',
                'size': item.stat().st_size if item.is_file() else None,
                'modified': item.stat().st_mtime
            }
            items.append(item_info)
        
        return items
    
    async def _search_files(
        self,
        search_path: str,
        pattern: str,
        content_search: str = None,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """Search for files by name pattern and optionally content"""
        path = Path(search_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Search path not found: {search_path}")
        
        matches = []
        
        # Search by filename pattern
        for item in path.rglob("*"):
            if item.is_file():
                if fnmatch.fnmatch(item.name, pattern):
                    match_info = {
                        'path': str(item),
                        'name': item.name,
                        'size': item.stat().st_size,
                        'modified': item.stat().st_mtime,
                        'content_matches': []
                    }
                    
                    # Search content if specified
                    if content_search:
                        try:
                            with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                            search_term = content_search if case_sensitive else content_search.lower()
                            search_content = content if case_sensitive else content.lower()
                            
                            if search_term in search_content:
                                # Find line numbers with matches
                                lines = content.split('\n')
                                for i, line in enumerate(lines, 1):
                                    line_search = line if case_sensitive else line.lower()
                                    if search_term in line_search:
                                        match_info['content_matches'].append({
                                            'line_number': i,
                                            'line_content': line.strip()
                                        })
                        except Exception:
                            # Skip files that can't be read
                            continue
                    
                    matches.append(match_info)
        
        return matches
    
    async def _copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file or directory"""
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source not found: {source}")
        
        # Create destination directory if needed
        if dst_path.suffix:  # destination is a file
            dst_path.parent.mkdir(parents=True, exist_ok=True)
        else:  # destination is a directory
            dst_path.mkdir(parents=True, exist_ok=True)
        
        if src_path.is_file():
            if dst_path.is_dir():
                dst_path = dst_path / src_path.name
            shutil.copy2(src_path, dst_path)
            return {'copied': str(src_path), 'to': str(dst_path), 'type': 'file'}
        elif src_path.is_dir():
            if dst_path.exists() and dst_path.is_dir():
                dst_path = dst_path / src_path.name
            shutil.copytree(src_path, dst_path)
            return {'copied': str(src_path), 'to': str(dst_path), 'type': 'directory'}
        else:
            raise ValueError(f"Unknown source type: {source}")
    
    async def _move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move a file or directory"""
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source not found: {source}")
        
        # Create destination directory if needed
        if dst_path.suffix:  # destination is a file
            dst_path.parent.mkdir(parents=True, exist_ok=True)
        else:  # destination is a directory
            dst_path.mkdir(parents=True, exist_ok=True)
            dst_path = dst_path / src_path.name
        
        shutil.move(str(src_path), str(dst_path))
        
        return {
            'moved': str(src_path),
            'to': str(dst_path),
            'type': 'directory' if dst_path.is_dir() else 'file'
        }
