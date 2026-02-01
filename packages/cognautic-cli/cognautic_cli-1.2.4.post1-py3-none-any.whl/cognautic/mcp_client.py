"""
MCP Client implementation for Cognautic CLI
Allows connecting to external MCP servers to access their tools, resources, and prompts
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MCPTransportType(Enum):
    """MCP transport types"""
    STDIO = "stdio"
    HTTP_SSE = "http_sse"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection"""
    name: str
    command: str  # Command to start the server (for STDIO)
    args: List[str] = None  # Arguments for the command
    env: Dict[str, str] = None  # Environment variables
    transport: MCPTransportType = MCPTransportType.STDIO
    url: str = None  # URL for HTTP_SSE transport

    def __post_init__(self):
        if self.args is None:
            self.args = []
        if self.env is None:
            self.env = {}


@dataclass
class MCPResource:
    """Represents an MCP resource"""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None


@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class MCPPrompt:
    """Represents an MCP prompt template"""
    name: str
    description: Optional[str] = None
    arguments: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []


class MCPClient:
    """
    MCP Client for connecting to MCP servers
    Implements the Model Context Protocol client specification
    """

    def __init__(self, server_config: MCPServerConfig):
        self.config = server_config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.connected = False
        self.resources: List[MCPResource] = []
        self.tools: List[MCPTool] = []
        self.prompts: List[MCPPrompt] = []
        self._request_id = 0

    async def connect(self) -> bool:
        """Connect to the MCP server"""
        try:
            if self.config.transport == MCPTransportType.STDIO:
                return await self._connect_stdio()
            elif self.config.transport == MCPTransportType.HTTP_SSE:
                return await self._connect_http_sse()
            else:
                logger.error(f"Unsupported transport type: {self.config.transport}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.config.name}: {e}")
            return False

    async def _connect_stdio(self) -> bool:
        """Connect to MCP server using STDIO transport"""
        try:
            # Start the MCP server process
            self.process = await asyncio.create_subprocess_exec(
                self.config.command,
                *self.config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**self.config.env}
            )

            # Send initialize request
            init_response = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "cognautic-cli",
                    "version": "1.2.3-1"
                }
            })

            if not init_response or "error" in init_response:
                logger.error(f"Failed to initialize MCP server: {init_response}")
                return False

            # Send initialized notification
            await self._send_notification("notifications/initialized", {})

            # Discover server capabilities
            await self._discover_capabilities()

            self.connected = True
            logger.info(f"Connected to MCP server: {self.config.name}")
            return True

        except Exception as e:
            logger.error(f"STDIO connection failed: {e}")
            return False

    async def _connect_http_sse(self) -> bool:
        """Connect to MCP server using HTTP with SSE transport"""
        # TODO: Implement HTTP SSE transport
        logger.warning("HTTP SSE transport not yet implemented")
        return False

    async def _discover_capabilities(self):
        """Discover resources, tools, and prompts from the server"""
        try:
            # List resources
            resources_response = await self._send_request("resources/list", {})
            if resources_response and "result" in resources_response:
                self.resources = [
                    MCPResource(
                        uri=r.get("uri"),
                        name=r.get("name"),
                        description=r.get("description"),
                        mime_type=r.get("mimeType")
                    )
                    for r in resources_response["result"].get("resources", [])
                ]
                logger.info(f"Discovered {len(self.resources)} resources")

            # List tools
            tools_response = await self._send_request("tools/list", {})
            if tools_response and "result" in tools_response:
                self.tools = [
                    MCPTool(
                        name=t.get("name"),
                        description=t.get("description"),
                        input_schema=t.get("inputSchema", {})
                    )
                    for t in tools_response["result"].get("tools", [])
                ]
                logger.info(f"Discovered {len(self.tools)} tools")

            # List prompts
            prompts_response = await self._send_request("prompts/list", {})
            if prompts_response and "result" in prompts_response:
                self.prompts = [
                    MCPPrompt(
                        name=p.get("name"),
                        description=p.get("description"),
                        arguments=p.get("arguments", [])
                    )
                    for p in prompts_response["result"].get("prompts", [])
                ]
                logger.info(f"Discovered {len(self.prompts)} prompts")

        except Exception as e:
            logger.error(f"Failed to discover capabilities: {e}")

    async def read_resource(self, uri: str) -> Optional[Dict[str, Any]]:
        """Read a resource from the MCP server"""
        try:
            response = await self._send_request("resources/read", {"uri": uri})
            if response and "result" in response:
                return response["result"]
            return None
        except Exception as e:
            logger.error(f"Failed to read resource {uri}: {e}")
            return None

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call a tool on the MCP server"""
        try:
            response = await self._send_request("tools/call", {
                "name": name,
                "arguments": arguments
            })
            if response and "result" in response:
                return response["result"]
            return None
        except Exception as e:
            logger.error(f"Failed to call tool {name}: {e}")
            return None

    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Get a prompt from the MCP server"""
        try:
            params = {"name": name}
            if arguments:
                params["arguments"] = arguments

            response = await self._send_request("prompts/get", params)
            if response and "result" in response:
                return response["result"]
            return None
        except Exception as e:
            logger.error(f"Failed to get prompt {name}: {e}")
            return None

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request to the MCP server"""
        if not self.process or not self.process.stdin:
            logger.error("Not connected to MCP server")
            return None

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params
        }

        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()

            # Read response
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=30.0
            )

            if not response_line:
                logger.error("Empty response from MCP server")
                return None

            response = json.loads(response_line.decode())
            return response

        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response to {method}")
            return None
        except Exception as e:
            logger.error(f"Error sending request {method}: {e}")
            return None

    async def _send_notification(self, method: str, params: Dict[str, Any]):
        """Send a JSON-RPC notification (no response expected)"""
        if not self.process or not self.process.stdin:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }

        try:
            notification_json = json.dumps(notification) + "\n"
            self.process.stdin.write(notification_json.encode())
            await self.process.stdin.drain()
        except Exception as e:
            logger.error(f"Error sending notification {method}: {e}")

    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server: {e}")
            finally:
                self.process = None
                self.connected = False
                logger.info(f"Disconnected from MCP server: {self.config.name}")

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from this MCP server"""
        return [
            {
                "name": f"mcp_{self.config.name}_{tool.name}",
                "description": f"[MCP:{self.config.name}] {tool.description}",
                "input_schema": tool.input_schema,
                "mcp_server": self.config.name,
                "mcp_tool_name": tool.name
            }
            for tool in self.tools
        ]

    def get_available_resources(self) -> List[Dict[str, Any]]:
        """Get list of available resources from this MCP server"""
        return [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mime_type": resource.mime_type,
                "mcp_server": self.config.name
            }
            for resource in self.resources
        ]


class MCPClientManager:
    """
    Manages multiple MCP client connections
    """

    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}

    async def add_server(self, config: MCPServerConfig) -> bool:
        """Add and connect to an MCP server"""
        if config.name in self.clients:
            logger.warning(f"MCP server {config.name} already connected")
            return False

        client = MCPClient(config)
        if await client.connect():
            self.clients[config.name] = client
            return True
        return False

    async def remove_server(self, name: str) -> bool:
        """Disconnect and remove an MCP server"""
        if name not in self.clients:
            return False

        await self.clients[name].disconnect()
        del self.clients[name]
        return True

    def get_client(self, name: str) -> Optional[MCPClient]:
        """Get an MCP client by name"""
        return self.clients.get(name)

    def list_servers(self) -> List[str]:
        """List all connected MCP servers"""
        return list(self.clients.keys())

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from all connected MCP servers"""
        all_tools = []
        for client in self.clients.values():
            all_tools.extend(client.get_available_tools())
        return all_tools

    def get_all_resources(self) -> List[Dict[str, Any]]:
        """Get all resources from all connected MCP servers"""
        all_resources = []
        for client in self.clients.values():
            all_resources.extend(client.get_available_resources())
        return all_resources

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call a tool on a specific MCP server"""
        client = self.get_client(server_name)
        if not client:
            logger.error(f"MCP server {server_name} not found")
            return None

        return await client.call_tool(tool_name, arguments)

    async def read_resource(self, server_name: str, uri: str) -> Optional[Dict[str, Any]]:
        """Read a resource from a specific MCP server"""
        client = self.get_client(server_name)
        if not client:
            logger.error(f"MCP server {server_name} not found")
            return None

        return await client.read_resource(uri)

    async def disconnect_all(self):
        """Disconnect from all MCP servers"""
        for client in list(self.clients.values()):
            await client.disconnect()
        self.clients.clear()
