"""
MCP Tool Wrapper - Integrates MCP tools into Cognautic's tool registry
"""

from typing import Dict, Any, Optional
from .base import BaseTool, ToolResult, PermissionLevel
import logging

logger = logging.getLogger(__name__)


class MCPToolWrapper(BaseTool):
    """
    Wrapper that makes MCP tools compatible with Cognautic's tool registry
    Each instance wraps a single MCP tool from a specific server
    """
    
    def __init__(self, mcp_manager, server_name: str, tool_name: str, tool_info: Dict[str, Any]):
        """
        Initialize MCP tool wrapper
        
        Args:
            mcp_manager: MCPClientManager instance
            server_name: Name of the MCP server
            tool_name: Original MCP tool name
            tool_info: Tool information from MCP server
        """
        self.mcp_manager = mcp_manager
        self.server_name = server_name
        self.mcp_tool_name = tool_name
        self.tool_info = tool_info
        
        # Create unique tool name: mcp_servername_toolname
        wrapped_name = f"mcp_{server_name}_{tool_name}"
        
        # Extract description and schema
        description = tool_info.get('description', f'MCP tool from {server_name}')
        self.input_schema = tool_info.get('input_schema', {})  # Store schema as instance variable
        
        # Initialize base tool (without parameters - BaseTool doesn't accept it)
        super().__init__(
            name=wrapped_name,
            description=f"[MCP:{server_name}] {description}",
            permission_level=PermissionLevel.SAFE_OPERATIONS  # MCP tools are safe by default
        )
    
    def get_capabilities(self) -> list:
        """Get list of capabilities this MCP tool provides"""
        # Return the MCP tool name as its capability
        return [self.mcp_tool_name]
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the MCP tool
        
        Args:
            **kwargs: Tool arguments (will be passed to MCP server)
        
        Returns:
            ToolResult with the MCP tool's response
        """
        try:
            # Call the MCP tool through the manager
            result = await self.mcp_manager.call_tool(
                self.server_name,
                self.mcp_tool_name,
                kwargs
            )
            
            if result is None:
                return ToolResult(
                    success=False,
                    error=f"MCP tool '{self.mcp_tool_name}' returned no result"
                )
            
            # MCP tools return a dict with 'content' or 'result'
            # Extract the actual content
            if isinstance(result, dict):
                content = result.get('content') or result.get('result') or result
                
                # If content is a list of content blocks (MCP format)
                if isinstance(content, list):
                    # Combine all text content
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get('type') == 'text':
                                text_parts.append(item.get('text', ''))
                            else:
                                # Include other types as JSON
                                import json
                                text_parts.append(json.dumps(item))
                        else:
                            text_parts.append(str(item))
                    content = '\n'.join(text_parts)
                
                return ToolResult(
                    success=True,
                    data=content
                )
            else:
                return ToolResult(
                    success=True,
                    data=str(result)
                )
                
        except Exception as e:
            logger.error(f"MCP tool execution failed: {e}")
            return ToolResult(
                success=False,
                error=f"MCP tool execution failed: {str(e)}"
            )

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this MCP tool"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema
            }
        }


def register_mcp_tools(tool_registry, mcp_manager):
    """
    Register all MCP tools from connected servers into the tool registry
    
    Args:
        tool_registry: Cognautic's ToolRegistry instance
        mcp_manager: MCPClientManager instance
    
    Returns:
        Number of tools registered
    """
    tools_registered = 0
    
    # Get all tools from all connected MCP servers
    all_mcp_tools = mcp_manager.get_all_tools()
    
    for tool_info in all_mcp_tools:
        try:
            server_name = tool_info['mcp_server']
            tool_name = tool_info['mcp_tool_name']
            
            # Create wrapper
            wrapper = MCPToolWrapper(
                mcp_manager=mcp_manager,
                server_name=server_name,
                tool_name=tool_name,
                tool_info=tool_info
            )
            
            # Register with tool registry
            tool_registry.register_tool(wrapper)
            tools_registered += 1
            
            logger.info(f"Registered MCP tool: {wrapper.name}")
            
        except Exception as e:
            logger.error(f"Failed to register MCP tool {tool_info.get('name')}: {e}")
    
    return tools_registered


def unregister_mcp_tools(tool_registry, server_name: Optional[str] = None):
    """
    Unregister MCP tools from the tool registry
    
    Args:
        tool_registry: Cognautic's ToolRegistry instance
        server_name: If provided, only unregister tools from this server.
                    If None, unregister all MCP tools.
    
    Returns:
        Number of tools unregistered
    """
    tools_unregistered = 0
    
    # Get all registered tools
    all_tools = list(tool_registry.tools.keys())
    
    for tool_name in all_tools:
        # Check if it's an MCP tool
        if tool_name.startswith('mcp_'):
            # If server_name is specified, only unregister tools from that server
            if server_name:
                expected_prefix = f"mcp_{server_name}_"
                if not tool_name.startswith(expected_prefix):
                    continue
            
            # Unregister the tool
            if tool_name in tool_registry.tools:
                del tool_registry.tools[tool_name]
                tools_unregistered += 1
                logger.info(f"Unregistered MCP tool: {tool_name}")
    
    return tools_unregistered
