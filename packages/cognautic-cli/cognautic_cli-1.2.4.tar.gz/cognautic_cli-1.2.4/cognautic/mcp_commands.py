"""
MCP slash command handlers for Cognautic CLI
"""

from rich.console import Console

console = Console()


async def handle_mcp_command(cmd, parts, context):
    """Handle MCP-related slash commands"""
    # Get MCP manager and config from context (they should already be initialized)
    mcp_manager = context.get('mcp_manager')
    mcp_config = context.get('mcp_config')
    
    if not mcp_manager or not mcp_config:
        console.print("[red]ERROR: MCP manager not initialized[/red]")
        return True
    
    if cmd == "mcp" and len(parts) == 1:
        # Show MCP help
        console.print("\n[bold cyan]MCP (Model Context Protocol) Commands:[/bold cyan]")
        console.print("• /mcp list - List all connected MCP servers")
        console.print("• /mcp connect <server_name> - Connect to a configured MCP server")
        console.print("• /mcp disconnect <server_name> - Disconnect from an MCP server")
        console.print("• /mcp tools - List all available tools from connected MCP servers")
        console.print("• /mcp resources - List all available resources from connected MCP servers")
        console.print("• /mcp config - Show MCP server configurations")
        console.print("\n[dim]MCP allows Cognautic to connect to external servers that provide tools, resources, and prompts.[/dim]")
        return True
    
    elif cmd == "mcp-list" or (cmd == "mcp" and len(parts) > 1 and parts[1] == "list"):
        # List connected MCP servers
        servers = mcp_manager.list_servers()
        if servers:
            console.print("\n[bold green]Connected MCP Servers:[/bold green]")
            for server_name in servers:
                client = mcp_manager.get_client(server_name)
                console.print(f"  • {server_name}")
                console.print(f"    Tools: {len(client.tools)}")
                console.print(f"    Resources: {len(client.resources)}")
                console.print(f"    Prompts: {len(client.prompts)}")
        else:
            console.print("[yellow]No MCP servers connected.[/yellow]")
            console.print("[dim]Use /mcp connect <server_name> to connect to a server.[/dim]")
        return True
    
    elif cmd == "mcp-connect" or (cmd == "mcp" and len(parts) > 1 and parts[1] == "connect"):
        # Connect to an MCP server
        if len(parts) < 2 or (cmd == "mcp" and len(parts) < 3):
            console.print("[red]Usage: /mcp connect <server_name>[/red]")
            # Show available servers
            available = mcp_config.list_servers()
            if available:
                console.print("\n[cyan]Available servers:[/cyan]")
                for server_name in available:
                    console.print(f"  • {server_name}")
            return True
        
        server_name = parts[2] if cmd == "mcp" else parts[1]
        config = mcp_config.get_server(server_name)
        
        if not config:
            console.print(f"[red]Server '{server_name}' not found in configuration.[/red]")
            console.print(f"[dim]Edit ~/.cognautic/mcp_servers.json to add server configurations.[/dim]")
            return True
        
        console.print(f"[yellow]Connecting to MCP server: {server_name}...[/yellow]")
        success = await mcp_manager.add_server(config)
        
        if success:
            client = mcp_manager.get_client(server_name)
            console.print(f"[green]INFO: Connected to {server_name}[/green]")
            console.print(f"  Tools: {len(client.tools)}")
            console.print(f"  Resources: {len(client.resources)}")
            console.print(f"  Prompts: {len(client.prompts)}")
            
            # Register MCP tools with AI engine if available
            if context.get('ai_engine') and len(client.tools) > 0:
                from cognautic.tools.mcp_wrapper import register_mcp_tools
                try:
                    tools_registered = register_mcp_tools(
                        context['ai_engine'].tool_registry,
                        mcp_manager
                    )
                    console.print(f"[green]SUCCESS Registered {tools_registered} MCP tools with AI engine[/green]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not register MCP tools: {e}[/yellow]")
            
            # Show troubleshooting hint if no capabilities discovered
            if len(client.tools) == 0 and len(client.resources) == 0 and len(client.prompts) == 0:
                console.print("\n[yellow]Warning: Server connected but no capabilities discovered.[/yellow]")
                console.print("[dim]This usually means:[/dim]")
                console.print("[dim]  1. The MCP server package isn't installed[/dim]")
                console.print("[dim]  2. The server isn't responding to capability requests[/dim]")
                console.print(f"\n[dim]To fix:[/dim]")
                console.print(f"[dim]  • Install: npm install -g @modelcontextprotocol/server-{server_name}[/dim]")
                console.print(f"[dim]  • Check: npx @modelcontextprotocol/server-{server_name} --help[/dim]")
                console.print(f"[dim]  • See: MCP_TROUBLESHOOTING.md for detailed help[/dim]")
        else:
            console.print(f"[red]Failed to connect to {server_name}[/red]")
        return True
    
    elif cmd == "mcp-disconnect" or (cmd == "mcp" and len(parts) > 1 and parts[1] == "disconnect"):
        # Disconnect from an MCP server
        if len(parts) < 2 or (cmd == "mcp" and len(parts) < 3):
            console.print("[red]Usage: /mcp disconnect <server_name>[/red]")
            return True
        
        server_name = parts[2] if cmd == "mcp" else parts[1]
        
        # Unregister tools before disconnecting
        if context.get('ai_engine'):
            from cognautic.tools.mcp_wrapper import unregister_mcp_tools
            try:
                tools_unregistered = unregister_mcp_tools(
                    context['ai_engine'].tool_registry,
                    server_name
                )
                if tools_unregistered > 0:
                    console.print(f"[dim]Unregistered {tools_unregistered} MCP tools[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not unregister MCP tools: {e}[/yellow]")
        
        success = await mcp_manager.remove_server(server_name)
        
        if success:
            console.print(f"[green]✓ Disconnected from {server_name}[/green]")
        else:
            console.print(f"[red]Server '{server_name}' not connected.[/red]")
        return True
    
    elif cmd == "mcp-tools" or (cmd == "mcp" and len(parts) > 1 and parts[1] == "tools"):
        # List all tools from connected MCP servers
        tools = mcp_manager.get_all_tools()
        
        if tools:
            console.print("\n[bold cyan]Available MCP Tools:[/bold cyan]")
            for tool in tools:
                console.print(f"\n  [green]{tool['name']}[/green]")
                console.print(f"    {tool['description']}")
                console.print(f"    Server: {tool['mcp_server']}")
        else:
            console.print("[yellow]No MCP tools available.[/yellow]")
            console.print("[dim]Connect to an MCP server first using /mcp connect <server_name>[/dim]")
        return True
    
    elif cmd == "mcp-resources" or (cmd == "mcp" and len(parts) > 1 and parts[1] == "resources"):
        # List all resources from connected MCP servers
        resources = mcp_manager.get_all_resources()
        
        if resources:
            console.print("\n[bold cyan]Available MCP Resources:[/bold cyan]")
            for resource in resources:
                console.print(f"\n  [green]{resource['name']}[/green]")
                if resource.get('description'):
                    console.print(f"    {resource['description']}")
                console.print(f"    URI: {resource['uri']}")
                console.print(f"    Server: {resource['mcp_server']}")
        else:
            console.print("[yellow]No MCP resources available.[/yellow]")
            console.print("[dim]Connect to an MCP server first using /mcp connect <server_name>[/dim]")
        return True
    
    elif cmd == "mcp" and len(parts) > 1 and parts[1] == "config":
        # Show MCP configuration
        servers = mcp_config.get_all_servers()
        
        if servers:
            console.print("\n[bold cyan]Configured MCP Servers:[/bold cyan]")
            for name, config in servers.items():
                console.print(f"\n  [green]{name}[/green]")
                console.print(f"    Command: {config.command}")
                console.print(f"    Args: {' '.join(config.args)}")
                console.print(f"    Transport: {config.transport.value}")
                if config.env:
                    console.print(f"    Environment: {list(config.env.keys())}")
        else:
            console.print("[yellow]No MCP servers configured.[/yellow]")
        
        console.print(f"\n[dim]Configuration file: ~/.cognautic/mcp_servers.json[/dim]")
        return True
    
    else:
        console.print(f"[red]Unknown MCP command. Use /mcp for help.[/red]")
        return True
