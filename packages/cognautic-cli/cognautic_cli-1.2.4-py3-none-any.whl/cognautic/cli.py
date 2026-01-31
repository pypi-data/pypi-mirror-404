"""
Main CLI interface for Cognautic
"""

import click
import asyncio
import logging
import os
import readline
import signal
from pathlib import Path
import sys
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import Completer, Completion
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.columns import Columns
import threading
import queue
from typing import Optional

# Suppress verbose logging from Google AI and other libraries
os.environ['GRPC_VERBOSITY'] = 'NONE'
os.environ['GRPC_TRACE'] = ''
os.environ['GLOG_minloglevel'] = '3'  # Suppress all Google logging
os.environ['GLOG_logtostderr'] = '0'  # Don't log to stderr
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logs
os.environ['ABSL_LOGGING_VERBOSITY'] = '3'  # Suppress ABSL logs

# Redirect stderr to suppress C++ library logs
import sys
import io

# Create a custom stderr that filters out Google AI noise
class FilteredStderr:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = ""
    
    def write(self, text):
        # Filter out Google AI error messages
        if any(pattern in text for pattern in [
            'ALTS creds ignored',
            'plugin_credentials.cc',
            'validate_metadata_from_plugin',
            'Plugin added invalid metadata',
            'All log messages before absl::InitializeLog',
            'INTERNAL:Illegal header value'
        ]):
            return
        self.original_stderr.write(text)
    
    def flush(self):
        self.original_stderr.flush()
    
    def isatty(self):
        return self.original_stderr.isatty()

    def __getattr__(self, name):
        return getattr(self.original_stderr, name)

    @property
    def encoding(self):
        return getattr(self.original_stderr, 'encoding', 'utf-8')

    @property
    def errors(self):
        return getattr(self.original_stderr, 'errors', None)

    def fileno(self):
        return self.original_stderr.fileno()

    def writable(self):
        return True

    def readable(self):
        return False

    def seekable(self):
        return False

    def close(self):
        try:
            self.original_stderr.close()
        except Exception:
            pass

# Install the filtered stderr
sys.stderr = FilteredStderr(sys.stderr)

logging.getLogger('google').setLevel(logging.CRITICAL)
logging.getLogger('google.generativeai').setLevel(logging.CRITICAL)
logging.getLogger('websockets').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.getLogger('grpc').setLevel(logging.CRITICAL)

# Set root logger to WARNING to suppress debug messages
logging.basicConfig(level=logging.WARNING)

from .config import ConfigManager
from .ai_engine import AIEngine
from .websocket_server import WebSocketServer
from .memory import MemoryManager
from .rules import RulesManager
from .confirmation import ConfirmationManager
from . import __version__ as __cli_version__
from .voice_input import transcribe_once
from .mcp_commands import handle_mcp_command
from .utils import is_restricted_directory
from .repo_documenter import document_repository
from .multi_agent import MultiAgentOrchestrator, AgentConfig

console = Console()


def _show_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"Cognautic CLI, version {__cli_version__}")
    ctx.exit()

class SlashCommandCompleter(Completer):
    """Auto-completer for slash commands"""
    
    def __init__(self, workspace: Optional[str] = None):
        self.workspace = workspace or os.getcwd()
        self.commands = {
            '/help': 'Show help information',
            '/workspace': 'Change working directory (alias: /ws)',
            '/ws': 'Change working directory',
            '/setup': 'Run interactive setup wizard',
            '/config': 'Manage configuration',
            '/provider': 'Switch AI provider',
            '/model': 'Switch AI model',
            '/models': 'Fetch available models from provider',
            '/endpoint': 'Set provider endpoint/base URL',
            '/lmodel': 'Load local Hugging Face model',
            '/session': 'Manage chat sessions',
            '/speed': 'Set typing speed',
            '/yolo': 'Toggle YOLO mode (skip confirmations)',
            '/askq': 'Toggle ask question mode (AI can ask clarifying questions)',
            '/voice': 'Capture voice and prefill prompt',
            '/editor': 'Open vim editor for file editing',
            '/mml': 'Enable multi-model mode with specified providers/models',
            '/qmml': 'Quit multi-model mode',
            '/multiagent': 'Multi-agent collaboration mode (agents discuss, plan, then work together)',
            '/index': 'Show codebase index status',
            '/ps': 'List all running background processes',
            '/processes': 'List all running background processes',
            '/ct': 'Terminate a background process',
            '/cancel': 'Terminate a background process',
            '/clear': 'Clear chat screen',
            '/exit': 'Exit chat session',
            '/quit': 'Exit chat session',
            '/mcp': 'Manage MCP server connections',
            '/mcp-list': 'List connected MCP servers',
            '/mcp-connect': 'Connect to an MCP server',
            '/mcp-disconnect': 'Disconnect from an MCP server',
            '/mcp-tools': 'List tools from MCP servers',
            '/mcp-resources': 'List resources from MCP servers',
            '/plugin': 'Manage plugins (install, list, load, unload)',
            '/docrepo': 'Generate documentation for a git repository',
        }
    
    def set_workspace(self, workspace: str):
        if workspace:
            self.workspace = workspace
    
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        # Only show completions if the line starts with /
        if text.startswith('/'):
            word = text.split()[-1] if text.split() else text
            for cmd, description in self.commands.items():
                if cmd.startswith(word):
                    yield Completion(
                        cmd,
                        start_position=-len(word),
                        display=cmd,
                        display_meta=description
                    )
            return
        
        at_idx = text.rfind('@')
        if at_idx != -1:
            fragment = text[at_idx + 1:]
            if not any(c.isspace() for c in fragment):
                typed_path = fragment
                import os as _os
                typed_dir, typed_base = _os.path.split(typed_path)
                if typed_dir in ('', '.'):  # relative to workspace
                    fs_dir = self.workspace
                else:
                    expanded_dir = _os.path.expanduser(typed_dir)
                    if not _os.path.isabs(expanded_dir):
                        fs_dir = _os.path.normpath(_os.path.join(self.workspace, expanded_dir))
                    else:
                        fs_dir = expanded_dir
                if typed_path.endswith('/'):
                    base_dir_candidate = _os.path.expanduser(typed_path)
                    if not _os.path.isabs(base_dir_candidate):
                        fs_dir = _os.path.normpath(_os.path.join(self.workspace, base_dir_candidate))
                    else:
                        fs_dir = base_dir_candidate
                    typed_dir, typed_base = typed_path, ''
                try:
                    for name in sorted(_os.listdir(fs_dir)):
                        if not name.startswith(typed_base):
                            continue
                        full_path = _os.path.join(fs_dir, name)
                        is_dir = _os.path.isdir(full_path)
                        insertion_relative = name if typed_dir in ('', '.') else _os.path.join(typed_dir, name)
                        insertion_text = '@' + (insertion_relative + ('/' if is_dir else ''))
                        display_text = insertion_relative + ('/' if is_dir else '')
                        yield Completion(
                            insertion_text,
                            start_position=-(len(text) - at_idx),
                            display=display_text,
                            display_meta=('dir' if is_dir else 'file')
                        )
                except Exception:
                    pass

@click.group(invoke_without_command=True)
@click.option('-v', is_flag=True, is_eager=True, expose_value=False, callback=_show_version, help='Show the version and exit.')
@click.version_option(version=__cli_version__, prog_name="Cognautic CLI")
@click.pass_context
def main(ctx):
    """Cognautic CLI - AI-powered development assistant"""
    if ctx.invoked_subcommand is None:
        # No subcommand provided, start interactive chat
        ctx.invoke(chat)

@main.command()
@click.option('--provider', help='AI provider to configure')
@click.option('--api-key', help='API key for the provider')
@click.option('--interactive', is_flag=True, help='Interactive setup mode')
def setup(provider, api_key, interactive):
    """Initialize Cognautic CLI and configure API keys"""
    console.print(Panel.fit("🚀 Cognautic CLI Setup", style="bold blue"))
    
    config_manager = ConfigManager()
    
    if interactive:
        config_manager.interactive_setup()
    elif provider and api_key:
        config_manager.set_api_key(provider, api_key)
        console.print(f"SUCCESS: API key for {provider} configured successfully", style="green")
    else:
        console.print("ERROR: Please provide --provider and --api-key, or use --interactive", style="red")

@main.command()
@click.option('--provider', help='AI provider to use')
@click.option('--model', help='Specific model to use')
@click.option('--project-path', type=click.Path(exists=True), help='Project path to work with')
@click.option('--websocket-port', default=8765, help='WebSocket server port')
@click.option('--session', help='Session ID to continue')
def chat(provider, model, project_path, websocket_port, session):
    """Start interactive chat session with AI agent"""
    ascii_art = """
 ██████╗ ██████╗  ██████╗ ███╗   ██╗ █████╗ ██╗   ██╗████████╗██╗ ██████╗
██╔════╝██╔═══██╗██╔════╝ ████╗  ██║██╔══██╗██║   ██║╚══██╔══╝██║██╔════╝
██║     ██║   ██║██║  ███╗██╔██╗ ██║███████║██║   ██║   ██║   ██║██║     
██║     ██║   ██║██║   ██║██║╚██╗██║██╔══██║██║   ██║   ██║   ██║██║     
╚██████╗╚██████╔╝╚██████╔╝██║ ╚████║██║  ██║╚██████╔╝   ██║   ██║╚██████╗
 ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝ ╚═════╝
"""
    console.print(ascii_art, style="bold green")
    
    # Handle Sentinel objects from Click
    if not isinstance(provider, str):
        provider = None
    if not isinstance(model, str):
        model = None
    if not isinstance(project_path, (str, type(None))):
        project_path = None
    if not isinstance(session, str):
        session = None
    
    config_manager = ConfigManager()
    memory_manager = MemoryManager()
    
    # Determine available providers: configured (with API keys) + no-auth providers (e.g., ollama)
    from .provider_endpoints import get_all_providers, get_provider_config
    configured_providers = config_manager.list_providers()
    no_auth_providers = [
        p for p in get_all_providers()
        if get_provider_config(p).get('no_auth', False)
    ]
    combined_providers = sorted(set(configured_providers) | set(no_auth_providers))
    
    # If none at all, run setup to configure at least one API-key provider
    if not combined_providers:
        console.print("🔧 No providers available. Let's set up Cognautic CLI first!", style="yellow")
        config_manager.interactive_setup()
        configured_providers = config_manager.list_providers()
        # Recompute combined providers after setup
        no_auth_providers = [
            p for p in get_all_providers()
            if get_provider_config(p).get('no_auth', False)
        ]
        combined_providers = sorted(set(configured_providers) | set(no_auth_providers))
        if not combined_providers:
            console.print("ERROR: Setup cancelled. No providers available.", style="red")
            return
    
    # Handle session loading
    if session:
        if memory_manager.load_session(session):
            current_session = memory_manager.get_current_session()
            if not provider:
                provider = current_session.provider
            if not model:
                model = current_session.model
            if not project_path:
                project_path = current_session.workspace
        else:
            return
    
    # Use provided provider or last used provider or default
    if not provider or not isinstance(provider, str):
        provider = (
            config_manager.get_config_value('last_provider')
            or config_manager.get_config_value('default_provider')
            or (combined_providers[0] if combined_providers else None)
        )
    
    # Enforce API key only for providers that require it; fallback to a valid provider if possible
    prov_cfg = get_provider_config(provider) if isinstance(provider, str) else {}
    requires_key = not prov_cfg.get('no_auth', False)
    if requires_key and not config_manager.has_api_key(provider):
        # Try to fallback to a no-auth provider or any configured provider with a key
        fallback_providers = []
        for p in combined_providers:
            cfg = get_provider_config(p)
            if cfg.get('no_auth', False) or config_manager.has_api_key(p):
                fallback_providers.append(p)
        # Remove the invalid current provider if present
        fallback_providers = [p for p in fallback_providers if p != provider]
        if fallback_providers:
            new_provider = fallback_providers[0]
            console.print(
                f"WARNING: No API key for '{provider}'. Falling back to '{new_provider}'.",
                style="yellow",
            )
            provider = new_provider
        else:
            console.print(
                f"ERROR: No API key found for {provider}. Available providers: {', '.join(combined_providers)}",
                style="red",
            )
            return
    
    # Load saved model for the provider if no model was specified
    if not model or not isinstance(model, str):
        saved_model = config_manager.get_provider_model(provider)
        if saved_model:
            model = saved_model
    
    ai_engine = AIEngine(config_manager)
    
    # Start WebSocket server in background
    websocket_server = WebSocketServer(ai_engine, port=websocket_port)
    
    async def run_chat():
        # Start WebSocket server
        server_task = asyncio.create_task(websocket_server.start())
        
        # Track last Ctrl+C time for double-tap detection
        import time
        last_ctrl_c_time = [0]  # Use list to make it mutable in nested function
        
        try:
            console.print("INFO: Type '/help' for commands, or press Ctrl+C twice to exit")
            console.print("INFO: Press Enter to send, Alt+Enter for new line")
            console.print("INFO: Press Shift+Tab to toggle Terminal mode")
            if project_path:
                console.print(f"DIR: Working in: {project_path}")
            
            # Only show session info if continuing an existing session
            if memory_manager.get_current_session():
                current_session = memory_manager.get_current_session()
                console.print(f"SESSION: Continuing session: {current_session.session_id} - {current_session.title}")
                # Show recent conversation history
                history = memory_manager.get_conversation_history(limit=3)
                if history:
                    console.print("\n[dim]Recent conversation:[/dim]")
                    for msg in history[-3:]:
                        role_color = "cyan" if msg.role == "user" else "magenta"
                        console.print(f"[{role_color}]{msg.role.title()}:[/{role_color}] {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
            
            console.print("-" * 50)
            
            # Set workspace - use provided project_path or current working directory
            current_workspace = project_path or os.getcwd()
            
            # Validate that the workspace is not a restricted directory
            is_restricted, restriction_reason = is_restricted_directory(current_workspace)
            if is_restricted:
                console.print(f"ERROR: {restriction_reason}", style="bold red")
                console.print("INFO: Please navigate to a specific project directory and try again.", style="yellow")
                return
            
            # Load saved provider/model from config if not specified
            saved_provider = config_manager.get_config_value('last_provider')
            saved_model = config_manager.get_config_value('last_model')
            
            current_model = model or saved_model  # Track current model in this scope
            current_provider = provider or saved_provider or 'openai'  # Track current provider in this scope
            
            # Multi-model mode state
            multi_model_mode = False
            multi_model_configs = []  # List of (provider, model) tuples
            multi_model_folders = {}  # Map of model names to folder paths
            original_workspace = current_workspace  # Store original workspace for restoration
            
            # Multi-agent collaboration mode state
            multiagent_mode = False
            multiagent_configs = []  # List of AgentConfig objects
            multiagent_orchestrator = None  # MultiAgentOrchestrator instance
            
            session_created = False  # Track if session has been created
            
            # Check if indexing is needed (but don't block on it)
            from .codebase_indexer import CodebaseIndexer
            indexer = CodebaseIndexer(current_workspace)
            needs_indexing = indexer.needs_reindex()
            
            # Show quick status if index exists
            if not needs_indexing:
                index = indexer.load_index()
                if index:
                    console.print(f"[dim]INFO: Codebase indexed: {index.total_files} files, {index.total_lines:,} lines[/dim]")
            else:
                console.print(f"[dim]INFO: Codebase will be indexed in background...[/dim]")
            
            # Flag to track if background indexing is running
            indexing_in_background = needs_indexing
            
            # Store the original working directory where cognautic was run
            original_cwd = os.getcwd()
            
            # Setup readline for command history and arrow keys
            history_file = Path.home() / ".cognautic" / ".chat_history"
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                readline.read_history_file(str(history_file))
            except FileNotFoundError:
                pass
            
            # Set history length
            readline.set_history_length(1000)
            
            # Show current workspace
            console.print(f"DIR: Workspace: {current_workspace}")
            
            # Terminal mode state
            terminal_mode = [False]  # Use list to make it mutable in nested function
            # Voice prefill buffer (set after Ctrl+G transcription)
            voice_prefill = [""]
            
            # Initialize confirmation manager
            confirmation_manager = ConfirmationManager()
            
            # Initialize MCP manager and config
            from .mcp_client import MCPClientManager
            from .mcp_config import MCPConfigManager
            mcp_manager = MCPClientManager()
            mcp_config = MCPConfigManager()
            
            # Initialize plugin manager
            from .plugin_manager import PluginManager
            plugin_manager = PluginManager()
            
            # Initialize plugin API early so plugins can be loaded before first message
            plugin_context = {
                'current_workspace': current_workspace,
                'model': current_model,
                'provider': current_provider,
                'memory_manager': memory_manager,
                'config_manager': config_manager,
                'ai_engine': ai_engine,
                'tool_registry': ai_engine.tool_registry if hasattr(ai_engine, 'tool_registry') else None
            }
            plugin_manager.initialize_api(plugin_context)
            
            # Load all enabled plugins at startup
            await plugin_manager.load_all_plugins()
            
            # Setup key bindings for Shift+Tab toggle and multi-line support
            bindings = KeyBindings()
            
            @bindings.add('s-tab')  # Shift+Tab
            def toggle_mode(event):
                terminal_mode[0] = not terminal_mode[0]
                mode_name = ">  Terminal" if terminal_mode[0] else " Chat"
                # Clear current line and show mode switch message
                event.app.current_buffer.text = ''
                event.app.exit(result='__MODE_TOGGLE__')
            
            @bindings.add('enter')  # Enter key submits
            def submit_message(event):
                event.current_buffer.validate_and_handle()
            
            @bindings.add('escape', 'enter')  # Meta+Enter (Alt+Enter) adds new line
            def new_line(event):
                event.current_buffer.insert_text('\n')
            
            @bindings.add('c-y')  # Ctrl+Y to toggle confirmation mode
            def toggle_confirmation(event):
                confirmation_manager.toggle_yolo_mode()
                event.app.current_buffer.text = ''
                event.app.exit(result='__CONFIRMATION_TOGGLE__')

            @bindings.add('c-g')  # Ctrl+G to capture voice input and prefill
            def toggle_voice(event):
                event.app.current_buffer.text = ''
                event.app.exit(result='__VOICE_TOGGLE__')

            @bindings.add('tab')
            def accept_or_complete(event):
                buf = event.current_buffer
                if buf.complete_state:
                    comp = buf.complete_state.current_completion
                    if comp is not None:
                        buf.apply_completion(comp)
                    else:
                        buf.complete_next()
                else:
                    buf.start_completion(select_first=True)
            
            # Create prompt session with multi-line support and command completion
            command_completer = SlashCommandCompleter(current_workspace)
            session = PromptSession(
                key_bindings=bindings,
                multiline=True,  # Allow multi-line editing
                completer=command_completer,
                complete_while_typing=True  # Show completions as you type
            )
            
            console.print("[dim]INFO: Press Shift+Tab to toggle between Chat and Terminal modes; Ctrl+G for voice input[/dim]\n")
            
            while True:
                try:
                    # Show current workspace and mode in prompt
                    workspace_info = f" [{Path(current_workspace).name}]" if current_workspace else ""
                    mode_indicator = "> " if terminal_mode[0] else ""
                    
                    prompt_text = HTML(f'<ansibrightcyan><b>{mode_indicator}You{workspace_info}:</b></ansibrightcyan> ')
                    user_input = await session.prompt_async(
                        prompt_text,
                        default=voice_prefill[0] if voice_prefill[0] else ""
                    )
                    
                    # Handle mode toggle
                    if user_input == '__MODE_TOGGLE__':
                        mode_name = ">  Terminal" if terminal_mode[0] else ">  Chat"
                        console.print(f"[bold yellow]Switched to {mode_name} mode[/bold yellow]")
                        console.print("[dim]Press Shift+Tab to toggle modes[/dim]")
                        continue
                    
                    # Handle confirmation mode toggle
                    if user_input == '__CONFIRMATION_TOGGLE__':
                        confirmation_manager.display_mode_status()
                        continue
                    
                    # Handle voice input toggle (one-shot transcription)
                    if user_input == '__VOICE_TOGGLE__':
                        console.print("[dim]Listening... Speak now[/dim]")
                        try:
                            text = await asyncio.to_thread(transcribe_once)
                            voice_prefill[0] = text
                            preview = text[:120] + ("..." if len(text) > 120 else "")
                            console.print(f"[green]Voice captured[/green]: {preview}")
                        except Exception as e:
                            console.print(f"[red]Voice input failed:[/red] {e}")
                        continue
                    
                    if user_input.lower() in ['exit', 'quit']:
                        break
                    
                    # Clear voice prefill after a normal input is accepted
                    if voice_prefill[0]:
                        voice_prefill[0] = ""
                    
                    # Handle terminal mode
                    if terminal_mode[0]:
                        if not user_input.strip():
                            continue
                        
                        # Execute command in terminal mode with live output
                        try:
                            # Run command with live output streaming
                            process = subprocess.Popen(
                                user_input,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                cwd=current_workspace,
                                bufsize=1,  # Line buffered
                                universal_newlines=True
                            )
                            
                            # Stream output in real-time
                            import select
                            import time
                            
                            try:
                                while True:
                                    # Check if process has finished
                                    if process.poll() is not None:
                                        # Read any remaining output
                                        remaining_stdout = process.stdout.read()
                                        remaining_stderr = process.stderr.read()
                                        if remaining_stdout:
                                            console.print(remaining_stdout, end='')
                                        if remaining_stderr:
                                            console.print(f"[red]{remaining_stderr}[/red]", end='')
                                        break
                                    
                                    # Read stdout
                                    stdout_line = process.stdout.readline()
                                    if stdout_line:
                                        console.print(stdout_line, end='')
                                    
                                    # Read stderr
                                    stderr_line = process.stderr.readline()
                                    if stderr_line:
                                        console.print(f"[red]{stderr_line}[/red]", end='')
                                    
                                    # Small sleep to prevent busy waiting
                                    if not stdout_line and not stderr_line:
                                        time.sleep(0.01)
                                
                                # Wait for process to complete
                                returncode = process.wait()
                                
                                # Show exit code if non-zero
                                if returncode != 0:
                                    console.print(f"[yellow]Exit code: {returncode}[/yellow]")
                                    
                            except KeyboardInterrupt:
                                # Handle Ctrl+C - terminate the process but don't exit CLI
                                console.print("\n[yellow]^C[/yellow]")
                                process.terminate()
                                try:
                                    process.wait(timeout=2)
                                except subprocess.TimeoutExpired:
                                    process.kill()
                                    process.wait()
                                console.print("[yellow]Process terminated[/yellow]")
                            
                        except Exception as e:
                            console.print(f"[red]Error executing command: {str(e)}[/red]")
                        
                        continue
                    
                    # Handle slash commands
                    if user_input.startswith('/'):
                        # Create context dict for slash commands
                        context = {
                            'current_workspace': current_workspace,
                            'model': current_model,
                            'provider': current_provider,
                            'memory_manager': memory_manager,
                            'original_cwd': original_cwd,
                            'config_manager': config_manager,
                            'confirmation_manager': confirmation_manager,
                            'multi_model_mode': multi_model_mode,
                            'multi_model_configs': multi_model_configs,
                            'multi_model_folders': multi_model_folders,
                            'multiagent_mode': multiagent_mode,
                            'multiagent_configs': multiagent_configs,
                            'multiagent_orchestrator': multiagent_orchestrator,
                            'original_workspace': original_workspace,
                            'mcp_manager': mcp_manager,
                            'mcp_config': mcp_config,
                            'ai_engine': ai_engine,
                            'plugin_manager': plugin_manager
                        }
                        result = await handle_slash_command(user_input, config_manager, ai_engine, context)
                        if result:
                            # Update local variables from context
                            old_workspace = current_workspace
                            current_workspace = context.get('current_workspace', current_workspace)
                            current_model = context.get('model', current_model)
                            current_provider = context.get('provider', current_provider)
                            multi_model_mode = context.get('multi_model_mode', multi_model_mode)
                            multi_model_configs = context.get('multi_model_configs', multi_model_configs)
                            multi_model_folders = context.get('multi_model_folders', multi_model_folders)
                            multiagent_mode = context.get('multiagent_mode', multiagent_mode)
                            multiagent_configs = context.get('multiagent_configs', multiagent_configs)
                            multiagent_orchestrator = context.get('multiagent_orchestrator', multiagent_orchestrator)
                            
                            if old_workspace != current_workspace:
                                if memory_manager.get_current_session():
                                    memory_manager.update_session_info(workspace=current_workspace)
                                command_completer.set_workspace(current_workspace)
                            
                            # Propagate voice prefill from slash command (e.g., /voice)
                            if 'voice_prefill' in context:
                                voice_prefill[0] = context['voice_prefill'] or ""
                            
                            continue
                        else:
                            break
                    
                    # Create session only when user sends first actual message (not slash command)
                    if not session_created and not memory_manager.get_current_session():
                        session_id = memory_manager.create_session(
                            provider=current_provider,
                            model=current_model,
                            workspace=current_workspace
                        )
                        session_created = True
                        console.print(f"SUCCESS: Created new session: {session_id[:8]} - Chat Session {session_id[:8]}")
                        
                        # Generate title from first message
                        title = memory_manager.generate_session_title(user_input)
                        memory_manager.update_session_info(title=title)
                        
                        # Start background indexing if needed (after first message to not delay startup)
                        if indexing_in_background:
                            
                            def index_in_background():
                                try:
                                    console.print("\n[dim]📚 Indexing codebase in background...[/dim]")
                                    index = indexer.index(lambda c, t, f: None)
                                    indexer.save_index(index)
                                    stats = indexer.get_stats(index)
                                    console.print(f"\n[dim]✓ Indexed {stats['total_files']} files, {stats['total_lines']:,} lines[/dim]")
                                except Exception as e:
                                    console.print(f"\n[dim]⚠ Indexing failed: {e}[/dim]")
                            
                            index_thread = threading.Thread(target=index_in_background, daemon=True)
                            index_thread.start()
                            indexing_in_background = False
                    
                    # Check if multiagent mode is active
                    multiagent_mode = context.get('multiagent_mode', False) if 'context' in locals() else False
                    multiagent_orchestrator = context.get('multiagent_orchestrator') if 'context' in locals() else None
                    
                    # Process user input with AI (including conversation history)
                    if multiagent_mode and multiagent_orchestrator:
                        # Multi-agent collaboration mode
                        console.print("\n[bold cyan]🤖 Starting Multi-Agent Collaboration[/bold cyan]\n")
                        
                        try:
                            # Run the collaboration workflow
                            await multiagent_orchestrator.run_collaboration(user_input)
                            
                            # Disable multiagent mode after completion
                            if 'context' in locals():
                                context['multiagent_mode'] = False
                                context['multiagent_orchestrator'] = None
                            
                            # Skip normal processing
                            continue
                            
                        except Exception as e:
                            console.print(f"[red]Error during multi-agent collaboration: {e}[/red]")
                            import traceback
                            console.print(f"[dim]{traceback.format_exc()}[/dim]")
                            
                            # Disable multiagent mode on error
                            if 'context' in locals():
                                context['multiagent_mode'] = False
                                context['multiagent_orchestrator'] = None
                            continue
                    
                    elif multi_model_mode:
                        # Multi-model mode: process with all configured models
                        console.print(f"[dim]Processing with {len(multi_model_configs)} models in parallel...[/dim]")
                        
                        # Get conversation history for context
                        conversation_history = memory_manager.get_context_for_ai(limit=10)
                        
                        # Side-by-side concurrent streaming using Live Columns with threaded producers
                        async def consume_queue(display_name, q, buffers):
                            response = ""
                            while True:
                                chunk = await asyncio.to_thread(q.get)
                                if chunk is sentinel:
                                    break
                                response += chunk
                                buffers[display_name] = response
                            return response
                        
                        # Disable Ctrl+C during AI responses
                        import signal
                        original_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
                        
                        try:
                            # Prepare buffers and tasks for concurrent streaming
                            all_responses = []
                            import re
                            model_buffers = {}
                            display_names = []
                            tasks = []
                            model_queues = {}
                            # unique sentinel to signal end of stream per model
                            sentinel = object()
                            # Fixed column widths to avoid layout shifts
                            term_width = console.size.width
                            num_cols = max(1, len(multi_model_configs))
                            gap = 3
                            col_width = max(20, int((term_width - (num_cols - 1) * gap) / num_cols))
                            for provider_name, model_name in multi_model_configs:
                                safe_model_name = re.sub(r'[/:\\<>|"?*]', '_', model_name) if model_name else provider_name
                                folder_key = f"{provider_name}_{safe_model_name}"
                                model_folder = multi_model_folders.get(folder_key, current_workspace)
                                display_name = f"{provider_name}:{model_name}" if model_name else provider_name
                                display_names.append(display_name)
                                model_buffers[display_name] = ""
                                q = queue.Queue()
                                model_queues[display_name] = q

                                # Start background producer thread that iterates provider stream and pushes chunks
                                def _producer(p=provider_name, m=model_name, folder=model_folder, name=display_name, out_q=q):
                                    async def _run():
                                        try:
                                            async for chunk in ai_engine.process_message_stream(
                                                user_input,
                                                provider=p,
                                                model=m,
                                                project_path=folder,
                                                conversation_history=conversation_history,
                                                confirmation_manager=confirmation_manager
                                            ):
                                                out_q.put(chunk)
                                        except Exception as e:
                                            out_q.put(f"[Error] {e}")
                                        finally:
                                            out_q.put(sentinel)
                                    asyncio.run(_run())

                                threading.Thread(target=_producer, daemon=True).start()

                                # Async consumer task to drain queue and update buffers
                                tasks.append(asyncio.create_task(consume_queue(display_name, q, model_buffers)))

                            def render_columns():
                                panels = []
                                for name in display_names:
                                    content = model_buffers.get(name, "")
                                    text = Text(content, overflow="fold", no_wrap=False)
                                    panels.append(Panel(text, title=name, width=col_width))
                                return Columns(panels, equal=True, expand=False, padding=1)

                            # Live render while tasks stream concurrently
                            with Live(render_columns(), console=console, refresh_per_second=10, transient=True) as live:
                                while any(not t.done() for t in tasks):
                                    live.update(render_columns())
                                    await asyncio.sleep(0.05)
                                results = await asyncio.gather(*tasks, return_exceptions=True)
                                live.update(render_columns())
                            # Print one final static snapshot for scrollback
                            console.print(render_columns())

                            for res in results:
                                if isinstance(res, str) and res:
                                    all_responses.append(res)
                            full_response = "\n\n".join(all_responses) if all_responses else ""
                        finally:
                            # Re-enable Ctrl+C after AI responses
                            signal.signal(signal.SIGINT, original_handler)
                    else:
                        # Single model mode (original behavior)
                        console.print(f"[dim]Processing with {current_provider}, model: {current_model or 'default'}...[/dim]")
                        
                        # Get conversation history for context
                        conversation_history = memory_manager.get_context_for_ai(limit=10)
                        
                        # Add border before AI response
                        console.print("[bold magenta]─[/bold magenta]" * 50)
                        console.print("[bold magenta]AI:[/bold magenta] ", end="")
                        full_response = ""
                        
                        # Disable Ctrl+C during AI response
                        import signal
                        original_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
                        
                        try:
                            async for chunk in ai_engine.process_message_stream(
                                user_input, 
                                provider=current_provider, 
                                model=current_model,
                                project_path=current_workspace,
                                conversation_history=conversation_history,
                                confirmation_manager=confirmation_manager,
                                memory_manager=memory_manager
                            ):
                                # Display chunks immediately with minimal overhead
                                sys.stdout.write(chunk)
                                sys.stdout.flush()
                                full_response += chunk
                        finally:
                            # Re-enable Ctrl+C after AI response
                            signal.signal(signal.SIGINT, original_handler)
                        
                        console.print()  # New line after streaming
                        console.print("[bold magenta]─[/bold magenta]" * 50)  # Border after AI response
                    
                    # AI response is now automatically added to memory by process_message_stream
                    # because it handles intermediate tool turns and signatures more accurately.
                    pass
                    
                except KeyboardInterrupt:
                    # Ctrl+C pressed while waiting for user input
                    current_time = time.time()
                    time_since_last = current_time - last_ctrl_c_time[0]
                    
                    if time_since_last < 2.0:  # Double tap within 2 seconds
                        console.print("\n[yellow]Exiting...[/yellow]")
                        break
                    else:
                        # First Ctrl+C - show hint
                        console.print("\n[dim]Press Ctrl+C again within 2 seconds to exit, or type 'exit'[/dim]")
                        last_ctrl_c_time[0] = current_time
                        continue
                except Exception as e:
                    console.print(f"ERROR: {str(e)}", style="red")
        
        finally:
            # Save command history
            try:
                readline.write_history_file(str(history_file))
            except Exception:
                pass
            
            # Cleanup MCP connections
            try:
                await mcp_manager.disconnect_all()
            except Exception:
                pass
            
            server_task.cancel()
            console.print("Chat session ended")
    
    asyncio.run(run_chat())


@main.command()
@click.argument('action')
@click.argument('key', required=False)
@click.argument('value', required=False)
def config(action, key, value):
    """Manage configuration and API keys"""
    config_manager = ConfigManager()
    
    if action == 'list':
        config_data = config_manager.get_config()
        console.print_json(data=config_data)
    elif action == 'set' and key and value:
        config_manager.set_config(key, value)
        console.print(f"SUCCESS: Set {key} = {value}", style="green")
    elif action == 'get' and key:
        value = config_manager.get_config_value(key)
        console.print(f"{key} = {value}")
    elif action == 'delete' and key:
        config_manager.delete_config(key)
        console.print(f"SUCCESS: Deleted {key}", style="green")
    elif action == 'reset':
        config_manager.reset_config()
        console.print("SUCCESS: Configuration reset to defaults", style="green")
    else:
        console.print("ERROR: Invalid config action. Use: list, set <key> <value>, get <key>, delete <key>, reset", style="red")

@main.command()
def providers():
    """List all available AI providers and their endpoints"""
    from .provider_endpoints import PROVIDER_ENDPOINTS, get_all_providers
    
    console.print(Panel.fit("🤖 Available AI Providers & Endpoints", style="bold blue"))
    
    for provider_name in get_all_providers():
        config = PROVIDER_ENDPOINTS[provider_name]
        
        console.print(f"\n[bold cyan]{provider_name.upper()}[/bold cyan]")
        console.print(f"Base URL: [green]{config['base_url']}[/green]")
        
        # List endpoints
        endpoints = {k: v for k, v in config.items() if k.endswith('_endpoint')}
        if endpoints:
            console.print("Endpoints:")
            for endpoint_name, endpoint_path in endpoints.items():
                clean_name = endpoint_name.replace('_endpoint', '').replace('_', ' ').title()
                console.print(f"  • {clean_name}: [yellow]{endpoint_path}[/yellow]")
        
        # Show auth method
        if 'headers' in config:
            auth_header = None
            for key, value in config['headers'].items():
                if 'api_key' in value.lower() or 'authorization' in key.lower():
                    auth_header = f"{key}: {value}"
                    break
            if auth_header:
                console.print(f"Auth: [dim]{auth_header}[/dim]")
        
        if 'auth_param' in config:
            console.print(f"Auth: [dim]URL parameter: {config['auth_param']}[/dim]")

@main.command()
@click.argument('action', required=False)
@click.argument('rule_type', required=False)
@click.argument('args', nargs=-1, required=False)
@click.option('--workspace', '-w', help='Workspace path for workspace rules')
def rules(action, rule_type, args, workspace):
    """Manage global and workspace rules for AI behavior
    
    Examples:
        cognautic rules                                    # List all rules
        cognautic rules add global "Use type hints"       # Add global rule
        cognautic rules add workspace "Follow PEP 8" -w . # Add workspace rule
        cognautic rules remove global 0                   # Remove global rule by index
        cognautic rules clear workspace -w .              # Clear workspace rules
    """
    rules_manager = RulesManager()
    
    if not action:
        # Display all rules
        rules_manager.display_rules(workspace)
        console.print("\nINFO: Usage:")
        console.print("  cognautic rules add global <rule> [description]")
        console.print("  cognautic rules add workspace <rule> [description] -w <path>")
        console.print("  cognautic rules remove global <index>")
        console.print("  cognautic rules remove workspace <index> -w <path>")
        console.print("  cognautic rules clear global")
        console.print("  cognautic rules clear workspace -w <path>")
        return
    
    if action == "add":
        if not rule_type or not args:
            console.print("ERROR: Usage: cognautic rules add <global|workspace> <rule> [description]", style="red")
            return
        
        # Join all args as the rule text
        rule_text = " ".join(args)
        
        if rule_type == "global":
            rules_manager.add_global_rule(rule_text)
        elif rule_type == "workspace":
            if not workspace:
                workspace = os.getcwd()
            rules_manager.add_workspace_rule(rule_text, workspace_path=workspace)
        else:
            console.print("ERROR: Rule type must be 'global' or 'workspace'", style="red")
    
    elif action == "remove":
        if not rule_type or not args:
            console.print("ERROR: Usage: cognautic rules remove <global|workspace> <index>", style="red")
            return
        
        try:
            index = int(args[0])
            if rule_type == "global":
                rules_manager.remove_global_rule(index)
            elif rule_type == "workspace":
                if not workspace:
                    workspace = os.getcwd()
                rules_manager.remove_workspace_rule(index, workspace)
            else:
                console.print("❌ Rule type must be 'global' or 'workspace'", style="red")
        except (ValueError, IndexError):
            console.print("ERROR: Index must be a valid number", style="red")
    
    elif action == "clear":
        if not rule_type:
            console.print("❌ Usage: cognautic rules clear <global|workspace>", style="red")
            return
        
        if rule_type == "global":
            rules_manager.clear_global_rules()
        elif rule_type == "workspace":
            if not workspace:
                workspace = os.getcwd()
            rules_manager.clear_workspace_rules(workspace)
        else:
            console.print("ERROR: Rule type must be 'global' or 'workspace'", style="red")
    
    else:
        console.print(f"❌ Unknown action: {action}", style="red")
        console.print("Valid actions: add, remove, clear")

async def handle_slash_command(command, config_manager, ai_engine, context):
    """Handle slash commands in chat mode"""
    parts = command[1:].split()
    cmd = parts[0].lower() if parts else ""
    
    if cmd == "help":
        show_help()
        return True
    
    elif cmd == "voice":
        console.print("[dim]Listening... Speak now[/dim]")
        try:
            text = await asyncio.to_thread(transcribe_once)
            context['voice_prefill'] = text
            preview = text[:120] + ("..." if len(text) > 120 else "")
            console.print(f"[green]Voice captured[/green]: {preview}")
        except Exception as e:
            console.print(f"[red]Voice input failed:[/red] {e}")
        return True
    
    elif cmd == "workspace" or cmd == "ws":
        if len(parts) < 2:
            current = context.get('current_workspace')
            if current:
                console.print(f"DIR: Current workspace: {current}")
            else:
                console.print("DIR: No workspace set")
            console.print("Usage: /workspace <path> or /ws <path>")
        else:
            path_input = parts[1]
            
            # First expand user home directory
            new_path = Path(path_input).expanduser()
            
            # Then handle relative vs absolute paths
            if not new_path.is_absolute():
                # Relative path from original working directory
                original_cwd = context.get('original_cwd', os.getcwd())
                new_path = Path(original_cwd) / new_path
            
            # Resolve to absolute path
            new_path = new_path.resolve()
            
            if new_path.exists() and new_path.is_dir():
                # Validate that the new workspace is not a restricted directory
                is_restricted, restriction_reason = is_restricted_directory(str(new_path))
                if is_restricted:
                    console.print(f"ERROR: {restriction_reason}", style="bold red")
                    console.print("INFO: Please choose a specific project directory.", style="yellow")
                else:
                    context['current_workspace'] = str(new_path)
                    console.print(f"SUCCESS: Workspace changed to: {new_path}")
                    console.print(f"INFO: AI will now create files in this directory")
            else:
                console.print(f"ERROR: Directory not found: {new_path}", style="red")
        return True
    
    elif cmd == "setup":
        console.print("🔧 Running setup wizard...")
        config_manager.interactive_setup()
        return True
    
    elif cmd == "config":
        if len(parts) < 2:
            console.print("Available config commands:")
            console.print("• /config list - Show current configuration")
            console.print("• /config providers - Show available providers")
            console.print("• /config set <key> <value> - Set configuration value")
        elif parts[1] == "list":
            config_data = config_manager.get_config()
            console.print_json(data=config_data)
        elif parts[1] == "providers":
            providers = config_manager.list_providers()
            console.print(f"Available providers: {', '.join(providers) if providers else 'None'}")
        elif parts[1] == "set" and len(parts) >= 4:
            config_manager.set_config(parts[2], parts[3])
            console.print(f"SUCCESS: Set {parts[2]} = {parts[3]}")
        return True
    
    elif cmd == "provider":
        if len(parts) < 2:
            current_provider = context.get('provider')
            console.print(f"Current provider: {current_provider}")
            # Merge configured providers and initialized providers (e.g., no-auth like ollama)
            configured = set(config_manager.list_providers())
            initialized = set(ai_engine.get_available_providers())
            providers = sorted(configured.union(initialized))
            console.print(f"Available providers: {', '.join(providers) if providers else 'None'}")
            console.print("Usage: /provider <provider_name>")
        else:
            new_provider = parts[1]
            # Check if it's the local provider or has an API key
            if new_provider == 'local':
                # Check if local model is configured
                local_model_path = config_manager.get_config_value('local_model_path')
                if local_model_path:
                    # Load the local model if not already loaded
                    if 'local' not in ai_engine.providers:
                        try:
                            console.print(f"INFO: Loading local model from: {local_model_path}")
                            ai_engine.load_local_model(local_model_path)
                            console.print("SUCCESS: Local model loaded successfully!")
                        except Exception as e:
                            console.print(f"ERROR: Error loading local model: {e}", style="red")
                            return True
                    
                    context['provider'] = new_provider
                    current_provider = new_provider  # Update current provider
                    # Save the provider choice
                    config_manager.set_config('last_provider', new_provider)
                    # Load saved model for this provider
                    saved_model = config_manager.get_provider_model(new_provider)
                    context['model'] = saved_model
                    current_model = saved_model  # Update current model
                    console.print(f"SUCCESS: Switched to provider: {new_provider}")
                    if saved_model:
                        console.print(f"INFO: Using saved model: {saved_model}")
                else:
                    console.print("ERROR: No local model configured", style="red")
                    console.print("INFO: Use /lmodel <path> to load a local model first", style="yellow")
            elif new_provider in ai_engine.providers or config_manager.has_api_key(new_provider):
                context['provider'] = new_provider
                current_provider = new_provider  # Update current provider
                # Save the provider choice
                config_manager.set_config('last_provider', new_provider)
                # Load saved model for this provider
                saved_model = config_manager.get_provider_model(new_provider)
                context['model'] = saved_model
                current_model = saved_model  # Update current model
                console.print(f"SUCCESS: Switched to provider: {new_provider}")
                if saved_model:
                    console.print(f"INFO: Using saved model: {saved_model}")
            else:
                console.print(f"ERROR: Provider {new_provider} not configured", style="red")
                if new_provider == 'local':
                    console.print("INFO: Use /lmodel <path> to load a local model first", style="yellow")
        return True
    
    elif cmd == "model" or cmd == "models":
        current_provider = context.get('provider')
        if not current_provider:
            console.print("ERROR: No provider selected", style="red")
            return True
        
        # Check if user wants to list models (fetch from API)
        if len(parts) >= 2 and parts[1] == "list":
            console.print(f"INFO: Fetching available models from {current_provider}...")
            
            try:
                # Import API client
                from .provider_endpoints import GenericAPIClient, get_provider_config
                
                # Get API key or allow if provider doesn't require auth
                config_manager = context.get('config_manager')
                provider_config = get_provider_config(current_provider)
                no_auth = provider_config.get('no_auth', False)
                api_key = config_manager.get_api_key(current_provider) if not no_auth else ''
                if not no_auth and not api_key:
                    console.print(f"ERROR: No API key configured for {current_provider}", style="red")
                    console.print(f"INFO: Run /setup to configure your API key")
                    return True
                
                # Create API client and fetch models
                base_url_override = config_manager.get_provider_endpoint(current_provider)
                client = GenericAPIClient(current_provider, api_key or '', base_url_override)
                
                # Check if provider has models endpoint
                if 'models_endpoint' not in provider_config:
                    console.print(f"INFO: {current_provider} doesn't provide a models API endpoint")
                    console.print(f"INFO: Check the provider's documentation for available models:")
                    
                    # Show documentation links
                    docs = {
                        'openai': 'https://platform.openai.com/docs/models',
                        'anthropic': 'https://docs.anthropic.com/claude/docs/models-overview',
                        'google': 'https://ai.google.dev/gemini-api/docs/models/gemini',
                        'together': 'https://docs.together.ai/docs/inference-models',
                        'openrouter': 'https://openrouter.ai/models',
                        'groq': 'https://console.groq.com/docs/models',
                        'mistral': 'https://docs.mistral.ai/getting-started/models/',
                        'deepseek': 'https://platform.deepseek.com/api-docs/',
                        'perplexity': 'https://docs.perplexity.ai/docs/model-cards',
                        'cohere': 'https://docs.cohere.com/docs/models',
                    }
                    
                    if current_provider in docs:
                        console.print(f"   {docs[current_provider]}")
                    
                    return True
                
                # Fetch models from API
                import nest_asyncio
                
                # Allow nested event loops
                try:
                    nest_asyncio.apply()
                except:
                    pass
                
                # Try to get models
                try:
                    result = asyncio.run(client.list_models())
                except RuntimeError:
                    # If we're in an event loop, use a workaround
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, client.list_models())
                        result = future.result(timeout=10)
                
                if 'data' in result:
                    models = result['data']
                    console.print(f"\n[bold cyan]Available models for {current_provider}:[/bold cyan]")
                    for i, model in enumerate(models[:20], 1):  # Show first 20
                        model_id = model.get('id') or model.get('name') or str(model)
                        console.print(f"  {i}. {model_id}")
                    
                    if len(models) > 20:
                        console.print(f"\n... and {len(models) - 20} more models")
                    
                    console.print(f"\nINFO: Use: /model <model_name> to switch")
                elif 'models' in result:
                    models = result['models']
                    console.print(f"\n[bold cyan]Available models for {current_provider}:[/bold cyan]")
                    for i, model in enumerate(models[:20], 1):
                        model_name = model.get('name', '').replace('models/', '')
                        console.print(f"  {i}. {model_name}")
                    
                    if len(models) > 20:
                        console.print(f"\n... and {len(models) - 20} more models")
                    
                    console.print(f"\nINFO: Use: /model <model_name> to switch")
                else:
                    console.print(f"WARNING: Unexpected response format from {current_provider}")
                    console.print(f"INFO: Check the provider's documentation for available models")
                    
            except Exception as e:
                console.print(f"ERROR: Error fetching models: {str(e)}", style="red")
                console.print(f"INFO: Check the provider's documentation for available models")
        
        elif len(parts) < 2:
            # Show current model and hint
            current_model = context.get('model')
            console.print(f"📌 Current model: {current_model or 'default'}")
            console.print(f"📌 Provider: {current_provider}")
            console.print(f"\nINFO: Use: /model list - to fetch available models from API")
            console.print(f"INFO: Use: /model <model_name> - to switch model")
        else:
            # Switch to new model
            new_model = parts[1]
            context['model'] = new_model
            
            # Save the model preference for the current provider and globally
            current_provider = context.get('provider')
            config_manager = context.get('config_manager')
            if config_manager:
                # Save as last used model globally
                config_manager.set_config('last_model', new_model)
                # Save as default for this provider
                if current_provider:
                    config_manager.set_provider_model(current_provider, new_model)
                    console.print(f"SUCCESS: Switched to model: {new_model}")
                    console.print(f"INFO: Model saved as default for provider: {current_provider}")
                else:
                    console.print(f"SUCCESS: Switched to model: {new_model}")
            else:
                console.print(f"SUCCESS: Switched to model: {new_model}")
        return True
    
    elif cmd == "endpoint":
        # Set or show endpoint/base URL for a provider
        target_provider = None
        base_url = None
        if len(parts) == 1:
            # Show current provider endpoint and usage
            current_provider = context.get('provider')
            if not current_provider:
                console.print("ERROR: No provider selected", style="red")
                console.print("Usage: /endpoint <base_url> OR /endpoint <provider> <base_url>")
                return True
            current_endpoint = config_manager.get_provider_endpoint(current_provider)
            console.print(f"Current provider: {current_provider}")
            console.print(f"Endpoint override: {current_endpoint or 'default'}")
            console.print("Usage: /endpoint <base_url> OR /endpoint <provider> <base_url>")
            return True
        elif len(parts) == 2:
            target_provider = context.get('provider')
            base_url = parts[1]
        else:
            target_provider = parts[1]
            base_url = parts[2]

        if not target_provider:
            console.print("ERROR: No provider selected", style="red")
            return True
        
        # Basic validation
        if not (base_url.startswith('http://') or base_url.startswith('https://')):
            console.print("ERROR: Endpoint must start with http:// or https://", style="red")
            return True

        # Save endpoint override
        config_manager.set_provider_endpoint(target_provider, base_url.rstrip('/'))
        # Reinitialize providers to pick up endpoint change
        try:
            ai_engine._initialize_providers()
        except Exception:
            pass
        console.print(f"SUCCESS: Set endpoint for {target_provider} = {base_url}")
        
        return True
    
    elif cmd == "session":
        memory_manager = context.get('memory_manager')
        if not memory_manager:
            console.print("ERROR: Memory manager not available", style="red")
            return True
        
        if len(parts) < 2:
            # Show current session info and list available sessions
            current_session = memory_manager.get_current_session()
            if current_session:
                console.print(f"SESSION: Current session: {current_session.session_id} - {current_session.title}")
                console.print(f"   Created: {current_session.created_at}")
                console.print(f"   Messages: {current_session.message_count}")
                console.print(f"   Provider: {current_session.provider}")
                if current_session.model:
                    console.print(f"   Model: {current_session.model}")
            else:
                console.print("SESSION: No active session")
            
            console.print("\nAvailable commands:")
            console.print("• /session list - List all sessions")
            console.print("• /session new - Create new session")
            console.print("• /session load <id> - Load existing session")
            console.print("• /session delete <id> - Delete session")
            console.print("• /session export <id> [format] - Export session")
            console.print("• /session title <new_title> - Update session title")
        
        elif parts[1] == "list":
            sessions = memory_manager.list_sessions()
            if not sessions:
                console.print("SESSION: No sessions found")
            else:
                console.print(f"SESSION: Found {len(sessions)} sessions:")
                for idx, session in enumerate(sessions[:10], 1):  # Show last 10 sessions with index
                    console.print(f"   [{idx}] {session.session_id} - {session.title}")
                    console.print(f"      {session.message_count} messages, {session.provider}")
                    console.print(f"      Last updated: {session.last_updated}")
                    console.print()
        
        elif parts[1] == "new":
            # Create new session (will replace current one)
            current_provider = context.get('provider', 'openai')
            current_model = context.get('model')
            current_workspace = context.get('current_workspace')
            
            session_id = memory_manager.create_session(
                provider=current_provider,
                model=current_model,
                workspace=current_workspace
            )
            
            # Generate title from a default message
            title = f"Chat Session {session_id[:8]}"
            memory_manager.update_session_info(title=title)
            
            console.print(f"SUCCESS: Created new session: {session_id[:8]} - {title}")
        
        elif parts[1] == "load" and len(parts) >= 3:
            session_identifier = parts[2]
            
            # Check if it's a numeric index
            if session_identifier.isdigit():
                index = int(session_identifier)
                sessions = memory_manager.list_sessions()
                if 1 <= index <= len(sessions):
                    session_id = sessions[index - 1].session_id
                else:
                    console.print(f"[red]Invalid session index: {index}. Use /session list to see available sessions.[/red]")
                    return True
            else:
                session_id = session_identifier
            
            if memory_manager.load_session(session_id):
                # Update context with session info
                current_session = memory_manager.get_current_session()
                context['provider'] = current_session.provider
                context['model'] = current_session.model
                context['current_workspace'] = current_session.workspace
        
        elif parts[1] == "delete" and len(parts) >= 3:
            session_id = parts[2]
            memory_manager.delete_session(session_id)
        
        elif parts[1] == "export" and len(parts) >= 3:
            session_id = parts[2]
            format_type = parts[3] if len(parts) >= 4 else "json"
            memory_manager.export_session(session_id, format_type)
        
        elif parts[1] == "title" and len(parts) >= 3:
            new_title = " ".join(parts[2:])
            memory_manager.update_session_info(title=new_title)
            console.print(f"SUCCESS: Updated session title to: {new_title}")
        
        else:
            console.print("ERROR: Invalid session command. Use /session for help.", style="red")
        
        return True
    
    elif cmd == "lmodel":
        if len(parts) < 2:
            # Show current local model status
            local_model_path = config_manager.get_config_value('local_model_path')
            if local_model_path:
                console.print(f"MODEL: Current local model: {local_model_path}")
                console.print("INFO: Use: /lmodel <path> - to load a different model")
                console.print("INFO: Use: /lmodel unload - to unload the current model")
                console.print("INFO: Use: /provider local - to switch to local model")
            else:
                console.print("MODEL: No local model loaded")
                console.print("\nUsage: /lmodel <model_path>")
                console.print("\nExamples:")
                console.print("  /lmodel ~/models/llama-2-7b")
                console.print("  /lmodel /path/to/huggingface/model")
                console.print("  /lmodel microsoft/phi-2")
                console.print("\nINFO: You can use:")
                console.print("  • Local path to a downloaded model")
                console.print("  • Hugging Face model ID (will download if needed)")
        elif parts[1] == "unload":
            # Unload the local model
            try:
                ai_engine.unload_local_model()
                console.print("SUCCESS: Local model unloaded successfully")
                # If current provider is local, switch to default
                if context.get('provider') == 'local':
                    available_providers = config_manager.list_providers()
                    if available_providers:
                        context['provider'] = available_providers[0]
                        console.print(f"SUCCESS: Switched to provider: {available_providers[0]}")
            except Exception as e:
                console.print(f"ERROR: Error unloading model: {e}", style="red")
        else:
            # Load a new local model
            model_path = " ".join(parts[1:])
            console.print(f"INFO: Loading local model from: {model_path}")
            console.print("⏳ This may take a few minutes depending on model size...")
            
            try:
                ai_engine.load_local_model(model_path)
                console.print("SUCCESS: Local model loaded successfully!")
                console.print("INFO: Use: /provider local - to switch to the local model")
                console.print("INFO: Or the model will be used automatically if 'local' is your default provider")
            except Exception as e:
                console.print(f"ERROR: Error loading model: {e}", style="red")
                console.print("\nINFO: Make sure you have installed the required dependencies:")
                console.print("   pip install transformers torch accelerate")
        return True
    
    elif cmd == "speed":
        config_manager = context.get('config_manager') or config_manager
        
        if len(parts) < 2:
            # Show current speed
            current_speed = config_manager.get_config_value('typing_speed') or 'fast'
            console.print(f"⚡ Current typing speed: {current_speed}")
            console.print("\nAvailable speeds:")
            console.print("  • instant - No delay (immediate)")
            console.print("  • fast    - 0.001s per character (~1000 chars/sec) [default]")
            console.print("  • normal  - 0.005s per character (~200 chars/sec)")
            console.print("  • slow    - 0.01s per character (~100 chars/sec)")
            console.print("  • <number> - Custom delay in seconds")
            console.print("\nUsage: /speed <instant|fast|normal|slow|number>")
        else:
            new_speed = parts[1]
            
            # Validate speed
            valid_speeds = ['instant', 'fast', 'normal', 'slow']
            try:
                # Try to parse as number
                float(new_speed)
                is_valid = True
            except ValueError:
                is_valid = new_speed in valid_speeds
            
            if is_valid:
                config_manager.set_config('typing_speed', new_speed)
                console.print(f"SUCCESS: Typing speed set to: {new_speed}")
            else:
                console.print(f"ERROR: Invalid speed: {new_speed}", style="red")
                console.print("Valid options: instant, fast, normal, slow, or a number")
        
        return True
    
    elif cmd == "rules" or cmd == "rule":
        rules_manager = RulesManager()
        current_workspace = context.get('current_workspace')
        
        if len(parts) < 2:
            # Display all rules
            rules_manager.display_rules(current_workspace)
            console.print("\n💡 Commands:")
            console.print("  /rules add global <rule> [description]")
            console.print("  /rules add workspace <rule> [description]")
            console.print("  /rules remove global <index>")
            console.print("  /rules remove workspace <index>")
            console.print("  /rules clear global")
            console.print("  /rules clear workspace")
        
        elif parts[1] == "add":
            if len(parts) < 4:
                console.print("❌ Usage: /rules add <global|workspace> <rule> [description]", style="red")
            else:
                rule_type = parts[2].lower()
                # Find where description starts (after the rule text)
                rule_parts = []
                description_parts = []
                in_description = False
                
                for i, part in enumerate(parts[3:], 3):
                    if part.startswith('[') and not in_description:
                        in_description = True
                        description_parts.append(part[1:])
                    elif in_description:
                        if part.endswith(']'):
                            description_parts.append(part[:-1])
                            break
                        else:
                            description_parts.append(part)
                    else:
                        rule_parts.append(part)
                
                rule = " ".join(rule_parts)
                description = " ".join(description_parts) if description_parts else ""
                
                if rule_type == "global":
                    rules_manager.add_global_rule(rule, description)
                elif rule_type == "workspace":
                    rules_manager.add_workspace_rule(rule, description, current_workspace)
                else:
                    console.print("❌ Rule type must be 'global' or 'workspace'", style="red")
        
        elif parts[1] == "remove":
            if len(parts) < 4:
                console.print("ERROR: Usage: /rules remove <global|workspace> <index>", style="red")
            else:
                rule_type = parts[2].lower()
                try:
                    index = int(parts[3])
                    if rule_type == "global":
                        rules_manager.remove_global_rule(index)
                    elif rule_type == "workspace":
                        rules_manager.remove_workspace_rule(index, current_workspace)
                    else:
                        console.print("ERROR: Rule type must be 'global' or 'workspace'", style="red")
                except ValueError:
                    console.print("ERROR: Index must be a number", style="red")
        
        elif parts[1] == "clear":
            if len(parts) < 3:
                console.print("ERROR: Usage: /rules clear <global|workspace>", style="red")
            else:
                rule_type = parts[2].lower()
                if rule_type == "global":
                    rules_manager.clear_global_rules()
                elif rule_type == "workspace":
                    rules_manager.clear_workspace_rules(current_workspace)
                else:
                    console.print("ERROR: Rule type must be 'global' or 'workspace'", style="red")
        
        else:
            console.print("ERROR: Invalid rules command. Use /rules for help.", style="red")
        
        return True
    
    elif cmd == "clear":
        console.clear()
        console.print("Chat cleared")
        return True
    
    elif cmd == "ps" or cmd == "processes":
        # List all running background processes
        try:
            result = await ai_engine.tool_registry.execute_tool(
                "command_runner",
                operation="check_process_status",
                user_id="ai_engine"
            )
            
            if result.success and result.data:
                processes = result.data.get('processes', [])
                if not processes:
                    console.print("PROCESS: No background processes running", style="dim")
                else:
                    console.print(f"\nPROCESS: Running Processes ({len(processes)}):", style="bold")
                    for proc in processes:
                        status_color = "green" if proc['status'] == 'running' else "yellow"
                        console.print(f"  • PID: {proc['process_id']} - {proc['command'][:50]}... [{proc['status']}]", style=status_color)
                        console.print(f"    Running for: {proc['running_time']:.1f}s", style="dim")
                    console.print("\nINFO: Use /ct <process_id> to terminate a process\n", style="dim")
            else:
                console.print("ERROR: Failed to get process list", style="red")
        except Exception as e:
            console.print(f"ERROR: {str(e)}", style="red")
        
        return True
    
    elif cmd == "ct" or cmd == "cancel":
        # Cancel/terminate a background process
        if len(parts) < 2:
            console.print("ERROR: Usage: /ct <process_id>", style="red")
            console.print("INFO: Tip: Process IDs are shown when commands run in background", style="dim")
            return True
        
        process_id = parts[1]
        try:
            result = await ai_engine.tool_registry.execute_tool(
                "command_runner",
                operation="kill_process",
                process_id=process_id,
                user_id="ai_engine"
            )
            
            if result.success:
                console.print(f"SUCCESS: Process {process_id} terminated successfully", style="green")
            else:
                console.print(f"ERROR: Failed to terminate process: {result.error}", style="red")
        except Exception as e:
            console.print(f"ERROR: {str(e)}", style="red")
        
        return True
    
    elif cmd == "index":
        # Manual codebase indexing control
        from .codebase_indexer import CodebaseIndexer
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        
        current_workspace = context.get('current_workspace', os.getcwd())
        indexer = CodebaseIndexer(current_workspace)
        
        if len(parts) < 2:
            # Show index status
            index = indexer.load_index()
            if index:
                console.print(f"\n[bold]INFO: Codebase Index Status[/bold]")
                console.print(f"Root: {index.root_path}")
                console.print(f"Files: {index.total_files}")
                console.print(f"Lines: {index.total_lines:,}")
                console.print(f"Size: {index.total_size / 1024 / 1024:.2f} MB")
                console.print(f"Languages: {', '.join(f'{lang}({count})' for lang, count in index.languages.items())}")
                console.print(f"Indexed: {index.indexed_at}")
                console.print("\n[dim]Commands:[/dim]")
                console.print("[dim]  /index rebuild - Rebuild index from scratch[/dim]")
                console.print("[dim]  /index stats - Show detailed statistics[/dim]")
            else:
                console.print("[yellow]No index found. Run /index rebuild to create one.[/yellow]")
        
        elif parts[1] == "rebuild":
            console.print("\n[yellow]📚 Rebuilding codebase index...[/yellow]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Indexing files...", total=100)
                
                def progress_callback(current, total, file_path):
                    percentage = (current / total) * 100
                    progress.update(task, completed=percentage, description=f"[cyan]Indexing: {file_path[:50]}...")
                
                # Index codebase
                index = indexer.index(progress_callback)
                indexer.save_index(index)
                
                progress.update(task, completed=100, description="[green]✓ Indexing complete!")
            
            # Show stats
            stats = indexer.get_stats(index)
            console.print(f"[green]✓ Indexed {stats['total_files']} files, {stats['total_lines']:,} lines of code[/green]")
            console.print(f"[dim]Languages: {', '.join(f'{lang}({count})' for lang, count in stats['languages'].items())}[/dim]\n")
        
        elif parts[1] == "stats":
            index = indexer.load_index()
            if not index:
                console.print("[yellow]No index found. Run /index rebuild to create one.[/yellow]")
            else:
                console.print(f"\n[bold]📊 Detailed Index Statistics[/bold]\n")
                console.print(f"[cyan]General:[/cyan]")
                console.print(f"  Root Path: {index.root_path}")
                console.print(f"  Total Files: {index.total_files}")
                console.print(f"  Total Lines: {index.total_lines:,}")
                console.print(f"  Total Size: {index.total_size / 1024 / 1024:.2f} MB")
                console.print(f"  Indexed At: {index.indexed_at}\n")
                
                console.print(f"[cyan]Languages:[/cyan]")
                for lang, count in sorted(index.languages.items(), key=lambda x: x[1], reverse=True):
                    # Calculate total lines for this language
                    lang_lines = sum(f.lines_of_code for f in index.files.values() if f.language == lang)
                    console.print(f"  {lang}: {count} files, {lang_lines:,} lines")
                
                console.print(f"\n[cyan]Top 10 Largest Files:[/cyan]")
                sorted_files = sorted(index.files.values(), key=lambda x: x.size, reverse=True)[:10]
                for f in sorted_files:
                    console.print(f"  {f.relative_path}: {f.size / 1024:.1f} KB ({f.lines_of_code} lines)")
        
        else:
            console.print(f"[red]Unknown index command: {parts[1]}[/red]")
            console.print("Available: rebuild, stats")
        
        return True
    
    elif cmd == "mml":
        # Multi-model mode command
        if len(parts) < 3 or len(parts) % 2 != 1:
            console.print("ERROR: Usage: /mml provider1 model1 provider2 model2 provider3 model3", style="red")
            console.print("Example: /mml openai gpt-4 anthropic claude-3-sonnet google gemini-pro", style="dim")
            return True
        
        # Parse provider-model pairs
        new_configs = []
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                provider_name = parts[i]
                model_name = parts[i + 1]
                
                # Validate provider is configured
                config_manager = context.get('config_manager')
                if not config_manager.has_api_key(provider_name):
                    console.print(f"ERROR: Provider {provider_name} not configured. Available providers: {', '.join(config_manager.list_providers())}", style="red")
                    return True
                
                new_configs.append((provider_name, model_name))
        
        if not new_configs:
            console.print("ERROR: No valid provider-model pairs specified", style="red")
            return True
        
        # Enable multi-model mode
        context['multi_model_mode'] = True
        context['multi_model_configs'] = new_configs
        
        # Create folders for each model
        import re
        
        current_workspace = context.get('current_workspace')
        multi_model_folders = {}
        
        for provider, model_name in new_configs:
            # Sanitize folder name by replacing invalid characters
            safe_model_name = re.sub(r'[/:\\<>|"?*]', '_', model_name) if model_name else provider
            folder_name = f"{provider}_{safe_model_name}"
            model_folder = Path(current_workspace) / folder_name
            try:
                model_folder.mkdir(parents=True, exist_ok=True)
                multi_model_folders[folder_name] = str(model_folder)
                console.print(f"INFO: Created folder for {provider}:{model_name} at {model_folder}")
            except Exception as e:
                console.print(f"WARNING: Failed to create folder for {provider}:{model_name}: {e}", style="yellow")
                # Continue with other models even if one fails
        
        context['multi_model_folders'] = multi_model_folders
        
        if not multi_model_folders:
            console.print("ERROR: Failed to create folders for any models", style="red")
            context['multi_model_mode'] = False
            context['multi_model_configs'] = []
            return True
        
        # Automatically enable YOLO mode
        confirmation_manager = context.get('confirmation_manager')
        if confirmation_manager and not confirmation_manager.yolo_mode:
            confirmation_manager.toggle_yolo_mode()
            console.print("INFO: Automatically enabled YOLO mode for multi-model operation", style="yellow")
        
        console.print(f"SUCCESS: Multi-model mode enabled with {len(new_configs)} models:", style="green")
        for provider, model_name in new_configs:
            console.print(f"  • {provider}:{model_name}")
        console.print("INFO: Each model will work in its own folder to avoid conflicts", style="dim")
        return True
    
    elif cmd == "qmml":
        # Quit multi-model mode
        if not context.get('multi_model_mode'):
            console.print("INFO: Multi-model mode is not currently active", style="yellow")
            return True
        
        context['multi_model_mode'] = False
        context['multi_model_configs'] = []
        context['multi_model_folders'] = {}
        
        console.print("SUCCESS: Multi-model mode disabled", style="green")
        console.print("INFO: Returned to single model mode", style="dim")
        return True
    
    elif cmd == "multiagent":
        # Multi-agent collaboration mode
        if len(parts) < 3 or len(parts) % 2 != 1:
            console.print("ERROR: Usage: /multiagent provider1 model1 provider2 model2 [provider3 model3 ...]", style="red")
            console.print("Example: /multiagent openai gpt-4 anthropic claude-3-sonnet-20240229 google gemini-pro", style="dim")
            console.print("\nThis mode enables multiple AI models to:", style="yellow")
            console.print("  1. Discuss the task and identify issues", style="dim")
            console.print("  2. Plan and split up the work", style="dim")
            console.print("  3. Work together in real-time", style="dim")
            return True
        
        # Reinitialize providers to pick up any newly configured ones
        try:
            ai_engine._initialize_providers()
        except Exception as e:
            console.print(f"[yellow]Warning: Could not reinitialize providers: {e}[/yellow]")
        
        # Parse provider-model pairs
        agent_configs = []
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                provider_name = parts[i]
                model_name = parts[i + 1]
                
                # Validate provider is available in AI engine
                if provider_name not in ai_engine.providers:
                    # Check if it's configured but not initialized
                    config_manager = context.get('config_manager')
                    if config_manager.has_api_key(provider_name):
                        console.print(f"ERROR: Provider {provider_name} is configured but failed to initialize.", style="red")
                        console.print(f"Available providers: {', '.join(ai_engine.providers.keys())}", style="yellow")
                    else:
                        # Check if it's a no-auth provider like ollama
                        from .provider_endpoints import get_provider_config
                        provider_config = get_provider_config(provider_name)
                        if not provider_config or not provider_config.get('no_auth', False):
                            console.print(f"ERROR: Provider {provider_name} not configured.", style="red")
                            console.print(f"Available providers: {', '.join(ai_engine.providers.keys())}", style="yellow")
                            console.print(f"Use /setup to configure {provider_name}", style="dim")
                    return True
                
                # Create agent config
                agent_num = len(agent_configs) + 1
                agent_name = f"Agent {agent_num}"
                
                # All agents work in the same workspace folder
                current_workspace = context.get('current_workspace', os.getcwd())
                agent_folder = Path(current_workspace)
                
                agent_config = AgentConfig(
                    provider=provider_name,
                    model=model_name,
                    name=agent_name,
                    folder=agent_folder
                )
                agent_configs.append(agent_config)
        
        if len(agent_configs) < 2:
            console.print("ERROR: Multi-agent mode requires at least 2 agents", style="red")
            return True
        
        # Display agent configuration
        console.print(f"\n[bold cyan]Multi-Agent Collaboration Setup[/bold cyan]")
        console.print(f"[dim]Configured {len(agent_configs)} agents:[/dim]\n")
        for agent in agent_configs:
            console.print(f"  • {agent.name}: {agent.provider}:{agent.model}")
        
        console.print(f"\n[dim]Shared workspace: {agent_configs[0].folder}[/dim]")
        console.print("\n[yellow]Ready to start collaboration![/yellow]")
        console.print("[dim]The agents will first discuss the task, then plan, then execute.[/dim]")
        console.print("[dim]All agents will work together in the same workspace.[/dim]\n")
        
        # Store in context for the next user message
        context['multiagent_mode'] = True
        context['multiagent_configs'] = agent_configs
        context['multiagent_orchestrator'] = MultiAgentOrchestrator(
            agents=agent_configs,
            workspace=context.get('current_workspace', os.getcwd()),
            ai_engine=ai_engine,
            memory_manager=context.get('memory_manager')
        )
        
        # Automatically enable YOLO mode
        confirmation_manager = context.get('confirmation_manager')
        if confirmation_manager and not confirmation_manager.yolo_mode:
            confirmation_manager.toggle_yolo_mode()
            console.print("INFO: Automatically enabled YOLO mode for multi-agent operation\n", style="yellow")
        
        console.print("[bold green]Multi-agent mode activated![/bold green]")
        console.print("[dim]Now send your project request and the agents will collaborate on it.[/dim]\n")
        
        return True
    
    elif cmd == "yolo":
        confirmation_manager = context.get('confirmation_manager')
        if confirmation_manager:
            confirmation_manager.toggle_yolo_mode()
            confirmation_manager.display_mode_status()
        else:
            console.print("ERROR: Confirmation manager not available", style="red")
        return True
    
    elif cmd == "askq":
        # Toggle ask question mode
        ai_engine = context.get('ai_engine')
        if not ai_engine:
            console.print("ERROR: AI engine not available", style="red")
            return True
        
        # Get the ask_question tool
        ask_tool = ai_engine.tool_registry.get_tool('ask_question')
        if not ask_tool:
            console.print("ERROR: Ask question tool not available", style="red")
            return True
        
        # Parse on/off argument
        if len(parts) >= 2:
            mode = parts[1].lower()
            if mode == "on":
                ask_tool.enable()
                console.print("SUCCESS: Ask question mode enabled", style="green")
                console.print("INFO: AI can now ask clarifying questions when confused", style="dim")
            elif mode == "off":
                ask_tool.disable()
                console.print("SUCCESS: Ask question mode disabled", style="green")
                console.print("INFO: AI will not ask questions anymore", style="dim")
            else:
                console.print("ERROR: Usage: /askq on|off", style="red")
        else:
            # Toggle if no argument provided
            if ask_tool.is_enabled():
                ask_tool.disable()
                console.print("SUCCESS: Ask question mode disabled", style="green")
                console.print("INFO: AI will not ask questions anymore", style="dim")
            else:
                ask_tool.enable()
                console.print("SUCCESS: Ask question mode enabled", style="green")
                console.print("INFO: AI can now ask clarifying questions when confused", style="dim")
        
        return True
    
    elif cmd == "editor":
        # Open vim editor
        import shutil
        
        # Check if vim is available
        if not shutil.which('vim'):
            console.print("ERROR: vim is not installed or not in PATH", style="red")
            console.print("INFO: Install vim using your package manager (e.g., apt install vim, brew install vim)", style="yellow")
            return True
        
        # Get file path if provided
        file_path = None
        if len(parts) >= 2:
            file_input = " ".join(parts[1:])
            
            # Expand user home directory
            file_path = Path(file_input).expanduser()
            
            # Handle relative vs absolute paths
            if not file_path.is_absolute():
                # Relative path from current workspace
                current_workspace = context.get('current_workspace', os.getcwd())
                file_path = Path(current_workspace) / file_path
            
            # Resolve to absolute path
            file_path = file_path.resolve()
        
        try:
            # Clear the screen before opening vim
            console.clear()
            
            # Build vim command with Ctrl+E keybindings
            vim_cmd = ['vim']
            
            # Add keybindings via -c flag (execute commands on startup)
            # Map Ctrl+E to save and quit in all modes
            vim_cmd.extend([
                '-c', 'nnoremap <C-e> :wqa<CR>',
                '-c', 'inoremap <C-e> <Esc>:wqa<CR>',
                '-c', 'vnoremap <C-e> <Esc>:wqa<CR>',
            ])
            
            # Add file path if provided
            if file_path:
                vim_cmd.append(str(file_path))
                console.print(f"[dim]Opening vim with: {file_path}[/dim]")
            else:
                console.print("[dim]Opening vim[/dim]")
            
            console.print("[dim]Press Ctrl+E in vim to save and exit, or :q! to quit without saving[/dim]\n")
            
            # Launch vim
            result = subprocess.run(vim_cmd)
            
            # Clear screen and show welcome back message
            console.clear()
            console.print("[green]INFO: Returned to chat mode[/green]\n")
            
        except Exception as e:
            console.print(f"[red]ERROR: Failed to open vim: {str(e)}[/red]")
        
        return True
    
    elif cmd == "docrepo":
        # Generate documentation for a git repository
        if len(parts) < 2:
            console.print("Usage: /docrepo <git_url>", style="yellow")
            console.print("Example: /docrepo https://github.com/user/repo", style="dim")
            return True
        
        repo_url = parts[1]
        current_workspace = context.get('current_workspace', os.getcwd())
        current_provider = context.get('provider', 'openai')
        current_model = context.get('model', '')
        
        # Validate git URL
        if not (repo_url.startswith('http://') or repo_url.startswith('https://') or repo_url.startswith('git@')):
            console.print("ERROR: Invalid git URL. Must start with http://, https://, or git@", style="red")
            return True
        
        # Get memory manager from context
        memory_manager = context.get('memory_manager')
        
        # Call the document_repository function
        await document_repository(
            repo_url=repo_url,
            workspace=current_workspace,
            ai_engine=ai_engine,
            provider=current_provider,
            model=current_model,
            memory_manager=memory_manager
        )
        
        return True

    
    elif cmd == "mcp" or cmd.startswith("mcp-"):
        # Handle MCP commands
        return await handle_mcp_command(cmd, parts, context)
    
    elif cmd == "plugin":
        # Handle plugin commands
        plugin_manager = context.get('plugin_manager')
        if not plugin_manager:
            console.print("ERROR: Plugin manager not available", style="red")
            return True
        
        if len(parts) < 2:
            console.print("Available plugin commands:", style="bold")
            console.print("• /plugin install <path> - Install a plugin from a directory")
            console.print("• /plugin list - List all installed plugins")
            console.print("• /plugin load <name> - Load a plugin")
            console.print("• /plugin unload <name> - Unload a plugin")
            console.print("• /plugin uninstall <name> - Uninstall a plugin")
            console.print("• /plugin info <name> - Show plugin information")
            return True
        
        subcmd = parts[1].lower()
        
        if subcmd == "install":
            if len(parts) < 3:
                console.print("ERROR: Usage: /plugin install <path>", style="red")
                return True
            
            plugin_path = " ".join(parts[2:])
            
            # Expand user home directory
            plugin_path = Path(plugin_path).expanduser()
            
            # Handle relative vs absolute paths
            if not plugin_path.is_absolute():
                original_cwd = context.get('original_cwd', os.getcwd())
                plugin_path = Path(original_cwd) / plugin_path
            
            plugin_path = plugin_path.resolve()
            
            console.print(f"Installing plugin from: {plugin_path}")
            if await plugin_manager.install_plugin(str(plugin_path)):
                console.print("SUCCESS: Plugin installed and loaded successfully!", style="green")
                console.print("INFO: Plugin is ready to use", style="dim")
            else:
                console.print("ERROR: Failed to install plugin", style="red")
        
        elif subcmd == "list":
            plugins = plugin_manager.list_installed_plugins()
            if not plugins:
                console.print("No plugins installed", style="dim")
                console.print("INFO: Use /plugin install <path> to install a plugin", style="dim")
            else:
                console.print(f"\n[bold]Installed Plugins ({len(plugins)}):[/bold]\n")
                for plugin in plugins:
                    status = "✓ Loaded" if plugin['loaded'] else ("○ Enabled" if plugin['enabled'] else "✗ Disabled")
                    status_color = "green" if plugin['loaded'] else ("yellow" if plugin['enabled'] else "red")
                    console.print(f"  [{status_color}]{status}[/{status_color}] {plugin['name']} v{plugin['version']}")
                    console.print(f"    {plugin['description']}", style="dim")
                    console.print(f"    Author: {plugin['author']}", style="dim")
                    console.print(f"    Path: {plugin['path']}", style="dim")
                    console.print()
        
        elif subcmd == "load":
            if len(parts) < 3:
                console.print("ERROR: Usage: /plugin load <name>", style="red")
                return True
            
            plugin_name = parts[2]
            console.print(f"Loading plugin: {plugin_name}")
            if await plugin_manager.load_plugin(plugin_name):
                console.print(f"SUCCESS: Plugin '{plugin_name}' loaded successfully!", style="green")
            else:
                console.print(f"ERROR: Failed to load plugin '{plugin_name}'", style="red")
        
        elif subcmd == "unload":
            if len(parts) < 3:
                console.print("ERROR: Usage: /plugin unload <name>", style="red")
                return True
            
            plugin_name = parts[2]
            console.print(f"Unloading plugin: {plugin_name}")
            if await plugin_manager.unload_plugin(plugin_name):
                console.print(f"SUCCESS: Plugin '{plugin_name}' unloaded successfully!", style="green")
            else:
                console.print(f"ERROR: Failed to unload plugin '{plugin_name}'", style="red")
        
        elif subcmd == "uninstall":
            if len(parts) < 3:
                console.print("ERROR: Usage: /plugin uninstall <name>", style="red")
                return True
            
            plugin_name = parts[2]
            console.print(f"Uninstalling plugin: {plugin_name}")
            if plugin_manager.uninstall_plugin(plugin_name):
                console.print(f"SUCCESS: Plugin '{plugin_name}' uninstalled successfully!", style="green")
            else:
                console.print(f"ERROR: Failed to uninstall plugin '{plugin_name}'", style="red")
        
        elif subcmd == "info":
            if len(parts) < 3:
                console.print("ERROR: Usage: /plugin info <name>", style="red")
                return True
            
            plugin_name = parts[2]
            plugins = plugin_manager.list_installed_plugins()
            plugin_info = next((p for p in plugins if p['name'] == plugin_name), None)
            
            if plugin_info:
                console.print(f"\n[bold cyan]Plugin: {plugin_info['name']}[/bold cyan]")
                console.print(f"Version: {plugin_info['version']}")
                console.print(f"Description: {plugin_info['description']}")
                console.print(f"Author: {plugin_info['author']}")
                console.print(f"Path: {plugin_info['path']}")
                console.print(f"Status: {'Loaded' if plugin_info['loaded'] else ('Enabled' if plugin_info['enabled'] else 'Disabled')}")
                
                # Show registered commands if loaded
                if plugin_info['loaded']:
                    plugin_instance = plugin_manager.get_plugin(plugin_name)
                    if plugin_instance and plugin_manager.plugin_api:
                        commands = plugin_manager.plugin_api.list_commands()
                        if commands:
                            console.print("\nRegistered Commands:")
                            for cmd, desc in commands.items():
                                console.print(f"  /{cmd} - {desc}")
            else:
                console.print(f"ERROR: Plugin '{plugin_name}' not found", style="red")
        
        else:
            console.print(f"ERROR: Unknown plugin command: {subcmd}", style="red")
        
        return True
    
    elif cmd == "exit" or cmd == "quit":
        return False
    
    else:
        # Check if this is a plugin command
        plugin_manager = context.get('plugin_manager')
        if plugin_manager:
            handled = await plugin_manager.handle_plugin_command(cmd, parts[1:] if len(parts) > 1 else [], context)
            if handled:
                return True
        
        console.print(f"ERROR: Unknown command: /{cmd}. Type /help for available commands.", style="red")
        return True

def show_help():
    """Show help information"""
    help_text = Text()
    help_text.append("Available commands:\n", style="bold")
    help_text.append("• Press Enter - Send message\n", style="bold green")
    help_text.append("• Press Alt+Enter - New line (multi-line input)\n", style="bold green")
    help_text.append("• Press Tab - Auto-complete slash commands\n", style="bold green")
    help_text.append("• Press Ctrl+C twice - Exit CLI\n", style="bold yellow")
    help_text.append("• Press Shift+Tab - Toggle between Chat and Terminal modes\n", style="bold yellow")
    help_text.append("• Press Ctrl+Y - Toggle between Safe and YOLO modes\n", style="bold yellow")
    help_text.append("\n")
    help_text.append("Slash Commands (type / to see auto-complete):\n", style="bold cyan")
    help_text.append("• /help - Show this help message\n")
    help_text.append("• /workspace <path> or /ws <path> - Change working directory\n")
    help_text.append("• /setup - Run interactive setup wizard\n")
    help_text.append("• /config [list|providers|set <key> <value>] - Manage configuration\n")
    help_text.append("• /provider [name] - Switch AI provider\n")
    help_text.append("• /model [model_id] - Switch AI model\n")
    help_text.append("• /model list or /models - Fetch available models from provider's API\n")
    help_text.append("• /lmodel <model_path> - Load local Hugging Face model\n")
    help_text.append("• /lmodel unload - Unload current local model\n")
    help_text.append("• /session [list|new|load <id>|delete <id>|export <id>] - Manage chat sessions\n")
    help_text.append("• /rules - Manage global and workspace rules for AI behavior\n")
    help_text.append("  - /rules add global <rule> [description] - Add a global rule\n", style="dim")
    help_text.append("  - /rules add workspace <rule> [description] - Add a workspace rule\n", style="dim")
    help_text.append("  - /rules remove global <index> - Remove a global rule\n", style="dim")
    help_text.append("  - /rules remove workspace <index> - Remove a workspace rule\n", style="dim")
    help_text.append("  - /rules clear global|workspace - Clear all rules of a type\n", style="dim")
    help_text.append("• /speed [instant|fast|normal|slow|<number>] - Set typing speed for AI responses\n")
    help_text.append("• /yolo - Toggle YOLO mode (skip confirmations for AI operations)\n", style="bold yellow")
    help_text.append("• /askq [on|off] - Toggle ask question mode (AI can ask clarifying questions)\n", style="bold yellow")
    help_text.append("• /mml <provider1> <model1> <provider2> <model2> ... - Enable multi-model mode\n", style="bold green")
    help_text.append("  Example: /mml openai gpt-4 anthropic claude-3-sonnet google gemini-pro\n", style="dim")
    help_text.append("• /qmml - Quit multi-model mode and return to single model\n", style="bold green")
    help_text.append("• /multiagent <provider1> <model1> <provider2> <model2> ... - Multi-agent collaboration mode\n", style="bold magenta")
    help_text.append("  Agents will discuss, plan, and work together on your project\n", style="dim")
    help_text.append("  Example: /multiagent openai gpt-4 anthropic claude-3-sonnet google gemini-pro\n", style="dim")
    help_text.append("• /index - Show codebase index status\n")
    help_text.append("  - /index rebuild - Rebuild codebase index from scratch\n", style="dim")
    help_text.append("  - /index stats - Show detailed index statistics\n", style="dim")
    help_text.append("• /ps or /processes - List all running background processes\n")
    help_text.append("• /ct <process_id> or /cancel <process_id> - Terminate a background process\n")
    help_text.append("• /editor [filepath] - Open vim editor (Ctrl+E to exit vim)\n")
    help_text.append("• /docrepo <git_url> - Generate documentation for a git repository\n", style="bold cyan")
    help_text.append("• /clear - Clear chat screen\n")
    help_text.append("• /plugin [install|list|load|unload|uninstall|info] - Manage plugins\n", style="bold magenta")
    help_text.append("  - /plugin install <path> - Install a plugin from a directory\n", style="dim")
    help_text.append("  - /plugin list - List all installed plugins\n", style="dim")
    help_text.append("  - /plugin load <name> - Load a plugin\n", style="dim")
    help_text.append("  - /plugin unload <name> - Unload a plugin\n", style="dim")
    help_text.append("\n")
    help_text.append("Multi-Model Mode:\n", style="bold cyan")
    help_text.append("• Chat with multiple AI models simultaneously for comparison\n", style="green")
    help_text.append("• Each model works in its own folder to avoid conflicts\n", style="green")
    help_text.append("• Automatically enables YOLO mode to prevent confirmation conflicts\n", style="green")
    help_text.append("• Use /mml to enable, /qmml to disable\n", style="green")
    help_text.append("\n")
    help_text.append("Confirmation Modes:\n", style="bold cyan")
    help_text.append("• Safe Mode (default) - AI asks for confirmation before file/command operations\n", style="green")
    help_text.append("• YOLO Mode - AI executes operations without confirmation (use /yolo or Ctrl+Y)\n", style="yellow")
    help_text.append("• /exit or /quit - Exit chat session\n")
    help_text.append("• exit or quit - Exit chat session\n")
    help_text.append("\n")
    help_text.append("CLI Commands (use outside chat):\n", style="bold cyan")
    help_text.append("• cognautic providers - List all AI providers and their API endpoints\n", style="cyan")
    help_text.append("\n• Any other text will be sent to the AI\n")
    
    console.print(Panel(help_text, title="Cognautic CLI Help", style="blue"))

if __name__ == '__main__':
    main()
