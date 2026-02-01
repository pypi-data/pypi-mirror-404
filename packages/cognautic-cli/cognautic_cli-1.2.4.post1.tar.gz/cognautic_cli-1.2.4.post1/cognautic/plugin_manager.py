"""
Plugin Manager for Cognautic CLI
Handles plugin loading, registration, and lifecycle management
"""

import os
import sys
import json
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadata for a plugin"""
    name: str
    version: str
    description: str
    author: str
    entry_point: str  # Module path to the plugin class
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        return cls(**data)


class PluginAPI:
    """
    API interface provided to plugins
    Provides access to Cognautic CLI functionality
    """
    
    def __init__(self, cli_context: Dict[str, Any]):
        self.context = cli_context
        self._command_handlers: Dict[str, Callable] = {}
        self._tool_registry = None
        
    def register_command(self, command: str, handler: Callable, description: str = ""):
        """
        Register a new slash command
        
        Args:
            command: Command name (without the leading /)
            handler: Async function to handle the command
            description: Description of the command for help text
        """
        self._command_handlers[command] = {
            'handler': handler,
            'description': description
        }
        logger.info(f"Plugin registered command: /{command}")
    
    def get_command_handler(self, command: str) -> Optional[Callable]:
        """Get handler for a command"""
        cmd_info = self._command_handlers.get(command)
        return cmd_info['handler'] if cmd_info else None
    
    def list_commands(self) -> Dict[str, str]:
        """List all registered plugin commands"""
        return {
            cmd: info['description'] 
            for cmd, info in self._command_handlers.items()
        }
    
    def register_tool(self, tool):
        """
        Register a new tool with the tool registry
        
        Args:
            tool: Instance of BaseTool
        """
        if self._tool_registry:
            self._tool_registry.register_tool(tool)
            logger.info(f"Plugin registered tool: {tool.name}")
    
    def get_workspace(self) -> str:
        """Get current workspace path"""
        return self.context.get('current_workspace', os.getcwd())
    
    def get_provider(self) -> str:
        """Get current AI provider"""
        return self.context.get('provider', 'openai')
    
    def get_model(self) -> str:
        """Get current AI model"""
        return self.context.get('model', '')
    
    def get_config_manager(self):
        """Get the config manager instance"""
        return self.context.get('config_manager')
    
    def get_ai_engine(self):
        """Get the AI engine instance"""
        return self.context.get('ai_engine')
    
    def get_memory_manager(self):
        """Get the memory manager instance"""
        return self.context.get('memory_manager')
    
    def print(self, message: str, style: str = ""):
        """
        Print a message to the console
        
        Args:
            message: Message to print
            style: Rich style string (e.g., "bold red", "green")
        """
        from rich.console import Console
        console = Console()
        if style:
            console.print(message, style=style)
        else:
            console.print(message)
    
    async def execute_command(self, command: str) -> Any:
        """
        Execute a shell command in the current workspace
        
        Args:
            command: Shell command to execute
            
        Returns:
            Command output
        """
        import subprocess
        workspace = self.get_workspace()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except Exception as e:
            return {
                'error': str(e),
                'returncode': -1
            }
    
    async def ask_ai(self, prompt: str, **kwargs) -> str:
        """
        Send a prompt to the AI engine and get a response
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments (provider, model, etc.)
            
        Returns:
            AI response text
        """
        ai_engine = self.get_ai_engine()
        if not ai_engine:
            raise RuntimeError("AI engine not available")
        
        provider = kwargs.get('provider', self.get_provider())
        model = kwargs.get('model', self.get_model())
        workspace = kwargs.get('workspace', self.get_workspace())
        
        response = ""
        async for chunk in ai_engine.process_message_stream(
            prompt,
            provider=provider,
            model=model,
            project_path=workspace,
            conversation_history=[]
        ):
            response += chunk
        
        return response


class BasePlugin(ABC):
    """
    Base class for all Cognautic plugins
    
    Plugins should inherit from this class and implement the required methods
    """
    
    def __init__(self, api: PluginAPI):
        self.api = api
        self.name = "base_plugin"
        self.version = "0.0.0"
        self.description = "Base plugin"
    
    @abstractmethod
    async def on_load(self):
        """
        Called when the plugin is loaded
        Use this to register commands, tools, etc.
        """
        pass
    
    async def on_unload(self):
        """
        Called when the plugin is unloaded
        Use this to cleanup resources
        """
        pass
    
    async def on_message(self, message: str, role: str) -> Optional[str]:
        """
        Called when a message is sent or received
        Can intercept and modify messages
        
        Args:
            message: The message content
            role: The role (user/assistant)
            
        Returns:
            Modified message or None to leave unchanged
        """
        return None


class PluginManager:
    """Manages plugin lifecycle and registration"""
    
    def __init__(self, plugins_dir: Optional[str] = None):
        self.plugins_dir = plugins_dir or str(Path.home() / ".cognautic" / "plugins")
        self.installed_plugins: Dict[str, Dict[str, Any]] = {}
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self.plugin_api: Optional[PluginAPI] = None
        
        # Create plugins directory if it doesn't exist
        Path(self.plugins_dir).mkdir(parents=True, exist_ok=True)
        
        # Load plugin registry
        self._load_registry()
    
    def _get_registry_path(self) -> Path:
        """Get path to plugin registry file"""
        return Path(self.plugins_dir) / "registry.json"
    
    def _load_registry(self):
        """Load plugin registry from disk"""
        registry_path = self._get_registry_path()
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    data = json.load(f)
                    self.installed_plugins = data.get('plugins', {})
            except Exception as e:
                logger.error(f"Failed to load plugin registry: {e}")
                self.installed_plugins = {}
    
    def _save_registry(self):
        """Save plugin registry to disk"""
        registry_path = self._get_registry_path()
        try:
            with open(registry_path, 'w') as f:
                json.dump({'plugins': self.installed_plugins}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save plugin registry: {e}")
    
    def initialize_api(self, cli_context: Dict[str, Any]):
        """Initialize the plugin API with CLI context"""
        self.plugin_api = PluginAPI(cli_context)
        
        # Set tool registry reference if available
        if 'tool_registry' in cli_context:
            self.plugin_api._tool_registry = cli_context['tool_registry']
    
    async def install_plugin(self, plugin_path: str) -> bool:
        """
        Install a plugin from a directory or file and auto-load it
        
        Args:
            plugin_path: Path to plugin directory or plugin.json file
            
        Returns:
            True if installation successful
        """
        plugin_path = Path(plugin_path).resolve()
        
        # Check if path exists
        if not plugin_path.exists():
            logger.error(f"Plugin path does not exist: {plugin_path}")
            return False
        
        # If it's a file, assume it's plugin.json
        if plugin_path.is_file():
            if plugin_path.name != "plugin.json":
                logger.error("Plugin file must be named 'plugin.json'")
                return False
            plugin_dir = plugin_path.parent
        else:
            plugin_dir = plugin_path
        
        # Load plugin metadata
        metadata_file = plugin_dir / "plugin.json"
        if not metadata_file.exists():
            logger.error(f"No plugin.json found in {plugin_dir}")
            return False
        
        try:
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
                metadata = PluginMetadata.from_dict(metadata_dict)
        except Exception as e:
            logger.error(f"Failed to load plugin metadata: {e}")
            return False
        
        # Check if plugin already installed
        if metadata.name in self.installed_plugins:
            logger.warning(f"Plugin '{metadata.name}' is already installed")
            # Update the path
            self.installed_plugins[metadata.name]['path'] = str(plugin_dir)
            self._save_registry()
            # Reload if already loaded
            if metadata.name in self.loaded_plugins:
                await self.unload_plugin(metadata.name)
                await self.load_plugin(metadata.name)
            return True
        
        # Install plugin
        self.installed_plugins[metadata.name] = {
            'metadata': metadata.to_dict(),
            'path': str(plugin_dir),
            'enabled': True
        }
        
        self._save_registry()
        logger.info(f"Plugin '{metadata.name}' installed successfully")
        
        # Auto-load the plugin if API is initialized
        if self.plugin_api:
            await self.load_plugin(metadata.name)
        
        return True
    
    def uninstall_plugin(self, plugin_name: str) -> bool:
        """
        Uninstall a plugin
        
        Args:
            plugin_name: Name of the plugin to uninstall
            
        Returns:
            True if uninstallation successful
        """
        if plugin_name not in self.installed_plugins:
            logger.error(f"Plugin '{plugin_name}' is not installed")
            return False
        
        # Unload if loaded
        if plugin_name in self.loaded_plugins:
            # We can't await here easily as uninstall is sync, but we should try
            # For now, just remove from loaded_plugins to avoid errors
            # Ideally uninstall_plugin should be async too
            del self.loaded_plugins[plugin_name]
        
        # Remove from registry
        del self.installed_plugins[plugin_name]
        self._save_registry()
        
        logger.info(f"Plugin '{plugin_name}' uninstalled successfully")
        return True
    
    async def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a plugin into memory
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            True if loading successful
        """
        if plugin_name not in self.installed_plugins:
            logger.error(f"Plugin '{plugin_name}' is not installed")
            return False
        
        if plugin_name in self.loaded_plugins:
            logger.warning(f"Plugin '{plugin_name}' is already loaded")
            return True
        
        if not self.plugin_api:
            logger.error("Plugin API not initialized")
            return False
        
        plugin_info = self.installed_plugins[plugin_name]
        plugin_dir = Path(plugin_info['path'])
        metadata = PluginMetadata.from_dict(plugin_info['metadata'])
        
        try:
            # Add plugin directory to Python path
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))
            
            # Import the plugin module
            entry_point = metadata.entry_point
            
            # Handle different entry point formats
            if '.' in entry_point:
                module_name, class_name = entry_point.rsplit('.', 1)
            else:
                module_name = entry_point
                class_name = 'Plugin'
            
            # Load the module
            spec = importlib.util.spec_from_file_location(
                module_name,
                plugin_dir / f"{module_name}.py"
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Get the plugin class
                if hasattr(module, class_name):
                    plugin_class = getattr(module, class_name)
                    
                    # Instantiate the plugin
                    plugin_instance = plugin_class(self.plugin_api)
                    
                    # Call on_load
                    import asyncio
                    if asyncio.iscoroutinefunction(plugin_instance.on_load):
                        await plugin_instance.on_load()
                    else:
                        plugin_instance.on_load()
                    
                    self.loaded_plugins[plugin_name] = plugin_instance
                    logger.info(f"Plugin '{plugin_name}' loaded successfully")
                    return True
                else:
                    logger.error(f"Plugin class '{class_name}' not found in module")
                    return False
            else:
                logger.error(f"Failed to load plugin module: {module_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load plugin '{plugin_name}': {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin from memory
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if unloading successful
        """
        if plugin_name not in self.loaded_plugins:
            logger.warning(f"Plugin '{plugin_name}' is not loaded")
            return True
        
        try:
            plugin = self.loaded_plugins[plugin_name]
            
            # Call on_unload
            import asyncio
            if asyncio.iscoroutinefunction(plugin.on_unload):
                await plugin.on_unload()
            else:
                plugin.on_unload()
            
            del self.loaded_plugins[plugin_name]
            logger.info(f"Plugin '{plugin_name}' unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin '{plugin_name}': {e}")
            return False
    
    async def load_all_plugins(self):
        """Load all enabled plugins"""
        for plugin_name, plugin_info in self.installed_plugins.items():
            if plugin_info.get('enabled', True):
                await self.load_plugin(plugin_name)
    
    def list_installed_plugins(self) -> List[Dict[str, Any]]:
        """List all installed plugins"""
        result = []
        for plugin_name, plugin_info in self.installed_plugins.items():
            metadata = PluginMetadata.from_dict(plugin_info['metadata'])
            result.append({
                'name': metadata.name,
                'version': metadata.version,
                'description': metadata.description,
                'author': metadata.author,
                'enabled': plugin_info.get('enabled', True),
                'loaded': plugin_name in self.loaded_plugins,
                'path': plugin_info['path']
            })
        return result
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a loaded plugin instance"""
        return self.loaded_plugins.get(plugin_name)
    
    async def handle_plugin_command(self, command: str, args: List[str], context: Dict[str, Any]) -> bool:
        """
        Handle a command that might be registered by a plugin
        
        Args:
            command: Command name (without /)
            args: Command arguments
            context: CLI context
            
        Returns:
            True if command was handled by a plugin
        """
        if not self.plugin_api:
            return False
        
        handler = self.plugin_api.get_command_handler(command)
        if handler:
            try:
                await handler(args, context)
                return True
            except Exception as e:
                logger.error(f"Plugin command '{command}' failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        return False
    
    async def on_message_hook(self, message: str, role: str) -> str:
        """
        Call on_message hook for all loaded plugins
        Allows plugins to intercept and modify messages
        
        Args:
            message: The message content
            role: The role (user/assistant)
            
        Returns:
            Modified message (or original if no plugin modified it)
        """
        modified_message = message
        
        for plugin in self.loaded_plugins.values():
            try:
                result = await plugin.on_message(modified_message, role)
                if result is not None:
                    modified_message = result
            except Exception as e:
                logger.error(f"Plugin message hook failed: {e}")
        
        return modified_message
