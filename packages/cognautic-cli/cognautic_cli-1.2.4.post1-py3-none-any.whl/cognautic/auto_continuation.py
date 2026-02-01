"""
Auto-continuation module for Cognautic CLI
Ensures AI automatically continues after tool execution without manual intervention
"""

import asyncio
from typing import AsyncGenerator, Dict, Any, List


class AutoContinuationManager:
    """Manages automatic continuation of AI responses after tool execution"""
    
    def __init__(self, max_iterations: int = 50):
        """
        Initialize auto-continuation manager
        
        Args:
            max_iterations: Maximum number of auto-continuation iterations to prevent infinite loops
        """
        self.max_iterations = max_iterations
        self.iteration_count = 0
        self.previous_tool_types = []  # Track previous tool types to detect repetitions
        
    def reset(self):
        """Reset iteration counter for new conversation turn"""
        self.iteration_count = 0
        self.previous_tool_types = []
    
    def should_continue(
        self, 
        tool_results: List[Dict[str, Any]], 
        has_end_response: bool,
        ai_response: str = ""
    ) -> bool:
        """
        Determine if AI should automatically continue
        
        SIMPLIFIED LOGIC: Always continue EXCEPT when end_response is called
        This ensures AI completes tasks without manual intervention
        
        Args:
            tool_results: List of tool execution results
            has_end_response: Whether end_response tool was called
            ai_response: The AI's text response (to detect promises without execution)
            
        Returns:
            True if should continue, False otherwise
        """
        # RULE 1: Don't continue if end_response was explicitly called
        # This is the ONLY condition that stops auto-continuation
        if has_end_response:
            return False
        
        # RULE 2: Don't continue if max iterations reached (safety limit)
        if self.iteration_count >= self.max_iterations:
            return False
        
        # RULE 3: Check if AI said it would use tools but didn't execute them
        # This handles the scenario where AI says "I will use X tool" but doesn't
        if not tool_results and ai_response:
            promise_indicators = [
                "i will use",
                "i can use",
                "let me use",
                "i'll use",
                "using the",
                "i will call",
                "i'll call",
                "let me call",
                "i can help you with that",
                "i will list",
                "i will find",
                "i will search",
                "i will check",
                "i will analyze",
                "i will show",
                "i will count"
            ]
            
            ai_lower = ai_response.lower()
            
            # Check if AI promised to use tools
            promised_to_use_tools = any(indicator in ai_lower for indicator in promise_indicators)
            
            # Check if AI mentioned specific tools
            tool_mentions = [
                "code_navigation",
                "directory_context",
                "file_operations",
                "web_search",
                "command_runner",
                "tool"
            ]
            mentioned_tools = any(tool in ai_lower for tool in tool_mentions)
            
            # If AI promised to use tools or mentioned specific tools but didn't execute any
            if promised_to_use_tools or mentioned_tools:
                self.iteration_count += 1
                return True
        
        # RULE 4: If no tools were executed and no promises detected, still continue
        # The AI might need another chance to complete the task
        if not tool_results:
            self.iteration_count += 1
            return True
        
        # RULE 5: If ANY tools were executed, ALWAYS continue
        # Let the AI decide when it's done by calling end_response
        # NOTE: ask_question is special - it continues with the user's answer injected
        self.iteration_count += 1
        return True
    
    def build_continuation_prompt(
        self, 
        tool_results: List[Dict[str, Any]],
        ai_response: str = ""
    ) -> str:
        """
        Build an appropriate continuation prompt based on tool results
        
        Args:
            tool_results: List of tool execution results
            ai_response: The AI's text response (to provide context)
            
        Returns:
            Continuation prompt string
        """
        # Special case: ask_question tool - inject user's answer
        for result in tool_results:
            tool_name = result.get('tool', result.get('type', ''))
            if tool_name == 'ask_question' or 'ask_question' in str(tool_name):
                # Extract the answer from the result
                data = result.get('data', {})
                if isinstance(data, dict):
                    answer = data.get('answer', '')
                    if answer:
                        # Return the answer as if the user said it
                        return f"My answer: {answer}"
        
        # Special case: AI said it would use tools but didn't
        if not tool_results and ai_response:
            return """You said you would use a tool, but you didn't actually execute it.

CRITICAL: You MUST include the actual JSON tool call in your response, not just say you will do it.

For example, if you want to use code_navigation to list symbols, you MUST include:

```json
{
  "tool_code": "code_navigation",
  "args": {
    "operation": "list_symbols",
    "file_path": "main.py"
  }
}
```

Now execute the tool you mentioned:"""
        
        # Categorize tool results
        has_file_reads = any(r.get('type') == 'file_read' for r in tool_results)
        has_file_ops = any(r.get('type') in ['file_op', 'file_write'] for r in tool_results)
        has_commands = any(r.get('type') == 'command' for r in tool_results)
        has_web_search = any(r.get('type') in ['web_search', 'web_fetch'] for r in tool_results)
        
        # Build context summary
        context_parts = []
        for result in tool_results:
            result_type = result.get('type', 'unknown')
            
            if result_type == 'command':
                cmd = result.get('command', 'unknown')
                output = result.get('output', '')
                # Truncate long outputs
                if len(output) > 500:
                    output = output[:500] + "... [truncated]"
                context_parts.append(f"Command '{cmd}' executed with output: {output}")
                
            elif result_type in ['file_op', 'file_write']:
                context_parts.append("File operation completed successfully")
                
            elif result_type == 'file_read':
                file_path = result.get('file_path', 'unknown')
                context_parts.append(f"Read file: {file_path}")
                
            elif result_type == 'web_search':
                query = result.get('query', 'unknown')
                results_count = len(result.get('results', []))
                context_parts.append(f"Web search for '{query}' returned {results_count} results")
        
        context = "\n".join(context_parts)
        
        # Build appropriate prompt based on tool types
        if has_file_reads and not has_file_ops and not has_commands:
            # Special case: only file reads, AI needs to analyze the content
            files_read = [r.get('file_path', 'unknown') for r in tool_results if r.get('type') == 'file_read']
            files_list = '\n'.join(f"- {f}" for f in files_read)
            return f"""You have successfully read the following files:

{files_list}

The file contents are provided above. Now analyze them and answer the user's question based on the ACTUAL content you just read.

IMPORTANT: Use the actual file content provided above, not assumptions. Provide a detailed analysis based on what you see in the files.

Your analysis:"""
        
        elif has_web_search:
            return f"""The web search has been completed. Based on the results:

{context}

Now CREATE the files you researched. You have the information you need, so:
1. Create all necessary files for the application
2. Write complete, functional code based on what you found
3. When you have created all files, call the end_response tool
4. DO NOT search again unless absolutely necessary

Create the files now:"""
        
        elif has_file_ops and not has_commands:
            return f"""Files have been created/modified:

{context}

Continue with the next steps:
1. If you need to create MORE files, create them now
2. If you need to install dependencies (npm install, pip install, etc.), run the commands now
3. If you need to configure anything else, do it now
4. When EVERYTHING is done, call the end_response tool

Continue now:"""
        
        elif has_commands:
            return f"""Commands have been executed:

{context}

Continue with the next steps:
1. If there are errors, fix them
2. If more setup is needed, do it now
3. If everything is working, provide final instructions
4. When EVERYTHING is done, call the end_response tool

Continue now:"""
        
        else:
            return f"""Tool execution completed:

{context}

Continue with any remaining work, then call end_response when fully done.

Continue now:"""
    
    async def generate_continuation(
        self,
        ai_provider,
        messages: List[Dict[str, str]],
        tool_results: List[Dict[str, Any]],
        model: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Generate continuation response from AI
        
        Args:
            ai_provider: AI provider instance
            messages: Conversation history
            tool_results: Tool execution results
            model: Model name
            config: Configuration dict
            
        Returns:
            AI's continuation response
        """
        try:
            # Build tool results summary with actual content
            # Use very clear formatting for providers that flatten messages (like Google)
            tool_results_text = ""
            for result in tool_results:
                if result.get("type") == "file_read":
                    # Include the actual file content with prominent headers
                    file_path = result.get("file_path", "unknown")
                    content = result.get("content", "")
                    tool_results_text += f"\n\n{'='*70}\n"
                    tool_results_text += f"FILE CONTENT: {file_path}\n"
                    tool_results_text += f"{'='*70}\n"
                    tool_results_text += f"{content}\n"
                    tool_results_text += f"{'='*70}\n"
                    tool_results_text += f"END OF FILE: {file_path}\n"
                    tool_results_text += f"{'='*70}\n"
                elif result.get("type") == "command":
                    # Include command output
                    command = result.get("command", "unknown")
                    output = result.get("output", "")
                    tool_results_text += f"\n\n{'='*70}\n"
                    tool_results_text += f"COMMAND OUTPUT: {command}\n"
                    tool_results_text += f"{'='*70}\n"
                    tool_results_text += f"{output}\n"
                    tool_results_text += f"{'='*70}\n"
                elif result.get("type") == "web_search":
                    # Include web search results
                    query = result.get("query", "unknown")
                    results = result.get("results", [])
                    
                    tool_results_text += f"\n\n{'='*70}\n"
                    tool_results_text += f"WEB SEARCH RESULTS: {query}\n"
                    tool_results_text += f"{'='*70}\n"
                    
                    if isinstance(results, list):
                        for i, item in enumerate(results):
                            tool_results_text += f"Result {i+1}:\n"
                            tool_results_text += f"Title: {item.get('title', 'N/A')}\n"
                            tool_results_text += f"URL: {item.get('url', 'N/A')}\n"
                            tool_results_text += f"Snippet: {item.get('snippet', 'N/A')}\n"
                            tool_results_text += "-" * 30 + "\n"
                    elif isinstance(results, dict):
                         # Handle fetch_url_content or other single-object returns
                         tool_results_text += str(results) + "\n"
                         
                    tool_results_text += f"{'='*70}\n"
            
            # Build continuation prompt
            continuation_prompt = self.build_continuation_prompt(tool_results)
            
            # Combine tool results with continuation prompt
            full_prompt = tool_results_text + "\n\n" + continuation_prompt if tool_results_text else continuation_prompt
            
            # Add to messages
            continuation_messages = messages + [
                {"role": "assistant", "content": "I'll continue with the task."},
                {"role": "user", "content": full_prompt}
            ]
            
            # Generate response
            max_tokens = config.get("max_tokens")
            if max_tokens == 0 or max_tokens == -1:
                max_tokens = None
            
            response = await ai_provider.generate_response(
                messages=continuation_messages,
                model=model,
                max_tokens=max_tokens or 16384,
                temperature=config.get("temperature", 0.7)
            )
            
            # Ensure we got a response
            if not response or not response.strip():
                # If empty response, return a simple continuation message
                return "Continuing with the task..."
            
            return response
        except Exception as e:
            # Log error and return a fallback message
            print(f"[Auto-continuation error: {e}]")
            return "Continuing with the task..."
