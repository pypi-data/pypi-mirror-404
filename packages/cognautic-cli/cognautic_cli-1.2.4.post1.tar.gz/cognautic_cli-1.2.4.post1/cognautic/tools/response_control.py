"""
Response control tool for managing AI continuation
"""

from typing import List, Dict, Any
from .base import BaseTool, ToolResult, PermissionLevel


class ResponseControlTool(BaseTool):
    """Tool for controlling AI response continuation"""
    
    def __init__(self):
        super().__init__(
            name="response_control",
            description="Control when AI response should end (stops auto-continuation)",
            permission_level=PermissionLevel.SAFE_OPERATIONS
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "end_response",
            "continue_response"
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "response_control",
                "description": "Control when AI response should end (stops auto-continuation)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The operation to perform",
                            "enum": self.get_capabilities()
                        },
                        "message": {
                            "type": "string",
                            "description": "Final message or reason for ending/continuing"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute response control operation"""
        
        if operation == "end_response":
            return ToolResult(
                success=True,
                data={
                    "action": "end_response",
                    "message": kwargs.get("message", "Response completed")
                }
            )
        elif operation == "continue_response":
            return ToolResult(
                success=True,
                data={
                    "action": "continue_response",
                    "message": kwargs.get("message", "Continuing response")
                }
            )
        else:
            return ToolResult(
                success=False,
                error=f"Unknown operation: {operation}"
            )
