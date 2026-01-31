"""
Confirmation handler for AI operations
"""

from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
import asyncio

console = Console()


class ConfirmationManager:
    """Manages confirmation prompts for AI operations"""
    
    def __init__(self):
        self.yolo_mode = False  # Default: require confirmation
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Setup prompt session with key bindings"""
        bindings = KeyBindings()
        
        @bindings.add('enter')
        def confirm(event):
            event.app.exit(result='confirm')
        
        @bindings.add('escape')
        def cancel(event):
            event.app.exit(result='cancel')
        
        self.session = PromptSession(key_bindings=bindings)
    
    def toggle_yolo_mode(self):
        """Toggle YOLO mode on/off"""
        self.yolo_mode = not self.yolo_mode
        return self.yolo_mode
    
    def set_yolo_mode(self, enabled: bool):
        """Set YOLO mode state"""
        self.yolo_mode = enabled
    
    def is_yolo_mode(self) -> bool:
        """Check if YOLO mode is enabled"""
        return self.yolo_mode
    
    async def confirm_operation(self, operation_type: str, details: dict) -> bool:
        """
        Ask user to confirm an operation
        
        Args:
            operation_type: Type of operation (file_operation, command_runner, etc.)
            details: Dictionary with operation details
        
        Returns:
            True if confirmed, False if cancelled
        """
        # If YOLO mode is enabled, auto-confirm everything
        if self.yolo_mode:
            return True
        
        # Format the confirmation prompt based on operation type
        if operation_type == "file_operations":
            operation = details.get("operation", "unknown")
            file_path = details.get("file_path", "unknown")
            
            # Different colors for different operations
            if operation in ["write_file", "write_file_lines", "create_file"]:
                color = "yellow"
                icon = "INFO:"
            elif operation == "delete_file":
                color = "red"
                icon = "WARNING:"
            elif operation in ["read_file", "read_file_lines", "list_directory"]:
                # Auto-confirm read operations
                return True
            else:
                color = "cyan"
                icon = "INFO:"
            
            console.print(f"\n[{color}]{icon} AI wants to perform file operation:[/{color}]")
            console.print(f"  Operation: [bold]{operation}[/bold]")
            console.print(f"  File: [bold]{file_path}[/bold]")
            
            # Show content preview for write operations
            if operation in ["write_file", "write_file_lines"] and "content" in details:
                content = details["content"]
                preview = content[:200] + "..." if len(content) > 200 else content
                console.print(f"  Content preview:\n[dim]{preview}[/dim]")
        
        elif operation_type == "command_runner":
            command = details.get("command", "unknown")
            cwd = details.get("cwd", ".")
            operation = details.get("operation", "run_command")
            
            icon = "INFO:" if operation == "run_async_command" else "INFO:"
            console.print(f"\n[yellow]{icon} AI wants to run command:[/yellow]")
            console.print(f"  Command: [bold]{command}[/bold]")
            console.print(f"  Directory: [dim]{cwd}[/dim]")
            if operation == "run_async_command":
                console.print(f"  Mode: [bold]Background[/bold]")
        
        else:
            # Generic confirmation for other operations
            console.print(f"\n[cyan]INFO: AI wants to perform operation:[/cyan]")
            console.print(f"  Type: [bold]{operation_type}[/bold]")
            for key, value in details.items():
                if key != "content":  # Don't show full content
                    console.print(f"  {key}: {value}")
        
        # Show confirmation prompt
        console.print("\n[bold green]Press ENTER to confirm[/bold green] or [bold red]ESC to cancel[/bold red]")
        
        try:
            result = await self.session.prompt_async("")
            
            if result == 'confirm':
                console.print("[green]SUCCESS: Confirmed[/green]")
                return True
            else:
                console.print("[red]CANCELLED: Operation cancelled[/red]")
                return False
        except (KeyboardInterrupt, EOFError):
            console.print("[red]CANCELLED: Operation cancelled[/red]")
            return False
    
    def display_mode_status(self):
        """Display current confirmation mode status"""
        if self.yolo_mode:
            console.print("[bold yellow]INFO: YOLO MODE: ON[/bold yellow] - AI operations will execute without confirmation")
        else:
            console.print("[bold green]INFO: SAFE MODE: ON[/bold green] - AI operations require confirmation")
