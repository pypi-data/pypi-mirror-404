"""
Tool registry for managing and executing tools
"""

from typing import Dict, List, Optional
import asyncio
from .base import BaseTool, ToolResult, PermissionLevel


class PermissionManager:
    """Manages permissions for tool execution"""
    
    def __init__(self, default_level: PermissionLevel = PermissionLevel.SAFE_OPERATIONS):
        self.default_level = default_level
        self.user_permissions = {}
    
    def can_execute(self, tool: BaseTool, user_id: str = "default") -> bool:
        """Check if user can execute a tool"""
        user_level = self.user_permissions.get(user_id, self.default_level)
        
        # Permission hierarchy
        hierarchy = {
            PermissionLevel.READ_ONLY: 0,
            PermissionLevel.SAFE_OPERATIONS: 1,
            PermissionLevel.SYSTEM_OPERATIONS: 2,
            PermissionLevel.UNRESTRICTED: 3
        }
        
        return hierarchy[user_level] >= hierarchy[tool.permission_level]
    
    def set_user_permission(self, user_id: str, level: PermissionLevel):
        """Set permission level for a user"""
        self.user_permissions[user_id] = level


class ToolRegistry:
    """Registry for managing and executing tools"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.permission_manager = PermissionManager()
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools"""
        from .file_operations import FileOperationsTool
        from .command_runner import CommandRunnerTool
        from .web_search import WebSearchTool
        from .code_analysis import CodeAnalysisTool
        from .response_control import ResponseControlTool
        from .file_reader import FileReaderTool
        from .directory_context import DirectoryContextTool
        from .code_navigation import CodeNavigationTool
        from .codebase_search import CodebaseSearchTool
        from .ask_question import AskQuestionTool
        
        # Register tools
        self.register_tool(FileOperationsTool())
        self.register_tool(CommandRunnerTool())
        self.register_tool(WebSearchTool())
        self.register_tool(CodeAnalysisTool())
        self.register_tool(ResponseControlTool())
        self.register_tool(FileReaderTool())
        self.register_tool(DirectoryContextTool())
        self.register_tool(CodeNavigationTool())
        self.register_tool(CodebaseSearchTool())
        self.register_tool(AskQuestionTool())
    
    def register_tool(self, tool: BaseTool):
        """Register a tool"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tools"""
        return list(self.tools.keys())
    
    def get_tool_info(self, name: str) -> Optional[Dict]:
        """Get information about a tool"""
        tool = self.get_tool(name)
        return tool.get_info() if tool else None
    
    def list_all_tools_info(self) -> List[Dict]:
        """Get information about all tools"""
        return [tool.get_info() for tool in self.tools.values()]
    
    async def execute_tool(
        self, 
        tool_name: str, 
        user_id: str = "default",
        **kwargs
    ) -> ToolResult:
        """Execute a tool with given parameters"""
        
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found"
            )
        
        # Check permissions
        if not self.permission_manager.can_execute(tool, user_id):
            return ToolResult(
                success=False,
                error=f"Insufficient permissions to execute '{tool_name}'"
            )
        
        try:
            # Execute the tool
            result = await tool.execute(**kwargs)
            return result
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )
    
    def set_permission_level(self, user_id: str, level: PermissionLevel):
        """Set permission level for a user"""
        self.permission_manager.set_user_permission(user_id, level)
