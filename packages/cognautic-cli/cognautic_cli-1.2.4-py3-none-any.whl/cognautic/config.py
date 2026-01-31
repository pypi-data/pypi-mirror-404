"""
Configuration management for Cognautic CLI
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import keyring
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

class ConfigManager:
    """Manages configuration and secure API key storage"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".cognautic"
        self.config_file = self.config_dir / "config.json"
        self.api_keys_file = self.config_dir / "api_keys.json"
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        
        # Default configuration
        self.default_config = {
            "default_provider": "openai",
            "default_model": "gpt-4",
            "websocket_port": 8765,
            "max_tokens": 4096,
            "temperature": 0.7,
            "auto_save": True,
            "verbose_logging": False,
            "provider_models": {},  # Store model selection per provider
            "provider_endpoints": {}  # Store endpoint overrides per provider
        }
        
        # Initialize configuration
        self._init_config()
        
        # Initialize encryption key
        self._init_encryption()
    
    def _init_config(self):
        """Initialize configuration file with defaults"""
        if not self.config_file.exists():
            self._save_config(self.default_config)
    
    def _init_encryption(self):
        """Initialize encryption for API keys"""
        try:
            # Try to get existing key from keyring
            key = keyring.get_password("cognautic", "encryption_key")
            if not key:
                # Generate new key
                key = Fernet.generate_key().decode()
                keyring.set_password("cognautic", "encryption_key", key)
            
            self.cipher = Fernet(key.encode())
        except Exception:
            # Silently fallback to no encryption if keyring is not available
            self.cipher = None
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception:
            return self.default_config.copy()
    
    def get_config_value(self, key: str) -> Any:
        """Get a specific configuration value"""
        config = self.get_config()
        return config.get(key)
    
    def set_config(self, key: str, value: Any):
        """Set a configuration value"""
        config = self.get_config()
        config[key] = value
        self._save_config(config)
    
    def delete_config(self, key: str):
        """Delete a configuration key"""
        config = self.get_config()
        if key in config:
            del config[key]
            self._save_config(config)
    
    def reset_config(self):
        """Reset configuration to defaults"""
        self._save_config(self.default_config.copy())
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            console.print(f"❌ Error saving configuration: {e}", style="red")
    
    def set_api_key(self, provider: str, api_key: str):
        """Set API key for a provider"""
        try:
            # Load existing API keys
            api_keys = self._load_api_keys()
            
            # Encrypt the API key if encryption is available
            if self.cipher:
                encrypted_key = self.cipher.encrypt(api_key.encode()).decode()
                api_keys[provider] = encrypted_key
            else:
                api_keys[provider] = api_key
            
            # Save API keys
            self._save_api_keys(api_keys)
            
        except Exception as e:
            console.print(f"❌ Error saving API key: {e}", style="red")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider"""
        try:
            # Ensure provider is a string
            if not isinstance(provider, str):
                return None
                
            # First check environment variables
            env_var = f"{provider.upper()}_API_KEY"
            if env_var in os.environ:
                return os.environ[env_var]
            
            # Then check stored keys
            api_keys = self._load_api_keys()
            encrypted_key = api_keys.get(provider)
            
            if not encrypted_key:
                return None
            
            # Decrypt the API key if encryption is available
            if self.cipher:
                try:
                    return self.cipher.decrypt(encrypted_key.encode()).decode()
                except Exception:
                    # If decryption fails, assume it's unencrypted (backward compatibility)
                    return encrypted_key
            else:
                return encrypted_key
                
        except Exception as e:
            console.print(f"❌ Error loading API key: {e}", style="red")
            return None
    
    def has_api_key(self, provider: str) -> bool:
        """Check if API key exists for a provider"""
        return self.get_api_key(provider) is not None
    
    def list_providers(self) -> list:
        """List all configured providers"""
        api_keys = self._load_api_keys()
        env_providers = [
            key.replace('_API_KEY', '').lower() 
            for key in os.environ.keys() 
            if key.endswith('_API_KEY')
        ]
        return list(set(list(api_keys.keys()) + env_providers))
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from file"""
        try:
            if self.api_keys_file.exists():
                with open(self.api_keys_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def _save_api_keys(self, api_keys: Dict[str, str]):
        """Save API keys to file"""
        try:
            with open(self.api_keys_file, 'w') as f:
                json.dump(api_keys, f, indent=2)
            
            # Set secure file permissions
            os.chmod(self.api_keys_file, 0o600)
            
        except Exception as e:
            console.print(f"❌ Error saving API keys: {e}", style="red")
    
    def set_provider_model(self, provider: str, model: str):
        """Set the preferred model for a specific provider"""
        config = self.get_config()
        if 'provider_models' not in config:
            config['provider_models'] = {}
        config['provider_models'][provider] = model
        self._save_config(config)
    
    def get_provider_model(self, provider: str) -> Optional[str]:
        """Get the preferred model for a specific provider"""
        config = self.get_config()
        provider_models = config.get('provider_models', {})
        return provider_models.get(provider)

    def set_provider_endpoint(self, provider: str, base_url: str):
        """Set the endpoint/base URL override for a provider"""
        config = self.get_config()
        if 'provider_endpoints' not in config:
            config['provider_endpoints'] = {}
        config['provider_endpoints'][provider] = base_url
        self._save_config(config)

    def get_provider_endpoint(self, provider: str) -> Optional[str]:
        """Get the endpoint/base URL override for a provider, if any"""
        config = self.get_config()
        endpoints = config.get('provider_endpoints', {})
        return endpoints.get(provider)
    
    def interactive_setup(self):
        """Interactive setup wizard with improved UX"""
        console.print("🔧 Cognautic CLI Interactive Setup", style="bold blue")
        console.print("This wizard will help you configure API keys for AI providers.\n")
        
        providers = [
            ("openai", "OpenAI", "OPENAI_API_KEY", "https://platform.openai.com/api-keys"),
            ("anthropic", "Anthropic", "ANTHROPIC_API_KEY", "https://console.anthropic.com/settings/keys"),
            ("google", "Google Gemini", "GOOGLE_API_KEY", "https://aistudio.google.com/app/apikey"),
            ("together", "Together AI", "TOGETHER_API_KEY", "https://api.together.xyz/settings/api-keys"),
            ("openrouter", "OpenRouter", "OPENROUTER_API_KEY", "https://openrouter.ai/keys"),
            ("groq", "Groq", "GROQ_API_KEY", "https://console.groq.com/keys"),
            ("mistral", "Mistral AI", "MISTRAL_API_KEY", "https://console.mistral.ai/api-keys"),
            ("deepseek", "DeepSeek", "DEEPSEEK_API_KEY", "https://platform.deepseek.com/api_keys"),
        ]
        
        while True:
            console.print("\n[bold cyan]Available Providers:[/bold cyan]")
            for i, (provider_id, provider_name, _, _) in enumerate(providers, 1):
                # Check if already configured
                is_configured = self.has_api_key(provider_id)
                status = "[green]✓ Configured[/green]" if is_configured else "[dim]Not configured[/dim]"
                console.print(f"  {i}. {provider_name:20} {status}")
            
            console.print(f"\n  {len(providers) + 1}. [yellow]Set default provider[/yellow]")
            console.print(f"  {len(providers) + 2}. [green]Finish setup[/green]")
            
            choice = Prompt.ask(
                "\n[bold]Select a provider to configure (or option)[/bold]",
                default=str(len(providers) + 2)
            )
            
            try:
                choice_num = int(choice)
            except ValueError:
                console.print("[red]Invalid choice. Please enter a number.[/red]")
                continue
            
            # Finish setup
            if choice_num == len(providers) + 2:
                break
            
            # Set default provider
            elif choice_num == len(providers) + 1:
                configured_providers = self.list_providers()
                if not configured_providers:
                    console.print("[yellow]No providers configured yet. Please configure at least one provider first.[/yellow]")
                    continue
                
                console.print("\n[bold cyan]Configured Providers:[/bold cyan]")
                for i, prov in enumerate(configured_providers, 1):
                    console.print(f"  {i}. {prov}")
                
                default_choice = Prompt.ask(
                    "\n[bold]Select default provider number[/bold]",
                    default="1"
                )
                
                try:
                    default_idx = int(default_choice) - 1
                    if 0 <= default_idx < len(configured_providers):
                        default_provider = configured_providers[default_idx]
                        self.set_config("default_provider", default_provider)
                        console.print(f"[green]✅ Default provider set to {default_provider}[/green]")
                    else:
                        console.print("[red]Invalid selection.[/red]")
                except ValueError:
                    console.print("[red]Invalid input.[/red]")
            
            # Configure a provider
            elif 1 <= choice_num <= len(providers):
                provider_id, provider_name, env_var, docs_url = providers[choice_num - 1]
                
                console.print(f"\n[bold cyan]Configuring {provider_name}[/bold cyan]")
                console.print(f"[dim]Get your API key from: {docs_url}[/dim]")
                console.print(f"[dim]Environment variable: {env_var}[/dim]\n")
                
                # Check if already configured
                if self.has_api_key(provider_id):
                    if not Confirm.ask(f"{provider_name} is already configured. Reconfigure?", default=False):
                        continue
                
                api_key = Prompt.ask(f"Enter {provider_name} API key (or press Enter to skip)", password=True)
                
                if api_key and api_key.strip():
                    self.set_api_key(provider_id, api_key.strip())
                    console.print(f"[green]✅ {provider_name} API key saved[/green]")
                else:
                    console.print(f"[yellow]⏭️  Skipped {provider_name}[/yellow]")
            
            else:
                console.print("[red]Invalid choice. Please select a valid number.[/red]")
        
        # Final summary
        configured_providers = self.list_providers()
        if configured_providers:
            console.print("\n[bold green]🎉 Setup complete![/bold green]")
            console.print(f"[green]Configured providers: {', '.join(configured_providers)}[/green]")
            
            default_provider = self.get_config_value("default_provider")
            if default_provider:
                console.print(f"[green]Default provider: {default_provider}[/green]")
            
            console.print("\n[bold]Next steps:[/bold]")
            console.print("  • Start chatting: [cyan]cognautic chat[/cyan]")
            console.print("  • Get help: [cyan]cognautic --help[/cyan]")
        else:
            console.print("\n[yellow]No providers configured. Run /setup again when you're ready.[/yellow]")
