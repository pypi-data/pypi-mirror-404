"""Conversation history management for interactive mode."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any


class Message:
    """Represents a single message in a conversation."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class Conversation:
    """Represents a conversation with messages."""
    
    def __init__(
        self,
        conversation_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        summary: Optional[str] = None
    ):
        self.conversation_id = conversation_id or datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.summary = summary  # AI-generated summary of older messages
        self.messages: List[Message] = []
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        message = Message(role, content)
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    def get_summary(self, max_length: int = 100) -> str:
        """Get a summary of the conversation (first user message)."""
        for msg in self.messages:
            if msg.role == "user":
                summary = msg.content[:max_length]
                if len(msg.content) > max_length:
                    summary += "..."
                return summary
        return "(empty conversation)"
    
    def estimate_tokens(self) -> int:
        """Estimate token count for the conversation."""
        # Rough estimation: ~4 characters per token
        total_chars = len(self.summary or "")
        for msg in self.messages:
            total_chars += len(msg.content)
        return total_chars // 4
    
    def should_summarize(self, threshold_tokens: int = 8000) -> bool:
        """Check if conversation should be summarized."""
        return self.estimate_tokens() > threshold_tokens and len(self.messages) > 4
    
    def compress_messages(self, keep_recent: int = 4) -> tuple[List[Message], List[Message]]:
        """Split messages into old (to summarize) and recent (to keep)."""
        if len(self.messages) <= keep_recent:
            return [], self.messages
        
        split_point = len(self.messages) - keep_recent
        return self.messages[:split_point], self.messages[split_point:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = {
            "conversation_id": self.conversation_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages]
        }
        if self.summary:
            data["summary"] = self.summary
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create from dictionary."""
        conv = cls(
            conversation_id=data["conversation_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            summary=data.get("summary")
        )
        conv.messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        return conv


class ConversationHistory:
    """Manages conversation history storage and retrieval."""
    
    def __init__(self, history_dir: Path):
        self.history_dir = history_dir
        
        # Check if history_dir exists as a file (not directory)
        if self.history_dir.exists() and not self.history_dir.is_dir():
            raise RuntimeError(
                f"History directory path {self.history_dir} exists but is not a directory. "
                f"Please remove or rename this file."
            )
        
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_conversation_file(self, conversation_id: str) -> Path:
        """Get the file path for a conversation."""
        return self.history_dir / f"{conversation_id}.json"
    
    def save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation to disk."""
        file_path = self._get_conversation_file(conversation.conversation_id)
        with open(file_path, 'w') as f:
            json.dump(conversation.to_dict(), f, indent=2)
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation from disk."""
        file_path = self._get_conversation_file(conversation_id)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return Conversation.from_dict(data)
        except Exception:
            return None
    
    def list_conversations(
        self,
        limit: Optional[int] = None,
        search_query: Optional[str] = None
    ) -> List[Conversation]:
        """List all conversations, optionally filtered and limited."""
        conversations = []
        
        for file_path in sorted(self.history_dir.glob("*.json"), reverse=True):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                conv = Conversation.from_dict(data)
                
                # Apply search filter if provided
                if search_query:
                    search_lower = search_query.lower()
                    found = False
                    for msg in conv.messages:
                        if search_lower in msg.content.lower():
                            found = True
                            break
                    if not found:
                        continue
                
                conversations.append(conv)
                
                if limit and len(conversations) >= limit:
                    break
            except Exception:
                continue
        
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        file_path = self._get_conversation_file(conversation_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def get_latest_conversation(self) -> Optional[Conversation]:
        """Get the most recent conversation."""
        conversations = self.list_conversations(limit=1)
        return conversations[0] if conversations else None
    
    def export_conversation(
        self,
        conversation_id: str,
        output_format: str = "markdown"
    ) -> Optional[str]:
        """Export a conversation to a specific format."""
        conv = self.load_conversation(conversation_id)
        if not conv:
            return None
        
        if output_format == "markdown":
            lines = [f"# Conversation: {conv.conversation_id}"]
            lines.append(f"\nCreated: {conv.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Updated: {conv.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            for msg in conv.messages:
                role_display = "**You:**" if msg.role == "user" else "**Claude:**"
                lines.append(f"\n## {role_display}\n")
                lines.append(msg.content)
                lines.append("")
            
            return "\n".join(lines)
        
        elif output_format == "json":
            return json.dumps(conv.to_dict(), indent=2)
        
        return None
    
    def summarize_conversation(
        self,
        conversation_id: str,
        keep_recent: int = 4
    ) -> Optional[str]:
        """Summarize older messages in a conversation, keeping recent ones.
        
        Args:
            conversation_id: The conversation to summarize
            keep_recent: Number of recent message pairs to keep unsummarized
            
        Returns:
            The generated summary or None if conversation not found
        """
        from claude_dev_cli.core import ClaudeClient
        
        conv = self.load_conversation(conversation_id)
        if not conv:
            return None
        
        # Split messages
        old_messages, recent_messages = conv.compress_messages(keep_recent)
        
        if not old_messages:
            return "No messages to summarize (too few messages)"
        
        # Build summary prompt
        conversation_text = []
        if conv.summary:
            conversation_text.append(f"Previous summary:\n{conv.summary}\n\n")
        
        conversation_text.append("Conversation to summarize:\n")
        for msg in old_messages:
            role_name = "User" if msg.role == "user" else "Assistant"
            conversation_text.append(f"{role_name}: {msg.content}\n")
        
        prompt = (
            "Please provide a concise summary of this conversation that captures:"
            "\n1. Main topics discussed"
            "\n2. Key questions asked and answers provided"
            "\n3. Important decisions or conclusions"
            "\n4. Any action items or follow-ups mentioned"
            "\n\nKeep the summary under 300 words but retain all important context."
            "\n\n" + "".join(conversation_text)
        )
        
        # Get summary from Claude
        client = ClaudeClient()
        new_summary = client.call(prompt)
        
        # Update conversation
        conv.summary = new_summary
        conv.messages = recent_messages
        conv.updated_at = datetime.utcnow()
        
        # Save updated conversation
        self.save_conversation(conv)
        
        return new_summary
