"""
Rules management for Cognautic CLI
Handles workspace-specific and global rules for AI behavior
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class RulesManager:
    """Manages workspace and global rules for AI behavior"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".cognautic"
        self.global_rules_file = self.config_dir / "global_rules.json"
        self.workspace_rules_cache = {}
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize global rules file if it doesn't exist
        if not self.global_rules_file.exists():
            self._save_global_rules([])
    
    def _get_workspace_rules_file(self, workspace_path: Optional[str] = None) -> Path:
        """Get the workspace rules file path"""
        if workspace_path:
            workspace = Path(workspace_path).resolve()
        else:
            workspace = Path.cwd()
        
        return workspace / ".cognautic_rules.json"
    
    def _load_global_rules(self) -> List[Dict[str, Any]]:
        """Load global rules from file"""
        try:
            if self.global_rules_file.exists():
                with open(self.global_rules_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            console.print(f"⚠️ Error loading global rules: {e}", style="yellow")
            return []
    
    def _save_global_rules(self, rules: List[Dict[str, Any]]):
        """Save global rules to file"""
        try:
            with open(self.global_rules_file, 'w') as f:
                json.dump(rules, f, indent=2)
        except Exception as e:
            console.print(f"❌ Error saving global rules: {e}", style="red")
    
    def _load_workspace_rules(self, workspace_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load workspace-specific rules"""
        rules_file = self._get_workspace_rules_file(workspace_path)
        
        try:
            if rules_file.exists():
                with open(rules_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            console.print(f"⚠️ Error loading workspace rules: {e}", style="yellow")
            return []
    
    def _save_workspace_rules(self, rules: List[Dict[str, Any]], workspace_path: Optional[str] = None):
        """Save workspace-specific rules"""
        rules_file = self._get_workspace_rules_file(workspace_path)
        
        try:
            with open(rules_file, 'w') as f:
                json.dump(rules, f, indent=2)
            console.print(f"✅ Workspace rules saved to: {rules_file}", style="green")
        except Exception as e:
            console.print(f"❌ Error saving workspace rules: {e}", style="red")
    
    def add_global_rule(self, rule: str, description: str = "") -> bool:
        """Add a global rule"""
        rules = self._load_global_rules()
        
        # Check if rule already exists
        for existing_rule in rules:
            if existing_rule.get('rule') == rule:
                console.print("⚠️ This rule already exists in global rules", style="yellow")
                return False
        
        rules.append({
            'rule': rule,
            'description': description,
            'type': 'global'
        })
        
        self._save_global_rules(rules)
        console.print("✅ Global rule added successfully", style="green")
        return True
    
    def add_workspace_rule(self, rule: str, description: str = "", workspace_path: Optional[str] = None) -> bool:
        """Add a workspace-specific rule"""
        rules = self._load_workspace_rules(workspace_path)
        
        # Check if rule already exists
        for existing_rule in rules:
            if existing_rule.get('rule') == rule:
                console.print("⚠️ This rule already exists in workspace rules", style="yellow")
                return False
        
        rules.append({
            'rule': rule,
            'description': description,
            'type': 'workspace'
        })
        
        self._save_workspace_rules(rules, workspace_path)
        console.print("✅ Workspace rule added successfully", style="green")
        return True
    
    def remove_global_rule(self, rule_index: int) -> bool:
        """Remove a global rule by index"""
        rules = self._load_global_rules()
        
        if 0 <= rule_index < len(rules):
            removed = rules.pop(rule_index)
            self._save_global_rules(rules)
            console.print(f"✅ Removed global rule: {removed['rule']}", style="green")
            return True
        else:
            console.print("❌ Invalid rule index", style="red")
            return False
    
    def remove_workspace_rule(self, rule_index: int, workspace_path: Optional[str] = None) -> bool:
        """Remove a workspace rule by index"""
        rules = self._load_workspace_rules(workspace_path)
        
        if 0 <= rule_index < len(rules):
            removed = rules.pop(rule_index)
            self._save_workspace_rules(rules, workspace_path)
            console.print(f"✅ Removed workspace rule: {removed['rule']}", style="green")
            return True
        else:
            console.print("❌ Invalid rule index", style="red")
            return False
    
    def list_global_rules(self) -> List[Dict[str, Any]]:
        """List all global rules"""
        return self._load_global_rules()
    
    def list_workspace_rules(self, workspace_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all workspace rules"""
        return self._load_workspace_rules(workspace_path)
    
    def get_all_rules(self, workspace_path: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get both global and workspace rules"""
        return {
            'global': self._load_global_rules(),
            'workspace': self._load_workspace_rules(workspace_path)
        }
    
    def get_rules_for_ai(self, workspace_path: Optional[str] = None) -> str:
        """Get formatted rules for AI context"""
        all_rules = self.get_all_rules(workspace_path)
        
        rules_text = []
        
        # Add global rules
        if all_rules['global']:
            rules_text.append("# Global Rules")
            for i, rule in enumerate(all_rules['global'], 1):
                rules_text.append(f"{i}. {rule['rule']}")
                if rule.get('description'):
                    rules_text.append(f"   Description: {rule['description']}")
        
        # Add workspace rules
        if all_rules['workspace']:
            if rules_text:
                rules_text.append("")
            rules_text.append("# Workspace Rules")
            for i, rule in enumerate(all_rules['workspace'], 1):
                rules_text.append(f"{i}. {rule['rule']}")
                if rule.get('description'):
                    rules_text.append(f"   Description: {rule['description']}")
        
        return "\n".join(rules_text) if rules_text else ""
    
    def display_rules(self, workspace_path: Optional[str] = None):
        """Display all rules in a formatted table"""
        all_rules = self.get_all_rules(workspace_path)
        
        # Display global rules
        if all_rules['global']:
            console.print(Panel.fit("🌍 Global Rules", style="bold blue"))
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=4)
            table.add_column("Rule", style="white")
            table.add_column("Description", style="dim")
            
            for i, rule in enumerate(all_rules['global']):
                table.add_row(
                    str(i),
                    rule['rule'],
                    rule.get('description', '')
                )
            
            console.print(table)
            console.print()
        else:
            console.print("INFO: No global rules defined", style="dim")
            console.print()
        
        # Display workspace rules
        if all_rules['workspace']:
            workspace_display = workspace_path or os.getcwd()
            console.print(Panel.fit(f"📁 Workspace Rules ({workspace_display})", style="bold green"))
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=4)
            table.add_column("Rule", style="white")
            table.add_column("Description", style="dim")
            
            for i, rule in enumerate(all_rules['workspace']):
                table.add_row(
                    str(i),
                    rule['rule'],
                    rule.get('description', '')
                )
            
            console.print(table)
        else:
            console.print(f"INFO No workspace rules defined for current workspace", style="dim")
    
    def clear_global_rules(self) -> bool:
        """Clear all global rules"""
        self._save_global_rules([])
        console.print("INFO: All global rules cleared", style="green")
        return True
    
    def clear_workspace_rules(self, workspace_path: Optional[str] = None) -> bool:
        """Clear all workspace rules"""
        self._save_workspace_rules([], workspace_path)
        console.print("INFO: All workspace rules cleared", style="green")
        return True
