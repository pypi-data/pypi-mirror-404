"""
Memory system for Cognautic CLI - handles conversation history and context persistence
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from rich.console import Console

console = Console()


@dataclass
class Message:
    """Represents a single message in a conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(**data)


@dataclass
class SessionInfo:
    """Information about a chat session"""
    session_id: str
    title: str
    created_at: str
    last_updated: str
    provider: str
    model: Optional[str] = None
    workspace: Optional[str] = None
    message_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionInfo':
        return cls(**data)


class MemoryManager:
    """Manages conversation memory and session persistence"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize memory manager
        
        Args:
            base_dir: Base directory for sessions. If None, uses current working directory
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path.cwd()
        
        self.sessions_dir = self.base_dir / ".sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        
        # Current session state
        self.current_session: Optional[SessionInfo] = None
        self.current_messages: List[Message] = []
        self.session_file: Optional[Path] = None

    def create_session(self, provider: str, model: Optional[str] = None, 
                      workspace: Optional[str] = None, title: Optional[str] = None) -> str:
        """Create a new chat session
        
        Args:
            provider: AI provider name
            model: Model name (optional)
            workspace: Current workspace path (optional)
            title: Session title (optional, will be auto-generated if not provided)
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())[:8]  # Short session ID
        timestamp = datetime.now().isoformat()
        
        if not title:
            title = f"Chat Session {session_id}"
        
        self.current_session = SessionInfo(
            session_id=session_id,
            title=title,
            created_at=timestamp,
            last_updated=timestamp,
            provider=provider,
            model=model,
            workspace=workspace,
            message_count=0
        )
        
        self.current_messages = []
        self.session_file = self.sessions_dir / f"{session_id}.json"
        
        # Save initial session file
        self._save_session()
        
        
        return session_id

    def _deserialize_data(self, obj: Any) -> Any:
        """Deep convert JSON data back to original formats, handling base64 bytes"""
        if isinstance(obj, dict):
            return {k: self._deserialize_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deserialize_data(i) for i in obj]
        elif isinstance(obj, str) and obj.startswith("__bytes__:"):
            import base64
            try:
                return base64.b64decode(obj[len("__bytes__:"):])
            except:
                return obj
        return obj

    def load_session(self, session_id: str) -> bool:
        """Load an existing session
        
        Args:
            session_id: Session ID to load
        
        Returns:
            True if session loaded successfully, False otherwise
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            console.print(f"❌ Session {session_id} not found", style="red")
            return False
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle binary data restoration
            data = self._deserialize_data(data)
            
            self.current_session = SessionInfo.from_dict(data['session_info'])
            self.current_messages = [Message.from_dict(msg) for msg in data['messages']]
            self.session_file = session_file
            
            console.print(f"✅ Loaded session: {session_id} - {self.current_session.title}", style="green")
            console.print(f"📊 Messages: {len(self.current_messages)}, Provider: {self.current_session.provider}")
            
            return True
            
        except Exception as e:
            console.print(f"❌ Error loading session {session_id}: {e}", style="red")
            return False

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the current session
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata dictionary
        """
        if not self.current_session:
            console.print("❌ No active session. Create or load a session first.", style="red")
            return
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
        
        self.current_messages.append(message)
        self.current_session.message_count = len(self.current_messages)
        self.current_session.last_updated = datetime.now().isoformat()
        
        # Save session after each message
        self._save_session()

    def get_conversation_history(self, limit: Optional[int] = None) -> List[Message]:
        """Get conversation history for the current session
        
        Args:
            limit: Maximum number of messages to return (most recent first)
        
        Returns:
            List of messages
        """
        if not self.current_messages:
            return []
        
        messages = self.current_messages.copy()
        if limit:
            messages = messages[-limit:]
        
        return messages

    def get_context_for_ai(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation context formatted for AI consumption
        
        Args:
            limit: Maximum number of recent messages to include
        
        Returns:
            List of message dictionaries with all necessary fields
        """
        messages = self.get_conversation_history(limit)
        context = []
        for msg in messages:
            m = {"role": msg.role, "content": msg.content}
            
            # Include metadata fields if present (vital for tool calling)
            if msg.metadata:
                # Common fields for tool calling
                for field in ["tool_calls", "name", "tool_call_id", "thought_signature"]:
                    if field in msg.metadata:
                        m[field] = msg.metadata[field]
            
            context.append(m)
        return context

    def list_sessions(self) -> List[SessionInfo]:
        """List all available sessions
        
        Returns:
            List of SessionInfo objects
        """
        sessions = []
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                session_info = SessionInfo.from_dict(data['session_info'])
                sessions.append(session_info)
                
            except Exception as e:
                console.print(f"❌ Error reading session file {session_file}: {e}", style="red")
        
        # Sort by last updated (most recent first)
        sessions.sort(key=lambda s: s.last_updated, reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session
        
        Args:
            session_id: Session ID to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            console.print(f"❌ Session {session_id} not found", style="red")
            return False
        
        try:
            session_file.unlink()
            
            # If this was the current session, clear it
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
                self.current_messages = []
                self.session_file = None
            
            console.print(f"✅ Deleted session: {session_id}", style="green")
            return True
            
        except Exception as e:
            console.print(f"❌ Error deleting session {session_id}: {e}", style="red")
            return False

    def update_session_info(self, **kwargs):
        """Update current session information
        
        Args:
            **kwargs: Fields to update (title, provider, model, workspace)
        """
        if not self.current_session:
            console.print("❌ No active session", style="red")
            return
        
        for key, value in kwargs.items():
            if hasattr(self.current_session, key):
                setattr(self.current_session, key, value)
        
        self.current_session.last_updated = datetime.now().isoformat()
        self._save_session()

    def get_current_session(self) -> Optional[SessionInfo]:
        """Get current session info
        
        Returns:
            Current SessionInfo or None
        """
        return self.current_session

    def _serialize_data(self, obj: Any) -> Any:
        """Deep convert object to JSON-serializable format, handling bytes"""
        if isinstance(obj, dict):
            return {k: self._serialize_data(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_data(i) for i in obj]
        elif isinstance(obj, bytes):
            import base64
            # Prefix with marker so we know to decode it later
            return f"__bytes__:{base64.b64encode(obj).decode('utf-8')}"
        return obj

    def _save_session(self):
        """Save current session to file with self-healing"""
        if not self.current_session or not self.session_file:
            return
        
        try:
            # Self-healing: Create sessions directory if it doesn't exist
            sessions_dir = Path(self.session_file).parent
            sessions_dir.mkdir(parents=True, exist_ok=True)
            
            raw_data = {
                'session_info': self.current_session.to_dict(),
                'messages': [msg.to_dict() for msg in self.current_messages]
            }
            
            # Convert binary data to base64 for JSON serialization
            data = self._serialize_data(raw_data)
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            console.print(f"❌ Error saving session: {e}", style="red")
            # Self-healing: Try to regenerate session from current state
            self._regenerate_session_file()

    def generate_session_title(self, first_message: str) -> str:
        """Generate a descriptive title from the first user message
        
        Args:
            first_message: First user message in the session
        
        Returns:
            Generated title
        """
        # Simple title generation - take first few words
        words = first_message.strip().split()[:6]
        title = " ".join(words)
        
        return title[:50] + "..." if len(title) > 50 else title
    
    def _regenerate_session_file(self):
        """Self-healing: Regenerate session file from current state"""
        try:
            if not self.current_session:
                # Create a new session if none exists
                self.current_session = SessionInfo(
                    session_id=str(uuid.uuid4())[:8],
                    title="Recovered Session",
                    created_at=datetime.now().isoformat(),
                    last_updated=datetime.now().isoformat(),
                    provider="unknown",
                    message_count=len(self.current_messages)
                )
            
            # Ensure sessions directory exists
            if self.session_file:
                sessions_dir = Path(self.session_file).parent
                sessions_dir.mkdir(parents=True, exist_ok=True)
                
                # Try to save again
                raw_data = {
                    'session_info': self.current_session.to_dict(),
                    'messages': [msg.to_dict() for msg in self.current_messages]
                }
                data = self._serialize_data(raw_data)
                
                with open(self.session_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                console.print("🔧 Session file regenerated successfully", style="yellow")
                
        except Exception as e:
            console.print(f"🔧 Self-healing failed: {e}", style="yellow")

    def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        """Export a session to a file
        
        Args:
            session_id: Session ID to export
            format: Export format ('json', 'markdown', 'txt')
        
        Returns:
            Path to exported file or None if failed
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            console.print(f"❌ Session {session_id} not found", style="red")
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session_info = SessionInfo.from_dict(data['session_info'])
            messages = [Message.from_dict(msg) for msg in data['messages']]
            
            export_file = self.sessions_dir / f"{session_id}_export.{format}"
            
            if format == "json":
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            elif format == "markdown":
                with open(export_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {session_info.title}\n\n")
                    f.write(f"**Session ID:** {session_info.session_id}\n")
                    f.write(f"**Created:** {session_info.created_at}\n")
                    f.write(f"**Provider:** {session_info.provider}\n")
                    if session_info.model:
                        f.write(f"**Model:** {session_info.model}\n")
                    f.write(f"**Messages:** {len(messages)}\n\n")
                    f.write("---\n\n")
                    
                    for msg in messages:
                        role_emoji = "👤" if msg.role == "user" else "🤖"
                        f.write(f"## {role_emoji} {msg.role.title()}\n\n")
                        f.write(f"{msg.content}\n\n")
                        f.write(f"*{msg.timestamp}*\n\n")
            
            elif format == "txt":
                with open(export_file, 'w', encoding='utf-8') as f:
                    f.write(f"{session_info.title}\n")
                    f.write("=" * len(session_info.title) + "\n\n")
                    f.write(f"Session ID: {session_info.session_id}\n")
                    f.write(f"Created: {session_info.created_at}\n")
                    f.write(f"Provider: {session_info.provider}\n")
                    if session_info.model:
                        f.write(f"Model: {session_info.model}\n")
                    f.write(f"Messages: {len(messages)}\n\n")
                    f.write("-" * 50 + "\n\n")
                    
                    for msg in messages:
                        f.write(f"{msg.role.upper()}: {msg.content}\n")
                        f.write(f"Time: {msg.timestamp}\n\n")
            
            console.print(f"✅ Exported session to: {export_file}", style="green")
            return str(export_file)
            
        except Exception as e:
            console.print(f"❌ Error exporting session: {e}", style="red")
            return None
