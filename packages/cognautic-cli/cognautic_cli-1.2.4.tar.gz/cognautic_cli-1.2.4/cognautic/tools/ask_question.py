"""
Ask Question Tool - Allows AI to ask clarifying questions to the user
"""

from typing import Dict, Any, List
from .base import BaseTool, ToolResult, PermissionLevel
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()


class AskQuestionTool(BaseTool):
    """Tool for AI to ask clarifying questions when confused"""
    
    def __init__(self):
        super().__init__(
            name="ask_question",
            description="Ask the user a clarifying question when confused or uncertain",
            permission_level=PermissionLevel.READ_ONLY
        )
        self.enabled = False  # Disabled by default
    
    def enable(self):
        """Enable the ask question feature"""
        self.enabled = True
    
    def disable(self):
        """Disable the ask question feature"""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if ask question feature is enabled"""
        return self.enabled
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities this tool provides"""
        return [
            "ask_question - Ask user a clarifying question with 2-3 AI-provided options plus automatic 'Something else' for custom input"
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the ask question tool
        
        Parameters:
        - question: The question to ask the user
        - option1: First option
        - option2: Second option
        - option3: Optional third option (if not provided, only 2 options will be shown)
        """
        if not self.enabled:
            return ToolResult(
                success=False,
                error="Ask question feature is disabled. Enable it with /askq on"
            )
        
        question = kwargs.get('question')
        option1 = kwargs.get('option1')
        option2 = kwargs.get('option2')
        option3 = kwargs.get('option3')  # Optional third option
        
        if not question:
            return ToolResult(
                success=False,
                error="Question is required"
            )
        
        if not option1 or not option2:
            return ToolResult(
                success=False,
                error="At least two options (option1 and option2) are required"
            )
        
        try:
            # Display the question in a nice panel
            console.print()
            console.print(Panel(
                f"[bold yellow]🤔 AI has a question:[/bold yellow]\n\n{question}",
                border_style="yellow",
                padding=(1, 2)
            ))
            
            # Display options
            console.print("\n[bold cyan]Please choose an option:[/bold cyan]")
            console.print(f"  [bold]1.[/bold] {option1}")
            console.print(f"  [bold]2.[/bold] {option2}")
            
            # Determine valid choices based on whether option3 is provided
            valid_choices = ["1", "2"]
            if option3:
                console.print(f"  [bold]3.[/bold] {option3}")
                valid_choices.append("3")
            
            # Always add "Something else" as the last option
            something_else_num = "4" if option3 else "3"
            console.print(f"  [bold]{something_else_num}.[/bold] Something else")
            valid_choices.append(something_else_num)
            
            # Get user's choice
            while True:
                choice = Prompt.ask(
                    "\n[bold]Your choice[/bold]",
                    choices=valid_choices,
                    default="1"
                )
                
                if choice == "1":
                    answer = option1
                    was_custom = False
                    break
                elif choice == "2":
                    answer = option2
                    was_custom = False
                    break
                elif choice == "3" and option3:
                    answer = option3
                    was_custom = False
                    break
                elif choice == something_else_num:
                    # User chose "Something else", ask for custom input
                    custom_answer = Prompt.ask(
                        "\n[bold]Please provide your answer[/bold]"
                    )
                    if custom_answer.strip():
                        answer = custom_answer.strip()
                        was_custom = True
                        break
                    else:
                        console.print("[yellow]Please provide a valid answer[/yellow]")
            
            console.print(f"\n[green]✓ You selected: {answer}[/green]\n")
            
            return ToolResult(
                success=True,
                data={
                    "question": question,
                    "answer": answer,
                    "was_custom": was_custom,
                    "inject_as_user_message": True,  # Special flag to inject answer as user message
                    "user_message": f"My answer: {answer}"  # The message to inject
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to ask question: {str(e)}"
            )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "ask_question",
                "description": "Ask the user a clarifying question when confused or uncertain. Use this when you have multiple options and need user guidance.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question to ask the user"
                        },
                        "option1": {
                            "type": "string",
                            "description": "First potential path or option"
                        },
                        "option2": {
                            "type": "string",
                            "description": "Second potential path or option"
                        },
                        "option3": {
                            "type": "string",
                            "description": "Optional third potential path or option"
                        }
                    },
                    "required": ["question", "option1", "option2"]
                }
            }
        }
