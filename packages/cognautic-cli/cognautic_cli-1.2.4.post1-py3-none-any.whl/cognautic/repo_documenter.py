"""
Repository Documenter for Cognautic CLI
Generates comprehensive documentation for public git repositories
"""

import os
import shutil
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()


async def document_repository(repo_url: str, workspace: str, ai_engine, provider: str, model: str, memory_manager=None) -> bool:
    """
    Document a git repository by cloning it, analyzing with AI, and generating files
    
    Args:
        repo_url: URL of the git repository
        workspace: Current workspace directory
        ai_engine: AI engine instance for generating documentation
        provider: AI provider to use
        model: AI model to use
        memory_manager: Memory manager for conversation context
        
    Returns:
        True if successful, False otherwise
    """
    console.print(f"Analyzing repository: {repo_url}...", style="cyan")
    
    # Extract repo name from URL
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    
    # Create tmp directory in workspace
    tmp_base = Path(workspace) / "tmp"
    
    try:
        tmp_base.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        console.print(f"Error creating tmp directory: {e}", style="red")
        return False
    
    repo_dir = tmp_base / repo_name
    console.print(f"Cloning to: {repo_dir}", style="dim")
    
    # Clean up existing directory if needed
    if repo_dir.exists():
        console.print(f"Removing existing directory...", style="dim")
        try:
            if repo_dir.is_dir():
                shutil.rmtree(repo_dir)
            else:
                repo_dir.unlink()
        except Exception as e:
            console.print(f"Error cleaning up existing dir: {e}", style="red")
            return False
    
    # Clone repository
    console.print("Cloning repository...", style="dim")
    
    try:
        result = subprocess.run(
            f"git clone --depth 1 {repo_url} {repo_dir}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            console.print(f"Error cloning repo: {result.stderr}", style="red")
            if "Authentication failed" in result.stderr:
                console.print("Please ensure the repository is public.", style="yellow")
            return False
    except subprocess.TimeoutExpired:
        console.print("Error: Clone operation timed out", style="red")
        return False
    except Exception as e:
        console.print(f"Error executing git clone: {e}", style="red")
        return False
    
    if not repo_dir.exists() or not any(repo_dir.iterdir()):
        console.print("Error: Repository directory is empty after clone.", style="red")
        return False
    
    # Analyze file structure
    console.print("Analyzing file structure...", style="dim")
    file_structure = []
    file_contents = {}
    
    # Walk through the repository
    for root, dirs, files in os.walk(repo_dir):
        # Skip .git directories
        if '.git' in dirs:
            dirs.remove('.git')
        
        rel_path = os.path.relpath(root, repo_dir)
        if rel_path == ".":
            rel_path = ""
        
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
            
            full_path = os.path.join(root, file)
            file_path = os.path.join(rel_path, file) if rel_path else file
            file_structure.append(file_path)
            
            # Read key configuration files
            if file.lower() in ['readme.md', 'package.json', 'requirements.txt', 
                               'cargo.toml', 'go.mod', 'pom.xml', 'build.gradle',
                               'setup.py', 'pyproject.toml', 'composer.json']:
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_contents[file_path] = f.read()
                except Exception:
                    pass
            
            # Read source files (limit size to avoid context overflow)
            elif file.endswith(('.py', '.js', '.ts', '.tsx', '.jsx', '.rs', '.go', 
                               '.java', '.c', '.cpp', '.h', '.rb', '.php', '.vue',
                               '.swift', '.kt', '.scala', '.cs')):
                try:
                    file_size = os.path.getsize(full_path)
                    if file_size < 15000:  # Less than 15KB
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            file_contents[file_path] = f.read()
                except Exception:
                    pass
    
    if not file_structure:
        console.print("Warning: No files found in the repository.", style="yellow")
    else:
        console.print(f"Found {len(file_structure)} files.", style="dim")
    
    # Generate documentation and graph using AI
    console.print("\n[bold cyan]Generating documentation with AI...[/bold cyan]")
    
    # Prepare repository information for AI
    repo_info = f"""Repository: {repo_url}
Repository Name: {repo_name}
Total Files: {len(file_structure)}

File Structure (first 100 files):
{chr(10).join(file_structure[:100])}
{'...(truncated)' if len(file_structure) > 100 else ''}

Key Files Found:
{chr(10).join([f"- {f}" for f in list(file_contents.keys())[:20]])}
"""
    
    # Add README content if available
    readme_content = ""
    for path, content in file_contents.items():
        if 'readme' in path.lower():
            readme_content = content[:2000]  # First 2000 chars
            break
    
    # Ask AI to generate documentation content
    docs_prompt = f"""Based on this repository information, create comprehensive Markdown documentation:

{repo_info}

{f"README excerpt:{chr(10)}{readme_content}" if readme_content else ""}

Generate a complete Markdown documentation with these sections:
1. # {repo_name} Documentation
2. ## Project Overview (what it does, purpose)
3. ## Installation (how to install/setup)
4. ## Usage (how to use it with examples)
5. ## Code Structure (explain the directory layout)
6. ## Architecture (describe the system design)

Write the COMPLETE documentation content. Be detailed and informative.

CRITICAL: Do NOT use any tools. Do NOT use the end_response tool. Output ONLY the raw Markdown text."""

    try:
        # Helper to clean response artifacts
        def clean_response(text):
            import re
            # Remove "Response Completed" box and similar tool artifacts
            text = re.sub(r'╔═+╗\s*║[^║]+║\s*╚═+╝', '', text, flags=re.DOTALL | re.MULTILINE)
            
            # Remove JSON tool calls
            text = re.sub(r'```json\s*\{.*?\}\s*```', '', text, flags=re.DOTALL)
            
            # Remove raw JSON tool calls (without code blocks)
            text = re.sub(r'\{\s*"tool_code".*?\}', '', text, flags=re.DOTALL)
            
            # Remove "Tool execution" messages
            text = re.sub(r'Tool execution.*', '', text, flags=re.IGNORECASE)
            
            # Remove ANSI color codes if any
            text = re.sub(r'\x1b\[[0-9;]*m', '', text)
            
            return text.strip()

        # Get documentation content from AI
        docs_response = ""
        async for chunk in ai_engine.process_message_stream(
            docs_prompt,
            provider=provider,
            model=model,
            project_path=workspace,
            conversation_history=[]
        ):
            docs_response += chunk
        
        # Clean the response
        docs_response = clean_response(docs_response)
        
        # Ask AI to generate graph script
        graph_prompt = f"""Create a Python script using graphviz to generate an architecture diagram for {repo_name}.

Repository info:
{repo_info}

Generate a COMPLETE, RUNNABLE Python script that:
1. Imports graphviz
2. Creates a Digraph
3. Adds nodes for main components (based on the file structure)
4. Adds edges showing relationships
5. Renders to PNG file
6. Includes error handling for missing graphviz

Output ONLY the Python code, no explanations. Start with #!/usr/bin/env python3

CRITICAL: Do NOT use any tools. Do NOT use the end_response tool. Output ONLY the Python code."""

        graph_response = ""
        async for chunk in ai_engine.process_message_stream(
            graph_prompt,
            provider=provider,
            model=model,
            project_path=workspace,
            conversation_history=[]
        ):
            graph_response += chunk
            
        # Clean the graph response
        graph_response = clean_response(graph_response)
        
        # Clean up cloned repository
        try:
            console.print("\n[dim]Cleaning up temporary files...[/dim]")
            shutil.rmtree(repo_dir)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not clean up temp directory: {e}[/yellow]")
        
        # Create output files
        docs_file = Path(workspace) / f"{repo_name}_DOCS.md"
        graph_file = Path(workspace) / "extra" / f"{repo_name}_graph.py"
        
        # Ensure extra directory exists
        graph_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Extract Python code from AI response (remove markdown code blocks if present)
        graph_code = graph_response
        if "```python" in graph_code:
            # Extract code from markdown code block
            start = graph_code.find("```python") + 9
            end = graph_code.find("```", start)
            if end > start:
                graph_code = graph_code[start:end].strip()
        elif "```" in graph_code:
            # Generic code block
            start = graph_code.find("```") + 3
            end = graph_code.find("```", start)
            if end > start:
                graph_code = graph_code[start:end].strip()
        
        # Write documentation file
        docs_file.write_text(docs_response.strip(), encoding='utf-8')
        console.print(f"[green]✓ Created documentation: {docs_file}[/green]")
        
        # Write graph script
        graph_file.write_text(graph_code.strip(), encoding='utf-8')
        graph_file.chmod(0o755)  # Make executable
        console.print(f"[green]✓ Created graph script: {graph_file}[/green]")
        
        # Final summary
        console.print("\n[bold green]✓ Repository documentation complete![/bold green]")
        console.print(f"[green]✓ Documentation: {docs_file}[/green]")
        console.print(f"[green]✓ Graph script: {graph_file}[/green]")
        console.print("\n[cyan]To generate the architecture diagram, run:[/cyan]")
        console.print(f"[dim]  python {graph_file}[/dim]")
        
        return True
        
    except Exception as e:
        console.print(f"\n[red]Error during documentation generation: {e}[/red]")
        
        # Clean up on error
        try:
            if repo_dir.exists():
                shutil.rmtree(repo_dir)
        except Exception:
            pass
        
        return False
