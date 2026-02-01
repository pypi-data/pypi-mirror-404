"""
Command runner tool for executing shell commands
"""

import asyncio
import subprocess
import psutil
from typing import List, Dict, Any, Optional
import signal
import os

from .base import BaseTool, ToolResult, PermissionLevel


class CommandRunnerTool(BaseTool):
    """Tool for executing shell commands and system operations"""
    
    def __init__(self):
        super().__init__(
            name="command_runner",
            description="Execute shell commands and system operations",
            permission_level=PermissionLevel.SYSTEM_OPERATIONS
        )
        self.running_processes = {}
    
    def get_capabilities(self) -> List[str]:
        return [
            "run_command",
            "run_async_command", 
            "get_command_output",
            "kill_process",
            "check_process_status"
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "command_runner",
                "description": "Execute shell commands and system operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The operation to perform",
                            "enum": self.get_capabilities()
                        },
                        "command": {
                            "type": "string",
                            "description": "The command to execute"
                        },
                        "cwd": {
                            "type": "string",
                            "description": "Current working directory for the command"
                        },
                        "process_id": {
                            "type": "string",
                            "description": "Process ID for status/kill operations"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds (default: 300)"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute command operation"""
        
        operations = {
            'run_command': self._run_command,
            'run_async_command': self._run_async_command,
            'get_command_output': self._get_command_output,
            'kill_process': self._kill_process,
            'check_process_status': self._check_process_status
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation: {operation}"
            )
        
        try:
            result = await operations[operation](**kwargs)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _run_command(
        self,
        command: str,
        cwd: str = None,
        timeout: int = 300,
        capture_output: bool = True,
        shell: bool = True
    ) -> Dict[str, Any]:
        """Run a command synchronously (default timeout: 5 minutes for long-running commands)"""
        
        try:
            if shell:
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=cwd,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None
                )
            else:
                cmd_parts = command.split()
                process = await asyncio.create_subprocess_exec(
                    *cmd_parts,
                    cwd=cwd,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None
                )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return {
                    'command': command,
                    'return_code': process.returncode,
                    'stdout': stdout.decode('utf-8') if stdout else '',
                    'stderr': stderr.decode('utf-8') if stderr else '',
                    'success': process.returncode == 0
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Command timed out after {timeout} seconds")
                
        except Exception as e:
            return {
                'command': command,
                'return_code': -1,
                'stdout': '',
                'stderr': str(e),
                'success': False,
                'error': str(e)
            }
    
    async def _run_async_command(
        self,
        command: str,
        cwd: str = None,
        shell: bool = True
    ) -> Dict[str, Any]:
        """Run a command asynchronously and return process ID"""
        
        try:
            if shell:
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                cmd_parts = command.split()
                process = await asyncio.create_subprocess_exec(
                    *cmd_parts,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            process_id = str(process.pid)
            self.running_processes[process_id] = {
                'process': process,
                'command': command,
                'cwd': cwd,
                'started_at': asyncio.get_event_loop().time()
            }
            
            return {
                'process_id': process_id,
                'command': command,
                'pid': process.pid,
                'status': 'running'
            }
            
        except Exception as e:
            raise Exception(f"Failed to start async command: {str(e)}")
    
    async def _get_command_output(self, process_id: str) -> Dict[str, Any]:
        """Get output from an async command"""
        
        if process_id not in self.running_processes:
            raise ValueError(f"Process ID not found: {process_id}")
        
        process_info = self.running_processes[process_id]
        process = process_info['process']
        
        # Check if process is still running
        if process.returncode is None:
            # Process is still running
            return {
                'process_id': process_id,
                'status': 'running',
                'return_code': None,
                'stdout': '',
                'stderr': '',
                'finished': False
            }
        else:
            # Process has finished
            try:
                stdout, stderr = await process.communicate()
                
                result = {
                    'process_id': process_id,
                    'status': 'finished',
                    'return_code': process.returncode,
                    'stdout': stdout.decode('utf-8') if stdout else '',
                    'stderr': stderr.decode('utf-8') if stderr else '',
                    'finished': True,
                    'success': process.returncode == 0
                }
                
                # Clean up
                del self.running_processes[process_id]
                return result
                
            except Exception as e:
                return {
                    'process_id': process_id,
                    'status': 'error',
                    'error': str(e),
                    'finished': True,
                    'success': False
                }
    
    async def _kill_process(self, process_id: str, force: bool = False) -> Dict[str, Any]:
        """Kill a running process"""
        
        if process_id not in self.running_processes:
            raise ValueError(f"Process ID not found: {process_id}")
        
        process_info = self.running_processes[process_id]
        process = process_info['process']
        
        try:
            if force:
                process.kill()
            else:
                process.terminate()
            
            # Wait for process to finish
            await asyncio.wait_for(process.wait(), timeout=5.0)
            
            # Clean up
            del self.running_processes[process_id]
            
            return {
                'process_id': process_id,
                'killed': True,
                'method': 'force' if force else 'terminate'
            }
            
        except asyncio.TimeoutError:
            # Force kill if terminate didn't work
            process.kill()
            await process.wait()
            del self.running_processes[process_id]
            
            return {
                'process_id': process_id,
                'killed': True,
                'method': 'force (after timeout)'
            }
        except Exception as e:
            return {
                'process_id': process_id,
                'killed': False,
                'error': str(e)
            }
    
    async def _check_process_status(self, process_id: str = None) -> Dict[str, Any]:
        """Check status of running processes"""
        
        if process_id:
            # Check specific process
            if process_id not in self.running_processes:
                return {
                    'process_id': process_id,
                    'found': False
                }
            
            process_info = self.running_processes[process_id]
            process = process_info['process']
            
            return {
                'process_id': process_id,
                'found': True,
                'command': process_info['command'],
                'pid': process.pid,
                'status': 'running' if process.returncode is None else 'finished',
                'return_code': process.returncode,
                'started_at': process_info['started_at'],
                'running_time': asyncio.get_event_loop().time() - process_info['started_at']
            }
        else:
            # Check all processes
            processes = []
            for pid, info in self.running_processes.items():
                process = info['process']
                processes.append({
                    'process_id': pid,
                    'command': info['command'],
                    'pid': process.pid,
                    'status': 'running' if process.returncode is None else 'finished',
                    'return_code': process.returncode,
                    'started_at': info['started_at'],
                    'running_time': asyncio.get_event_loop().time() - info['started_at']
                })
            
            return {
                'total_processes': len(processes),
                'processes': processes
            }
