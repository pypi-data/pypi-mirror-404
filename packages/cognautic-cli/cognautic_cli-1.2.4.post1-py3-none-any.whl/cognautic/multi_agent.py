"""
Multi-Agent Collaboration System

This module enables multiple AI models to collaborate in real-time on projects.
The workflow consists of:
1. Discussion Phase: Models discuss the task and identify issues
2. Planning Phase: Models split up the work among themselves
3. Execution Phase: Models work in real-time on their assigned tasks
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.text import Text

console = Console()


@dataclass
class AgentConfig:
    """Configuration for a single agent"""
    provider: str
    model: str
    name: str  # Display name like "Agent 1", "Agent 2"
    folder: Path  # Working directory for this agent


@dataclass
class AgentMessage:
    """A message from an agent during discussion"""
    agent_name: str
    content: str
    timestamp: datetime
    phase: str  # 'discussion', 'planning', 'execution'


@dataclass
class TaskAssignment:
    """A task assigned to an agent"""
    agent_name: str
    description: str
    files: List[str]
    priority: int


class MultiAgentOrchestrator:
    """Orchestrates collaboration between multiple AI agents"""
    
    def __init__(
        self,
        agents: List[AgentConfig],
        workspace: str,
        ai_engine,
        memory_manager=None
    ):
        self.agents = agents
        self.workspace = Path(workspace)
        self.ai_engine = ai_engine
        self.memory_manager = memory_manager
        self.conversation_history: List[AgentMessage] = []
        self.task_assignments: Dict[str, List[TaskAssignment]] = {
            agent.name: [] for agent in agents
        }
        
    async def run_collaboration(self, user_request: str) -> None:
        """
        Main entry point for multi-agent collaboration
        
        Args:
            user_request: The user's project request
        """
        console.print("\n[bold cyan]MULTI-AGENT: Multi-Agent Collaboration Mode Activated[/bold cyan]\n")
        console.print(f"[dim]Agents: {', '.join(agent.name for agent in self.agents)}[/dim]\n")
        
        # Phase 1: Discussion
        await self._discussion_phase(user_request)
        
        # Phase 2: Planning
        await self._planning_phase(user_request)
        
        # Phase 3: Execution
        await self._execution_phase(user_request)
        
        # Summary
        self._show_summary()
    
    async def _discussion_phase(self, user_request: str) -> None:
        """
        Phase 1: Agents discuss the task and identify potential issues
        """
        console.print("[bold yellow]Phase 1: Discussion[/bold yellow]\n")
        console.print("[dim]Agents will now discuss the task and identify potential issues...[/dim]\n")
        
        # Each agent analyzes the request and provides feedback
        for i, agent in enumerate(self.agents):
            # Create discussion prompt
            previous_discussion = self._format_discussion_history()
            
            if i == 0:
                # First agent starts the discussion
                prompt = f"""You are {agent.name}, an AI assistant collaborating with other AI models to complete a project.

IMPORTANT: This is the DISCUSSION phase. DO NOT create files, run commands, or use any tools. Just provide your analysis and thoughts in plain text.

USER REQUEST: {user_request}

This is a multi-agent collaboration. You are the first agent to speak. Please:
1. Analyze the user's request
2. Identify the main tasks that need to be completed
3. Point out any potential issues or challenges
4. Suggest an approach to tackle this project

Keep your response concise and focused. Other agents will respond after you.
Remember: NO TOOLS, just discussion!"""
            else:
                # Subsequent agents respond to previous discussion
                prompt = f"""You are {agent.name}, an AI assistant collaborating with other AI models to complete a project.

IMPORTANT: This is the DISCUSSION phase. DO NOT create files, run commands, or use any tools. Just provide your analysis and thoughts in plain text.

USER REQUEST: {user_request}

PREVIOUS DISCUSSION:
{previous_discussion}

Please:
1. Review what the previous agent(s) said
2. Add your perspective on the task
3. Point out anything they might have missed
4. Suggest improvements or alternative approaches
5. Identify any potential problems with their suggestions

Keep your response concise and focused.
Remember: NO TOOLS, just discussion!"""
            
            # Get agent's response
            console.print(f"[bold green]{agent.name}[/bold green] ({agent.provider}:{agent.model}):")
            
            response = await self._get_agent_response(agent, prompt)
            
            # Store in conversation history
            message = AgentMessage(
                agent_name=agent.name,
                content=response,
                timestamp=datetime.now(),
                phase='discussion'
            )
            self.conversation_history.append(message)
            
            # Display response
            console.print(Panel(response, border_style="green", padding=(1, 2)))
            console.print()
        
        console.print("[bold green]✓ Discussion phase complete[/bold green]\n")
    
    async def _planning_phase(self, user_request: str) -> None:
        """
        Phase 2: Agents split up the work among themselves
        """
        console.print("[bold yellow]Phase 2: Planning & Task Assignment[/bold yellow]\n")
        console.print("[dim]Agents will now divide the work among themselves...[/dim]\n")
        
        # Get the discussion summary
        discussion_summary = self._format_discussion_history()
        
        # Use the first agent as the "coordinator" to create initial task split
        coordinator = self.agents[0]
        
        planning_prompt = f"""You are {coordinator.name}, coordinating a multi-agent project.

IMPORTANT: This is the PLANNING phase. DO NOT create files or run commands. Just create the task assignment plan in JSON format.

USER REQUEST: {user_request}

DISCUSSION SUMMARY:
{discussion_summary}

AVAILABLE AGENTS:
{self._format_agent_list()}

Based on the discussion, please create a task assignment plan. For each agent, specify:
1. What they should work on
2. Which files they should create/modify
3. Priority (1=highest, 5=lowest)

Respond in JSON format:
{{
    "assignments": [
        {{
            "agent": "Agent 1",
            "description": "Task description",
            "files": ["file1.py", "file2.py"],
            "priority": 1
        }},
        ...
    ]
}}

Make sure all agents have meaningful work assigned. Split the work logically to avoid conflicts.
Remember: NO TOOLS in this phase, just provide the JSON plan!"""
        
        console.print(f"[bold green]{coordinator.name}[/bold green] is creating the task assignment plan...")
        
        response = await self._get_agent_response(coordinator, planning_prompt)
        
        # Parse task assignments
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                plan = json.loads(json_str)
                
                # Store assignments
                for assignment_data in plan.get('assignments', []):
                    agent_name = assignment_data['agent']
                    task = TaskAssignment(
                        agent_name=agent_name,
                        description=assignment_data['description'],
                        files=assignment_data.get('files', []),
                        priority=assignment_data.get('priority', 3)
                    )
                    
                    if agent_name in self.task_assignments:
                        self.task_assignments[agent_name].append(task)
                
                # Display task assignments
                self._display_task_assignments()
                
        except Exception as e:
            console.print(f"[red]Error parsing task assignments: {e}[/red]")
            console.print("[yellow]Proceeding with manual task distribution...[/yellow]")
            # Fallback: assign general tasks to each agent
            for agent in self.agents:
                task = TaskAssignment(
                    agent_name=agent.name,
                    description=f"Work on implementing features for: {user_request}",
                    files=[],
                    priority=3
                )
                self.task_assignments[agent.name].append(task)
        
        # Let other agents review and suggest modifications
        console.print("\n[dim]Other agents reviewing the plan...[/dim]\n")
        
        for agent in self.agents[1:]:
            review_prompt = f"""You are {agent.name}. Review this task assignment plan:

IMPORTANT: This is the PLANNING phase. DO NOT create files or run commands. Just provide your review and suggestions in plain text.

{self._format_task_assignments()}

Do you agree with this plan? If not, suggest specific changes. Keep your response brief.
Remember: NO TOOLS, just discussion!"""
            
            console.print(f"[bold green]{agent.name}[/bold green]:")
            review = await self._get_agent_response(agent, review_prompt)
            console.print(Panel(review, border_style="green", padding=(1, 2)))
            console.print()
            
            # Store review in conversation
            message = AgentMessage(
                agent_name=agent.name,
                content=review,
                timestamp=datetime.now(),
                phase='planning'
            )
            self.conversation_history.append(message)
        
        console.print("[bold green]✓ Planning phase complete[/bold green]\n")
    
    async def _execution_phase(self, user_request: str) -> None:
        """
        Phase 3: Agents work in real-time on their assigned tasks
        """
        console.print("[bold yellow]Phase 3: Real-time Execution[/bold yellow]\n")
        console.print("[dim]Agents are now working on their assigned tasks in parallel...[/dim]\n")
        
        # Import necessary modules for side-by-side display
        import queue
        import threading
        from rich.columns import Columns
        from rich.panel import Panel
        from rich.text import Text
        from rich.live import Live
        
        # Create buffers and queues for each agent
        agent_buffers = {}
        agent_queues = {}
        sentinel = object()  # Unique sentinel to signal end of stream
        
        for agent in self.agents:
            agent_buffers[agent.name] = ""
            agent_queues[agent.name] = queue.Queue()
        
        # Create async consumer tasks
        async def consume_queue(agent_name, q):
            response = ""
            while True:
                chunk = await asyncio.to_thread(q.get)
                if chunk is sentinel:
                    break
                response += chunk
                agent_buffers[agent_name] = response
            return response
        
        # Create producer threads for each agent
        def create_producer(agent, q):
            async def _run():
                try:
                    assignments = self.task_assignments.get(agent.name, [])
                    
                    if not assignments:
                        q.put(f"[yellow]No assignments for {agent.name}[/yellow]")
                        q.put(sentinel)
                        return
                    
                    # Build execution prompt
                    tasks_description = "\n".join([
                        f"- {task.description} (Priority: {task.priority})"
                        for task in sorted(assignments, key=lambda x: x.priority)
                    ])
                    
                    discussion_context = self._format_discussion_history()
                    
                    execution_prompt = f"""You are {agent.name}, working on a collaborative project.

USER REQUEST: {user_request}

YOUR ASSIGNED TASKS:
{tasks_description}

DISCUSSION CONTEXT:
{discussion_context}

WORKING DIRECTORY: {agent.folder}

Please complete your assigned tasks. You have access to file creation and editing tools.
All agents are working in the same shared workspace, so coordinate your file changes carefully.

IMPORTANT: DO NOT call the end_response tool! You are working in parallel with other agents. 
The system will automatically end when all agents complete their work.

Focus on your tasks and implement them properly. Be thorough and write clean, well-documented code."""
                    
                    # Stream the response
                    async for chunk in self._get_agent_response_stream(agent, execution_prompt, enable_tools=True):
                        q.put(chunk)
                    
                    # Store in conversation history
                    message = AgentMessage(
                        agent_name=agent.name,
                        content=agent_buffers.get(agent.name, ""),
                        timestamp=datetime.now(),
                        phase='execution'
                    )
                    self.conversation_history.append(message)
                    
                except Exception as e:
                    q.put(f"\n[red]Error: {str(e)}[/red]")
                finally:
                    q.put(sentinel)
            
            asyncio.run(_run())
        
        # Start producer threads
        for agent in self.agents:
            q = agent_queues[agent.name]
            threading.Thread(target=create_producer, args=(agent, q), daemon=True).start()
        
        # Create consumer tasks
        consumer_tasks = []
        for agent in self.agents:
            task = asyncio.create_task(consume_queue(agent.name, agent_queues[agent.name]))
            consumer_tasks.append(task)
        
        # Render function for live display
        def render_columns():
            panels = []
            term_width = console.size.width
            num_cols = len(self.agents)
            gap = 2
            col_width = max(30, int((term_width - (num_cols - 1) * gap) / num_cols))
            
            for agent in self.agents:
                content = agent_buffers.get(agent.name, "")
                # Truncate content if too long to avoid performance issues
                display_content = content[-2000:] if len(content) > 2000 else content
                text = Text(display_content, overflow="fold", no_wrap=False)
                title = f"{agent.name} ({agent.provider}:{agent.model[:20]})"
                panels.append(Panel(text, title=title, width=col_width, border_style="cyan"))
            
            return Columns(panels, equal=True, expand=False, padding=1)
        
        # Live render while agents work
        with Live(render_columns(), console=console, refresh_per_second=4, transient=True) as live:
            while any(not t.done() for t in consumer_tasks):
                live.update(render_columns())
                await asyncio.sleep(0.1)
            
            # Wait for all to complete
            await asyncio.gather(*consumer_tasks, return_exceptions=True)
            live.update(render_columns())
        
        # Print final static snapshot for scrollback
        console.print(render_columns())
        
        console.print("\n[bold green]✓ Execution phase complete[/bold green]\n")
    
    async def _agent_execute_tasks(self, agent: AgentConfig, user_request: str) -> None:
        """
        Execute tasks for a single agent
        """
        assignments = self.task_assignments.get(agent.name, [])
        
        if not assignments:
            console.print(f"[yellow]{agent.name} has no assignments[/yellow]")
            return
        
        # Build execution prompt
        tasks_description = "\n".join([
            f"- {task.description} (Priority: {task.priority})"
            for task in sorted(assignments, key=lambda x: x.priority)
        ])
        
        discussion_context = self._format_discussion_history()
        
        execution_prompt = f"""You are {agent.name}, working on a collaborative project.

USER REQUEST: {user_request}

YOUR ASSIGNED TASKS:
{tasks_description}

DISCUSSION CONTEXT:
{discussion_context}

WORKING DIRECTORY: {agent.folder}

Please complete your assigned tasks. You have access to file creation and editing tools.
All agents are working in the same shared workspace, so coordinate your file changes carefully.

Focus on your tasks and implement them properly. Be thorough and write clean, well-documented code."""
        
        console.print(f"\n[bold cyan]▶ {agent.name} starting work...[/bold cyan]")
        
        # Get agent to execute
        try:
            response = await self._get_agent_response(
                agent,
                execution_prompt,
                enable_tools=True
            )
            
            # Store execution log
            message = AgentMessage(
                agent_name=agent.name,
                content=response,
                timestamp=datetime.now(),
                phase='execution'
            )
            self.conversation_history.append(message)
            
            console.print(f"[bold green]✓ {agent.name} completed their tasks[/bold green]")
            
        except Exception as e:
            console.print(f"[red]Error during {agent.name} execution: {e}[/red]")
    
    async def _get_agent_response(
        self,
        agent: AgentConfig,
        prompt: str,
        enable_tools: bool = False
    ) -> str:
        """
        Get a response from a specific agent (non-streaming, for discussion/planning phases)
        This method calls providers DIRECTLY to avoid tool usage during discussion/planning
        """
        try:
            # For discussion and planning, call provider directly WITHOUT going through AI engine
            # This prevents the tool system from being activated
            provider_instance = self.ai_engine.providers.get(agent.provider)
            
            if not provider_instance:
                return f"[Error: Provider {agent.provider} not available]"
            
            # Create simple messages without system prompt (no tools)
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Respond concisely and clearly."},
                {"role": "user", "content": prompt}
            ]
            
            # Generate response directly from provider
            if hasattr(provider_instance, 'generate_response_stream'):
                # Use streaming if available and collect response
                full_response = ""
                async for chunk in provider_instance.generate_response_stream(
                    messages=messages,
                    model=agent.model
                ):
                    if isinstance(chunk, dict):
                        content = chunk.get('content', '')
                    else:
                        content = str(chunk)
                    full_response += content
                
                return full_response.strip()
            else:
                # Use regular response
                response = await provider_instance.generate_response(
                    messages=messages,
                    model=agent.model
                )
                return response.strip()
                
        except Exception as e:
            console.print(f"[red]Error getting response from {agent.name}: {e}[/red]")
            return f"[Error: {str(e)}]"
    
    async def _get_agent_response_stream(
        self,
        agent: AgentConfig,
        prompt: str,
        enable_tools: bool = False
    ):
        """
        Get a streaming response from a specific agent using AI engine's process_message_stream
        """
        try:
            # Use AI engine's process_message_stream which includes tool support
            async for chunk in self.ai_engine.process_message_stream(
                message=prompt,
                provider=agent.provider,
                model=agent.model,
                project_path=str(agent.folder),
                conversation_history=[],  # No history during execution to keep it focused
                confirmation_manager=None  # Auto-approve in multiagent mode
            ):
                yield chunk
                
        except Exception as e:
            yield f"\n[Error: {str(e)}]"
    
    def _format_discussion_history(self) -> str:
        """Format the discussion history for context"""
        discussion_messages = [
            msg for msg in self.conversation_history
            if msg.phase == 'discussion'
        ]
        
        if not discussion_messages:
            return "No previous discussion."
        
        formatted = []
        for msg in discussion_messages:
            formatted.append(f"{msg.agent_name}: {msg.content}")
        
        return "\n\n".join(formatted)
    
    def _format_agent_list(self) -> str:
        """Format the list of available agents"""
        return "\n".join([
            f"- {agent.name} ({agent.provider}:{agent.model})"
            for agent in self.agents
        ])
    
    def _format_task_assignments(self) -> str:
        """Format task assignments for display"""
        formatted = []
        for agent_name, tasks in self.task_assignments.items():
            if tasks:
                formatted.append(f"\n{agent_name}:")
                for task in tasks:
                    formatted.append(f"  - {task.description} (Priority: {task.priority})")
                    if task.files:
                        formatted.append(f"    Files: {', '.join(task.files)}")
        
        return "\n".join(formatted) if formatted else "No tasks assigned yet."
    
    def _display_task_assignments(self) -> None:
        """Display task assignments in a nice table"""
        table = Table(title="Task Assignments", show_header=True, header_style="bold cyan")
        table.add_column("Agent", style="green")
        table.add_column("Task", style="white")
        table.add_column("Files", style="yellow")
        table.add_column("Priority", style="magenta")
        
        for agent_name, tasks in self.task_assignments.items():
            for task in tasks:
                table.add_row(
                    agent_name,
                    task.description[:50] + "..." if len(task.description) > 50 else task.description,
                    ", ".join(task.files[:3]) + ("..." if len(task.files) > 3 else ""),
                    str(task.priority)
                )
        
        console.print(table)
        console.print()
    
    def _show_summary(self) -> None:
        """Show a summary of the collaboration"""
        console.print("\n[bold cyan]Collaboration Summary[/bold cyan]\n")
        
        # Count messages by phase
        discussion_count = len([m for m in self.conversation_history if m.phase == 'discussion'])
        planning_count = len([m for m in self.conversation_history if m.phase == 'planning'])
        execution_count = len([m for m in self.conversation_history if m.phase == 'execution'])
        
        console.print(f"[green]✓[/green] Discussion messages: {discussion_count}")
        console.print(f"[green]✓[/green] Planning messages: {planning_count}")
        console.print(f"[green]✓[/green] Execution messages: {execution_count}")
        console.print(f"[green]✓[/green] Total agents: {len(self.agents)}")
        console.print(f"[green]✓[/green] Total tasks assigned: {sum(len(tasks) for tasks in self.task_assignments.values())}")
        
        console.print(f"\n[bold]Shared Workspace:[/bold] {self.workspace}")
        console.print(f"[dim]All agents worked together in the same folder[/dim]")
        
        console.print("\n[bold green]Multi-agent collaboration complete![/bold green]\n")
