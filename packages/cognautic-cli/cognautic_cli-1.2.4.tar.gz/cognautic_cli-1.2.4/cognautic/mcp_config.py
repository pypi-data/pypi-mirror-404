"""
MCP Configuration Manager
Handles loading and saving MCP server configurations
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .mcp_client import MCPServerConfig, MCPTransportType

logger = logging.getLogger(__name__)


class MCPConfigManager:
    """
    Manages MCP server configurations
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".cognautic"
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "mcp_servers.json"
        self.servers: Dict[str, MCPServerConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """Load MCP server configurations from file"""
        if not self.config_file.exists():
            logger.info("No MCP server configuration found, creating default")
            self._create_default_config()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            for name, config in data.get("servers", {}).items():
                transport = MCPTransportType(config.get("transport", "stdio"))
                self.servers[name] = MCPServerConfig(
                    name=name,
                    command=config.get("command", ""),
                    args=config.get("args", []),
                    env=config.get("env", {}),
                    transport=transport,
                    url=config.get("url")
                )
            
            logger.info(f"Loaded {len(self.servers)} MCP server configurations")
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default MCP server configuration"""
        default_config = {
            "servers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(Path.home())],
                    "env": {},
                    "transport": "stdio",
                    "description": "Access files and directories on the local filesystem"
                },
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": ""
                    },
                    "transport": "stdio",
                    "description": "Interact with GitHub repositories"
                },
                "postgres": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-postgres"],
                    "env": {
                        "POSTGRES_CONNECTION_STRING": ""
                    },
                    "transport": "stdio",
                    "description": "Query PostgreSQL databases"
                }
            },
            "enabled": []
        }
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Created default MCP configuration at {self.config_file}")
    
    def save_config(self):
        """Save current MCP server configurations to file"""
        try:
            data = {"servers": {}, "enabled": []}
            
            for name, config in self.servers.items():
                data["servers"][name] = {
                    "command": config.command,
                    "args": config.args,
                    "env": config.env,
                    "transport": config.transport.value,
                    "url": config.url
                }
            
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Saved MCP configuration")
        except Exception as e:
            logger.error(f"Error saving MCP config: {e}")
    
    def add_server(self, config: MCPServerConfig):
        """Add a new MCP server configuration"""
        self.servers[config.name] = config
        self.save_config()
    
    def remove_server(self, name: str) -> bool:
        """Remove an MCP server configuration"""
        if name in self.servers:
            del self.servers[name]
            self.save_config()
            return True
        return False
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get an MCP server configuration by name"""
        return self.servers.get(name)
    
    def list_servers(self) -> List[str]:
        """List all configured MCP servers"""
        return list(self.servers.keys())
    
    def get_all_servers(self) -> Dict[str, MCPServerConfig]:
        """Get all MCP server configurations"""
        return self.servers.copy()
