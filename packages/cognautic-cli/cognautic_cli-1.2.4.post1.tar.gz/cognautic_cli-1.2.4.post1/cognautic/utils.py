"""
Utility functions for Cognautic CLI
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def ensure_directory(path: str) -> Path:
    """Ensure directory exists, create if it doesn't"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def is_restricted_directory(path: str) -> tuple[bool, Optional[str]]:
    """
    Check if a directory is restricted for running Cognautic CLI.
    
    Restricted directories include:
    - User home directory (Linux/Mac: ~, Windows: C:\\Users\\username)
    - /man directory on Linux
    - C:\\ drive root on Windows
    
    Args:
        path: The directory path to check
        
    Returns:
        A tuple of (is_restricted: bool, reason: Optional[str])
    """
    try:
        # Resolve to absolute path
        abs_path = Path(path).resolve()
        
        # Get home directory
        home_dir = Path.home().resolve()
        
        # Check if path is the home directory
        if abs_path == home_dir:
            return True, f"Cannot run Cognautic CLI in your home directory ({home_dir}). Please navigate to a specific project directory."
        
        # Check for /man directory on Linux/Unix
        if sys.platform in ['linux', 'darwin']:
            man_dir = Path('/man').resolve()
            if abs_path == man_dir or str(abs_path).startswith('/man/'):
                return True, "Cannot run Cognautic CLI in the /man directory."
        
        # Check for C:\ root on Windows
        if sys.platform == 'win32':
            # Check if it's a drive root (e.g., C:\, D:\)
            if abs_path.parent == abs_path:  # This is true for drive roots
                drive_letter = str(abs_path).upper()
                if drive_letter.startswith('C:'):
                    return True, f"Cannot run Cognautic CLI in the C:\\ drive root. Please navigate to a specific project directory."
        
        return False, None
        
    except Exception as e:
        # If there's an error resolving the path, allow it and let other validation handle it
        console.print(f"[dim]Warning: Could not validate directory restriction: {e}[/dim]")
        return False, None


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON file safely"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        console.print(f"❌ Invalid JSON in {file_path}: {e}", style="red")
        return {}


def save_json_file(file_path: str, data: Dict[str, Any], indent: int = 2):
    """Save data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    except Exception as e:
        console.print(f"❌ Error saving JSON to {file_path}: {e}", style="red")


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """Load YAML file safely"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        console.print(f"❌ Invalid YAML in {file_path}: {e}", style="red")
        return {}


def save_yaml_file(file_path: str, data: Dict[str, Any]):
    """Save data to YAML file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
    except Exception as e:
        console.print(f"❌ Error saving YAML to {file_path}: {e}", style="red")


def detect_project_type(project_path: str) -> Optional[str]:
    """Detect project type based on files present"""
    path = Path(project_path)
    
    # Check for specific files that indicate project type
    indicators = {
        'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile'],
        'node': ['package.json', 'yarn.lock', 'package-lock.json'],
        'java': ['pom.xml', 'build.gradle', 'build.xml'],
        'go': ['go.mod', 'go.sum'],
        'rust': ['Cargo.toml', 'Cargo.lock'],
        'php': ['composer.json', 'composer.lock'],
        'ruby': ['Gemfile', 'Gemfile.lock'],
        'dotnet': ['*.csproj', '*.sln', 'project.json'],
        'docker': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml']
    }
    
    for project_type, files in indicators.items():
        for file_pattern in files:
            if '*' in file_pattern:
                # Handle glob patterns
                if list(path.glob(file_pattern)):
                    return project_type
            else:
                # Handle exact file names
                if (path / file_pattern).exists():
                    return project_type
    
    # Check by file extensions
    extensions = set()
    for file_path in path.rglob('*'):
        if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
            extensions.add(file_path.suffix.lower())
    
    extension_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.rb': 'ruby',
        '.cs': 'csharp',
        '.cpp': 'cpp',
        '.c': 'c'
    }
    
    for ext, lang in extension_map.items():
        if ext in extensions:
            return lang
    
    return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def create_progress_bar(description: str = "Processing..."):
    """Create a progress bar with spinner"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    )


def display_table(data: List[Dict[str, Any]], title: str = None, columns: List[str] = None):
    """Display data in a formatted table"""
    if not data:
        console.print("No data to display", style="yellow")
        return
    
    # Auto-detect columns if not provided
    if not columns:
        columns = list(data[0].keys())
    
    table = Table(title=title)
    
    # Add columns
    for column in columns:
        table.add_column(column.replace('_', ' ').title())
    
    # Add rows
    for row in data:
        table.add_row(*[str(row.get(col, '')) for col in columns])
    
    console.print(table)


def validate_api_key(api_key: str, provider: str) -> bool:
    """Validate API key format for different providers"""
    if not api_key:
        return False
    
    # Basic validation patterns
    patterns = {
        'openai': lambda k: k.startswith('sk-') and len(k) > 20,
        'anthropic': lambda k: k.startswith('sk-ant-') and len(k) > 20,
        'google': lambda k: len(k) > 20,  # Google API keys vary in format
        'together': lambda k: len(k) > 20,
        'openrouter': lambda k: k.startswith('sk-or-') and len(k) > 20
    }
    
    validator = patterns.get(provider.lower())
    if validator:
        return validator(api_key)
    
    # Default validation - just check length
    return len(api_key) > 10


def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    return {
        'platform': sys.platform,
        'python_version': sys.version,
        'python_executable': sys.executable,
        'working_directory': os.getcwd(),
        'home_directory': str(Path.home()),
        'environment_variables': dict(os.environ)
    }


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def parse_requirements_txt(file_path: str) -> List[Dict[str, str]]:
    """Parse requirements.txt file"""
    requirements = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse package name and version
                if '==' in line:
                    package, version = line.split('==', 1)
                    requirements.append({
                        'package': package.strip(),
                        'version': version.strip(),
                        'operator': '=='
                    })
                elif '>=' in line:
                    package, version = line.split('>=', 1)
                    requirements.append({
                        'package': package.strip(),
                        'version': version.strip(),
                        'operator': '>='
                    })
                elif '<=' in line:
                    package, version = line.split('<=', 1)
                    requirements.append({
                        'package': package.strip(),
                        'version': version.strip(),
                        'operator': '<='
                    })
                else:
                    requirements.append({
                        'package': line.strip(),
                        'version': None,
                        'operator': None
                    })
    
    except FileNotFoundError:
        console.print(f"❌ Requirements file not found: {file_path}", style="red")
    except Exception as e:
        console.print(f"❌ Error parsing requirements: {e}", style="red")
    
    return requirements


def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are installed"""
    required_packages = [
        'click', 'asyncio', 'websockets', 'aiohttp', 'pydantic', 'rich',
        'requests', 'beautifulsoup4', 'cryptography', 'keyring'
    ]
    
    optional_packages = [
        'openai', 'anthropic', 'google-generativeai', 'together',
        'gitpython', 'psutil'
    ]
    
    status = {'required': {}, 'optional': {}}
    
    for package in required_packages:
        try:
            __import__(package)
            status['required'][package] = True
        except ImportError:
            status['required'][package] = False
    
    for package in optional_packages:
        try:
            __import__(package)
            status['optional'][package] = True
        except ImportError:
            status['optional'][package] = False
    
    return status
