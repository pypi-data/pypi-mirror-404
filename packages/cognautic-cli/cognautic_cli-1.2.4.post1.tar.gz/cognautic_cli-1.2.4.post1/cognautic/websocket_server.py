"""
WebSocket server for real-time communication
"""

import asyncio
import json
import logging
import uuid
import websockets
from datetime import datetime
from typing import Dict, Any, Optional
from websockets.server import WebSocketServerProtocol
from .ai_engine import AIEngine

# Suppress websocket server logging in chat mode
logging.getLogger(__name__).setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

class SessionManager:
    """Manages WebSocket sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.connections: Dict[str, websockets.server.WebSocketServerProtocol] = {}
    
    def create_session(self, websocket: WebSocketServerProtocol) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            'id': session_id,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'context': [],
            'project_path': None,
            'ai_provider': 'openai',
            'ai_model': None
        }
        
        self.connections[session_id] = websocket
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, **kwargs):
        """Update session data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(kwargs)
            self.sessions[session_id]['last_activity'] = datetime.now().isoformat()
    
    def remove_session(self, session_id: str):
        """Remove a session"""
        self.sessions.pop(session_id, None)
        self.connections.pop(session_id, None)
    
    def get_connection(self, session_id: str) -> Optional[WebSocketServerProtocol]:
        """Get WebSocket connection for session"""
        return self.connections.get(session_id)


class MessageHandler:
    """Handles WebSocket messages"""
    
    def __init__(self, ai_engine: AIEngine, session_manager: SessionManager):
        self.ai_engine = ai_engine
        self.session_manager = session_manager
    
    async def handle_message(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message"""
        
        message_type = message.get('type')
        
        handlers = {
            'chat': self._handle_chat,
            'tool_execute': self._handle_tool_execute,
            'session_config': self._handle_session_config,
            'typing_speed': self._handle_typing_speed,
            'project_analyze': self._handle_project_analyze,
            'project_build': self._handle_project_build
        }
        
        handler = handlers.get(message_type)
        if not handler:
            return {
                'type': 'error',
                'error': f'Unknown message type: {message_type}'
            }
        
        try:
            return await handler(session_id, message)
        except Exception as e:
            return {
                'type': 'error',
                'error': str(e)
            }
    
    async def _handle_chat(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat message with real-time streaming"""
        
        session = self.session_manager.get_session(session_id)
        if not session:
            return {'type': 'error', 'error': 'Session not found'}
        
        user_message = message.get('message', '')
        stream_enabled = message.get('stream', True)  # Enable streaming by default
        
        if not user_message:
            return {'type': 'error', 'error': 'Empty message'}
        
        # Add user message to context
        session['context'].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Get WebSocket connection for streaming
        websocket = self.session_manager.get_connection(session_id)
        
        if stream_enabled and websocket:
            # Stream response in real-time
            return await self._handle_chat_stream(session_id, session, user_message, websocket)
        else:
            # Non-streaming response (legacy mode)
            return await self._handle_chat_complete(session_id, session, user_message)
    
    async def _handle_chat_stream(self, session_id: str, session: Dict[str, Any], user_message: str, websocket: WebSocketServerProtocol) -> Dict[str, Any]:
        """Handle chat message with real-time character-by-character streaming"""
        
        try:
            # Get typing speed from session config (default: 0.001s = fast)
            typing_delay = session.get('typing_delay', 0.001)
            
            # Send stream start notification
            await websocket.send(json.dumps({
                'type': 'stream_start',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }))
            
            # Collect full response for context
            full_response = ""

            provider = session.get('ai_provider')

            # Stream AI response
            async for chunk in self.ai_engine.process_message_stream(
                message=user_message,
                provider=session.get('ai_provider'),
                model=session.get('ai_model'),
                project_path=session.get('project_path'),
                conversation_history=session.get('context', [])
            ):
                full_response += chunk

                # For Ollama or instant mode, send the whole chunk immediately (no per-char delay)
                if provider == 'ollama' or typing_delay == 0:
                    await websocket.send(json.dumps({
                        'type': 'stream_chunk',
                        'chunk': chunk,
                        'session_id': session_id
                    }))
                else:
                    # Typewriter effect: send character-by-character with small delay
                    for char in chunk:
                        await websocket.send(json.dumps({
                            'type': 'stream_chunk',
                            'chunk': char,
                            'session_id': session_id
                        }))
                        if typing_delay > 0:
                            await asyncio.sleep(typing_delay)
            
            # Send stream end notification
            await websocket.send(json.dumps({
                'type': 'stream_end',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }))
            
            # Add AI response to context
            session['context'].append({
                'role': 'assistant',
                'content': full_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Update session
            self.session_manager.update_session(session_id, context=session['context'])
            
            return {
                'type': 'chat_response',
                'message': full_response,
                'session_id': session_id,
                'streamed': True
            }
            
        except Exception as e:
            # Send error notification
            await websocket.send(json.dumps({
                'type': 'stream_error',
                'error': str(e),
                'session_id': session_id
            }))
            
            return {
                'type': 'error',
                'error': f'AI processing failed: {str(e)}'
            }
    
    async def _handle_chat_complete(self, session_id: str, session: Dict[str, Any], user_message: str) -> Dict[str, Any]:
        """Handle chat message with complete (non-streaming) response"""
        
        try:
            ai_response = await self.ai_engine.process_message(
                message=user_message,
                provider=session.get('ai_provider'),
                model=session.get('ai_model'),
                project_path=session.get('project_path'),
                context=session['context']
            )
            
            # Add AI response to context
            session['context'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Update session
            self.session_manager.update_session(session_id, context=session['context'])
            
            return {
                'type': 'chat_response',
                'message': ai_response,
                'session_id': session_id,
                'streamed': False
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'error': f'AI processing failed: {str(e)}'
            }
    
    async def _handle_tool_execute(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution request"""
        
        tool_name = message.get('tool_name')
        operation = message.get('operation')
        parameters = message.get('parameters', {})
        
        if not tool_name or not operation:
            return {
                'type': 'error',
                'error': 'Missing tool_name or operation'
            }
        
        try:
            # Execute tool through AI engine's tool registry
            result = await self.ai_engine.tool_registry.execute_tool(
                tool_name=tool_name,
                operation=operation,
                **parameters
            )
            
            return {
                'type': 'tool_result',
                'tool_name': tool_name,
                'operation': operation,
                'result': result.to_dict()
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'error': f'Tool execution failed: {str(e)}'
            }
    
    async def _handle_session_config(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session configuration"""
        
        config = message.get('config', {})
        
        # Update session with new configuration
        self.session_manager.update_session(session_id, **config)
        
        return {
            'type': 'session_updated',
            'session_id': session_id,
            'config': config
        }
    
    async def _handle_typing_speed(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle typing speed configuration"""
        
        speed = message.get('speed', 'fast')
        
        # Speed presets (in seconds per character)
        speed_map = {
            'instant': 0,
            'fast': 0.001,      # ~1000 chars/sec
            'normal': 0.005,    # ~200 chars/sec
            'slow': 0.01        # ~100 chars/sec
        }
        
        # Get delay value
        if isinstance(speed, (int, float)):
            typing_delay = float(speed)
        else:
            typing_delay = speed_map.get(speed, 0.001)
        
        # Update session
        self.session_manager.update_session(session_id, typing_delay=typing_delay)
        
        return {
            'type': 'typing_speed_updated',
            'session_id': session_id,
            'speed': speed,
            'delay': typing_delay
        }
    
    async def _handle_project_analyze(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle project analysis request"""
        
        project_path = message.get('project_path')
        options = message.get('options', {})
        
        if not project_path:
            return {
                'type': 'error',
                'error': 'Missing project_path'
            }
        
        try:
            result = await self.ai_engine.analyze_project(
                project_path=project_path,
                **options
            )
            
            return {
                'type': 'project_analysis',
                'project_path': project_path,
                'result': result
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'error': f'Project analysis failed: {str(e)}'
            }
    
    async def _handle_project_build(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle project build request"""
        
        description = message.get('description')
        options = message.get('options', {})
        
        if not description:
            return {
                'type': 'error',
                'error': 'Missing project description'
            }
        
        try:
            result = await self.ai_engine.build_project(
                description=description,
                **options
            )
            
            return {
                'type': 'project_build',
                'description': description,
                'result': result
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'error': f'Project build failed: {str(e)}'
            }


class WebSocketServer:
    """WebSocket server for real-time AI interaction"""
    
    def __init__(self, ai_engine: AIEngine, host: str = "localhost", port: int = 8765):
        self.ai_engine = ai_engine
        self.host = host
        self.port = port
        self.session_manager = SessionManager()
        self.message_handler = MessageHandler(ai_engine, self.session_manager)
        self.server = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket client connection"""
        
        # Create session for new connection
        session_id = self.session_manager.create_session(websocket)
        self.logger.info(f"New client connected: {session_id}")
        
        try:
            # Send welcome message
            welcome_message = {
                'type': 'welcome',
                'session_id': session_id,
                'message': 'Connected to Cognautic AI Assistant',
                'available_providers': self.ai_engine.get_available_providers(),
                'features': {
                    'streaming': True,
                    'real_time': True,
                    'tools': True
                },
                'server_version': '2.0.0'
            }
            await websocket.send(json.dumps(welcome_message))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type', 'unknown')
                    self.logger.info(f"Received message from {session_id}: {message_type}")
                    
                    # For chat messages with streaming, handle in a special way
                    if message_type == 'chat' and data.get('stream', True):
                        # Process with streaming - responses are sent during processing
                        response = await self.message_handler.handle_message(session_id, data)
                        # Only send final confirmation after streaming is complete
                        if response.get('type') != 'chat_response' or not response.get('streamed'):
                            await websocket.send(json.dumps(response))
                    else:
                        # Process message normally
                        response = await self.message_handler.handle_message(session_id, data)
                        # Send response
                        await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    error_response = {
                        'type': 'error',
                        'error': 'Invalid JSON message'
                    }
                    await websocket.send(json.dumps(error_response))
                
                except Exception as e:
                    self.logger.error(f"Error handling message from {session_id}: {str(e)}")
                    error_response = {
                        'type': 'error',
                        'error': f'Message handling failed: {str(e)}'
                    }
                    await websocket.send(json.dumps(error_response))
        
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {session_id}")
        
        except Exception as e:
            self.logger.error(f"Connection error for {session_id}: {str(e)}")
        
        finally:
            # Clean up session
            self.session_manager.remove_session(session_id)
    
    async def start(self):
        """Start the WebSocket server"""
        # Start server silently in chat mode
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        # Keep server running
        await self.server.wait_closed()
    
    async def stop(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped")
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about active sessions"""
        return {
            'total_sessions': len(self.session_manager.sessions),
            'sessions': list(self.session_manager.sessions.keys())
        }
