"""
Base classes for tools
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from enum import Enum


class PermissionLevel(Enum):
    """Permission levels for tool execution"""
    READ_ONLY = "read_only"
    SAFE_OPERATIONS = "safe_operations"
    SYSTEM_OPERATIONS = "system_operations"
    UNRESTRICTED = "unrestricted"


class ToolResult:
    """Result of a tool execution"""
    
    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error
        }


class BaseTool(ABC):
    """Base class for all tools"""
    
    def __init__(self, name: str, description: str, permission_level: PermissionLevel):
        self.name = name
        self.description = description
        self.permission_level = permission_level
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities this tool provides"""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool (OpenAI compatible format)"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information"""
        return {
            'name': self.name,
            'description': self.description,
            'permission_level': self.permission_level.value,
            'capabilities': self.get_capabilities(),
            'schema': self.get_schema()
        }
