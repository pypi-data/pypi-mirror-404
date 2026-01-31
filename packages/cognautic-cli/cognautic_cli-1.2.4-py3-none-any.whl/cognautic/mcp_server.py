"""
MCP Server implementation for Cognautic CLI
Exposes Cognautic's tools, resources, and prompts as an MCP server
"""

import asyncio
import json
import logging
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP Server that exposes Cognautic's capabilities
    Implements the Model Context Protocol server specification
    """

    def __init__(self, tool_registry, workspace: Optional[str] = None):
        self.tool_registry = tool_registry
        self.workspace = workspace or str(Path.cwd())
        self.capabilities = {
            "resources": {"subscribe": False, "listChanged": False},
            "tools": {"listChanged": False},
            "prompts": {"listChanged": False}
        }
        self.running = False

    async def start(self):
        """Start the MCP server (STDIO transport)"""
        self.running = True
        logger.info("MCP Server started")

        try:
            while self.running:
                # Read JSON-RPC message from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    break

                try:
                    message = json.loads(line.strip())
                    await self._handle_message(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    await self._send_error(-32700, "Parse error", None)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")

        except Exception as e:
            logger.error(f"MCP Server error: {e}")
        finally:
            self.running = False
            logger.info("MCP Server stopped")

    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming JSON-RPC message"""
        if "method" not in message:
            await self._send_error(-32600, "Invalid Request", message.get("id"))
            return

        method = message["method"]
        params = message.get("params", {})
        msg_id = message.get("id")

        # Handle requests (expect response)
        if msg_id is not None:
            await self._handle_request(method, params, msg_id)
        else:
            # Handle notifications (no response)
            await self._handle_notification(method, params)

    async def _handle_request(self, method: str, params: Dict[str, Any], msg_id: int):
        """Handle JSON-RPC request"""
        try:
            if method == "initialize":
                await self._handle_initialize(params, msg_id)
            elif method == "resources/list":
                await self._handle_resources_list(params, msg_id)
            elif method == "resources/read":
                await self._handle_resources_read(params, msg_id)
            elif method == "tools/list":
                await self._handle_tools_list(params, msg_id)
            elif method == "tools/call":
                await self._handle_tools_call(params, msg_id)
            elif method == "prompts/list":
                await self._handle_prompts_list(params, msg_id)
            elif method == "prompts/get":
                await self._handle_prompts_get(params, msg_id)
            else:
                await self._send_error(-32601, f"Method not found: {method}", msg_id)
        except Exception as e:
            logger.error(f"Error handling request {method}: {e}")
            await self._send_error(-32603, f"Internal error: {str(e)}", msg_id)

    async def _handle_notification(self, method: str, params: Dict[str, Any]):
        """Handle JSON-RPC notification"""
        if method == "notifications/initialized":
            logger.info("Client initialized")
        elif method == "notifications/cancelled":
            logger.info(f"Request cancelled: {params}")
        else:
            logger.debug(f"Received notification: {method}")

    async def _handle_initialize(self, params: Dict[str, Any], msg_id: int):
        """Handle initialize request"""
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": self.capabilities,
            "serverInfo": {
                "name": "cognautic-cli",
                "version": "1.2.3-1"
            }
        }
        await self._send_response(result, msg_id)

    async def _handle_resources_list(self, params: Dict[str, Any], msg_id: int):
        """Handle resources/list request"""
        # Expose workspace files as resources
        resources = []

        try:
            workspace_path = Path(self.workspace)
            if workspace_path.exists():
                # List common project files as resources
                common_files = [
                    "README.md", "package.json", "pyproject.toml",
                    "requirements.txt", "setup.py", ".gitignore"
                ]

                for filename in common_files:
                    file_path = workspace_path / filename
                    if file_path.exists():
                        resources.append({
                            "uri": f"file://{file_path}",
                            "name": filename,
                            "description": f"Project file: {filename}",
                            "mimeType": "text/plain"
                        })
        except Exception as e:
            logger.error(f"Error listing resources: {e}")

        result = {"resources": resources}
        await self._send_response(result, msg_id)

    async def _handle_resources_read(self, params: Dict[str, Any], msg_id: int):
        """Handle resources/read request"""
        uri = params.get("uri")
        if not uri:
            await self._send_error(-32602, "Missing uri parameter", msg_id)
            return

        try:
            # Parse file:// URI
            if uri.startswith("file://"):
                file_path = Path(uri[7:])
                if file_path.exists() and file_path.is_file():
                    content = file_path.read_text()
                    result = {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "text/plain",
                            "text": content
                        }]
                    }
                    await self._send_response(result, msg_id)
                else:
                    await self._send_error(-32602, f"File not found: {uri}", msg_id)
            else:
                await self._send_error(-32602, f"Unsupported URI scheme: {uri}", msg_id)
        except Exception as e:
            logger.error(f"Error reading resource: {e}")
            await self._send_error(-32603, f"Error reading resource: {str(e)}", msg_id)

    async def _handle_tools_list(self, params: Dict[str, Any], msg_id: int):
        """Handle tools/list request"""
        tools = []

        # Convert Cognautic tools to MCP tool format
        for tool_name, tool_instance in self.tool_registry.tools.items():
            tool_info = {
                "name": tool_name,
                "description": tool_instance.description,
                "inputSchema": {
                    "type": "object",
                    "properties": self._get_tool_schema(tool_instance),
                    "required": []
                }
            }
            tools.append(tool_info)

        result = {"tools": tools}
        await self._send_response(result, msg_id)

    def _get_tool_schema(self, tool_instance) -> Dict[str, Any]:
        """Generate JSON schema for tool parameters"""
        # This is a simplified schema - you may want to enhance this
        # based on your tool's actual parameter requirements
        schema = {}

        # Common parameters for file operations
        if hasattr(tool_instance, 'execute'):
            import inspect
            sig = inspect.signature(tool_instance.execute)
            for param_name, param in sig.parameters.items():
                if param_name == 'self' or param_name == 'kwargs':
                    continue
                schema[param_name] = {
                    "type": "string",
                    "description": f"Parameter: {param_name}"
                }

        return schema

    async def _handle_tools_call(self, params: Dict[str, Any], msg_id: int):
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            await self._send_error(-32602, "Missing tool name", msg_id)
            return

        try:
            # Get the tool from registry
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                await self._send_error(-32602, f"Tool not found: {tool_name}", msg_id)
                return

            # Execute the tool
            tool_result = await tool.execute(**arguments)

            # Format result for MCP
            result = {
                "content": [{
                    "type": "text",
                    "text": json.dumps(tool_result.to_dict(), indent=2)
                }],
                "isError": not tool_result.success
            }

            await self._send_response(result, msg_id)

        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            await self._send_error(-32603, f"Tool execution error: {str(e)}", msg_id)

    async def _handle_prompts_list(self, params: Dict[str, Any], msg_id: int):
        """Handle prompts/list request"""
        # Define some useful prompts for Cognautic
        prompts = [
            {
                "name": "code_review",
                "description": "Review code in the workspace for quality and best practices",
                "arguments": [
                    {
                        "name": "file_path",
                        "description": "Path to the file to review",
                        "required": True
                    }
                ]
            },
            {
                "name": "debug_help",
                "description": "Help debug an issue in the code",
                "arguments": [
                    {
                        "name": "error_message",
                        "description": "The error message or issue description",
                        "required": True
                    },
                    {
                        "name": "file_path",
                        "description": "Path to the file with the issue",
                        "required": False
                    }
                ]
            },
            {
                "name": "implement_feature",
                "description": "Implement a new feature in the codebase",
                "arguments": [
                    {
                        "name": "feature_description",
                        "description": "Description of the feature to implement",
                        "required": True
                    }
                ]
            }
        ]

        result = {"prompts": prompts}
        await self._send_response(result, msg_id)

    async def _handle_prompts_get(self, params: Dict[str, Any], msg_id: int):
        """Handle prompts/get request"""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})

        if not prompt_name:
            await self._send_error(-32602, "Missing prompt name", msg_id)
            return

        # Generate prompt based on name and arguments
        prompt_text = self._generate_prompt(prompt_name, arguments)

        if prompt_text:
            result = {
                "description": f"Prompt: {prompt_name}",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }
            await self._send_response(result, msg_id)
        else:
            await self._send_error(-32602, f"Prompt not found: {prompt_name}", msg_id)

    def _generate_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Generate prompt text based on name and arguments"""
        if prompt_name == "code_review":
            file_path = arguments.get("file_path", "")
            return f"Please review the code in {file_path} for quality, best practices, and potential issues."

        elif prompt_name == "debug_help":
            error_message = arguments.get("error_message", "")
            file_path = arguments.get("file_path", "")
            if file_path:
                return f"I'm getting this error: {error_message}\nIn file: {file_path}\nCan you help me debug this?"
            else:
                return f"I'm getting this error: {error_message}\nCan you help me debug this?"

        elif prompt_name == "implement_feature":
            feature_description = arguments.get("feature_description", "")
            return f"Please implement the following feature:\n{feature_description}"

        return None

    async def _send_response(self, result: Any, msg_id: int):
        """Send JSON-RPC response"""
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        await self._write_message(response)

    async def _send_error(self, code: int, message: str, msg_id: Optional[int]):
        """Send JSON-RPC error response"""
        error_response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        await self._write_message(error_response)

    async def _write_message(self, message: Dict[str, Any]):
        """Write JSON-RPC message to stdout"""
        try:
            message_json = json.dumps(message) + "\n"
            sys.stdout.write(message_json)
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Error writing message: {e}")

    def stop(self):
        """Stop the MCP server"""
        self.running = False
