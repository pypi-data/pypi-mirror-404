from typing import Dict, Any, List
from ..codebase_indexer import CodebaseIndexer
from .base import BaseTool, ToolResult, PermissionLevel


class CodebaseSearchTool(BaseTool):
    """Tool for searching indexed codebase"""
    
    def __init__(self, project_path: str = None):
        """Initialize tool
        
        Args:
            project_path: Path to project root
        """
        super().__init__(
            name="codebase_search",
            description="""Search the indexed codebase for symbols, files, imports, and more.
            
            Use this tool when you need to:
            - Find where a function or class is defined
            - Locate files by name or path
            - Find all usages of an import
            - Get codebase statistics
            - Understand project structure
            
            The codebase is automatically indexed on startup for fast searching.""",
            permission_level=PermissionLevel.READ_ONLY
        )
        self.project_path = project_path
        self.indexer = None
        if project_path:
            self.indexer = CodebaseIndexer(project_path)
    
    async def execute(self, action: str, query: str = None, file_path: str = None, 
                language: str = None, limit: int = 50, **kwargs) -> ToolResult:
        """Execute codebase search
        
        Args:
            action: Action to perform
            query: Search query
            file_path: File path for get_file_info
            language: Language filter
            limit: Maximum results
        
        Returns:
            ToolResult containing search results or stats
        """
        if not self.indexer:
            return ToolResult(
                success=False,
                error="No project path set. Use /workspace command to set working directory."
            )
        
        try:
            # Load index
            index = self.indexer.load_index()
            if not index:
                return ToolResult(
                    success=False,
                    error="Codebase not indexed. Index will be created automatically on next startup."
                )
            
            # Execute action
            if action == "search":
                if not query:
                    return ToolResult(success=False, error="Query required for search action")
                
                results = self.indexer.search(query, index)
                return ToolResult(
                    success=True,
                    data={
                        "action": "search",
                        "query": query,
                        "total_results": len(results),
                        "results": results[:limit]
                    }
                )
            
            elif action == "stats":
                stats = self.indexer.get_stats(index)
                return ToolResult(
                    success=True,
                    data={
                        "action": "stats",
                        "stats": stats
                    }
                )
            
            elif action == "list_files":
                files = []
                for file_index in index.files.values():
                    if language and file_index.language != language:
                        continue
                    files.append({
                        "path": file_index.relative_path,
                        "language": file_index.language,
                        "lines": file_index.lines_of_code,
                        "size": file_index.size
                    })
                
                return ToolResult(
                    success=True,
                    data={
                        "action": "list_files",
                        "language_filter": language,
                        "total_files": len(files),
                        "results": files[:limit]
                    }
                )
            
            elif action == "get_file_info":
                if not file_path:
                    return ToolResult(success=False, error="file_path required for get_file_info action")
                
                file_index = index.files.get(file_path)
                if not file_index:
                    return ToolResult(success=False, error=f"File not found in index: {file_path}")
                
                return ToolResult(
                    success=True,
                    data={
                        "action": "get_file_info",
                        "file": {
                            "path": file_index.relative_path,
                            "language": file_index.language,
                            "lines": file_index.lines_of_code,
                            "size": file_index.size,
                            "symbols": file_index.symbols,
                            "imports": file_index.imports,
                            "docstrings": file_index.docstrings
                        }
                    }
                )
            
            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error executing codebase search: {str(e)}"
            )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "codebase_search",
                "description": "Search the indexed codebase for symbols, files, and imports. Extremely fast.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["search", "stats", "list_files", "get_file_info"],
                            "description": "Action to perform"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query for 'search' action"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "File path for 'get_file_info' action"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results (default: 50)"
                        }
                    },
                    "required": ["action"]
                }
            }
        }

    def get_capabilities(self) -> List[str]:
        return ["search", "stats", "list_files", "get_file_info"]
