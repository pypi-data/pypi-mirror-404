"""
File tagging system for referencing files in AI conversations
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import fnmatch


class FileTag:
    """Represents a file tag with its path and content"""
    
    def __init__(self, tag: str, file_path: str, content: str = None, exists: bool = True):
        self.tag = tag  # Original @tag from user input
        self.file_path = file_path  # Resolved absolute path
        self.content = content  # File content (loaded lazily)
        self.exists = exists  # Whether file exists
        self.relative_path = None  # Relative path from workspace
    
    def load_content(self) -> str:
        """Load file content if not already loaded"""
        if self.content is None and self.exists:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.content = f.read()
            except Exception as e:
                self.content = f"Error reading file: {str(e)}"
                self.exists = False
        return self.content or ""


class FileTagger:
    """Handles file tagging and resolution"""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = Path(workspace_path).resolve() if workspace_path else None
    
    def find_file_tags(self, text: str) -> List[str]:
        """Find all @file tags in text"""
        # Match @filename, @path/filename, @./filename, @../filename, @/absolute/path
        pattern = r'@([a-zA-Z0-9._/-]+(?:\.[a-zA-Z0-9]+)?)'
        matches = re.findall(pattern, text)
        return [f"@{match}" for match in matches]
    
    def resolve_file_path(self, tag: str) -> Tuple[str, bool]:
        """Resolve a file tag to an absolute path"""
        # Remove @ prefix
        file_ref = tag[1:] if tag.startswith('@') else tag
        
        # Handle different path types
        if os.path.isabs(file_ref):
            # Absolute path
            resolved_path = Path(file_ref).resolve()
        elif file_ref.startswith('./') or file_ref.startswith('../'):
            # Relative path from current working directory
            resolved_path = Path(file_ref).resolve()
        elif self.workspace_path and '/' not in file_ref:
            # Simple filename - look in workspace root first
            resolved_path = self.workspace_path / file_ref
            if not resolved_path.exists():
                # If not found in workspace, try current directory
                resolved_path = Path(file_ref).resolve()
        elif self.workspace_path:
            # Relative path from workspace
            resolved_path = self.workspace_path / file_ref
        else:
            # No workspace, treat as relative to current directory
            resolved_path = Path(file_ref).resolve()
        
        return str(resolved_path), resolved_path.exists()
    
    def get_file_suggestions(self, partial_path: str = "", limit: int = 20) -> List[str]:
        """Get file suggestions for autocompletion"""
        suggestions = []
        
        # Get files from workspace if available
        if self.workspace_path and self.workspace_path.exists():
            suggestions.extend(self._get_workspace_suggestions(partial_path, limit // 2))
        
        # Get files from current directory
        suggestions.extend(self._get_current_dir_suggestions(partial_path, limit // 2))
        
        return list(set(suggestions))[:limit]
    
    def _get_workspace_suggestions(self, partial_path: str, limit: int) -> List[str]:
        """Get file suggestions from workspace"""
        suggestions = []
        try:
            if not partial_path:
                # Show files in workspace root
                for item in self.workspace_path.iterdir():
                    if item.is_file() and not item.name.startswith('.'):
                        suggestions.append(item.name)
            else:
                # Search for matching files - both prefix and contains matches
                # First, try exact prefix matches
                for item in self.workspace_path.rglob("*"):
                    if item.is_file() and not any(part.startswith('.') for part in item.parts):
                        rel_path = item.relative_to(self.workspace_path)
                        rel_path_str = str(rel_path)
                        # Check if filename starts with partial_path
                        if item.name.startswith(partial_path) or rel_path_str.startswith(partial_path):
                            suggestions.append(rel_path_str)
                
                # If no prefix matches, try contains matches
                if not suggestions:
                    pattern = f"*{partial_path}*"
                    for item in self.workspace_path.rglob(pattern):
                        if item.is_file() and not any(part.startswith('.') for part in item.parts):
                            rel_path = item.relative_to(self.workspace_path)
                            suggestions.append(str(rel_path))
        except Exception:
            pass
        
        return suggestions[:limit]
    
    def _get_current_dir_suggestions(self, partial_path: str, limit: int) -> List[str]:
        """Get file suggestions from current directory"""
        suggestions = []
        try:
            current_dir = Path.cwd()
            if not partial_path:
                # Show files in current directory
                for item in current_dir.iterdir():
                    if item.is_file() and not item.name.startswith('.'):
                        suggestions.append(f"./{item.name}")
            else:
                # Search for matching files - prefix matches first
                for item in current_dir.rglob("*"):
                    if item.is_file() and not any(part.startswith('.') for part in item.parts):
                        rel_path = item.relative_to(current_dir)
                        rel_path_str = str(rel_path)
                        # Check if filename starts with partial_path
                        if item.name.startswith(partial_path) or rel_path_str.startswith(partial_path):
                            suggestions.append(f"./{rel_path_str}")
                
                # If no prefix matches, try contains matches
                if not suggestions:
                    pattern = f"*{partial_path}*"
                    for item in current_dir.rglob(pattern):
                        if item.is_file() and not any(part.startswith('.') for part in item.parts):
                            rel_path = item.relative_to(current_dir)
                            suggestions.append(f"./{rel_path}")
        except Exception:
            pass
        
        return suggestions[:limit]
    
    def process_message_with_tags(self, message: str) -> Tuple[str, List[FileTag]]:
        """Process a message and resolve all file tags"""
        tags = self.find_file_tags(message)
        file_tags = []
        processed_message = message
        
        for tag in tags:
            file_path, exists = self.resolve_file_path(tag)
            file_tag = FileTag(tag, file_path, exists=exists)
            
            # Set relative path if in workspace
            if self.workspace_path and file_path.startswith(str(self.workspace_path)):
                file_tag.relative_path = str(Path(file_path).relative_to(self.workspace_path))
            
            file_tags.append(file_tag)
        
        return processed_message, file_tags
    
    def format_file_context(self, file_tags: List[FileTag]) -> str:
        """Format file tags into context for AI"""
        if not file_tags:
            return ""
        
        context_parts = ["## Referenced Files:\n"]
        
        for file_tag in file_tags:
            if file_tag.exists:
                content = file_tag.load_content()
                display_path = file_tag.relative_path or file_tag.file_path
                
                context_parts.append(f"### {file_tag.tag} ({display_path})")
                context_parts.append("```")
                context_parts.append(content)
                context_parts.append("```\n")
            else:
                context_parts.append(f"### {file_tag.tag} (FILE NOT FOUND)")
                context_parts.append(f"Path: {file_tag.file_path}\n")
        
        return "\n".join(context_parts)


def create_file_tagger(workspace_path: str = None) -> FileTagger:
    """Create a FileTagger instance"""
    return FileTagger(workspace_path)
