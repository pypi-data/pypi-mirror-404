"""Tests for conversation history and summarization."""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from claude_dev_cli.history import Message, Conversation, ConversationHistory


class TestMessage:
    """Tests for Message class."""
    
    def test_message_creation(self):
        """Test creating a message."""
        msg = Message("user", "Hello, Claude!")
        assert msg.role == "user"
        assert msg.content == "Hello, Claude!"
        assert isinstance(msg.timestamp, datetime)
    
    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        msg = Message("assistant", "Hello! How can I help?")
        data = msg.to_dict()
        
        assert data["role"] == "assistant"
        assert data["content"] == "Hello! How can I help?"
        assert "timestamp" in data
    
    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        data = {
            "role": "user",
            "content": "Test message",
            "timestamp": "2024-01-09T12:00:00"
        }
        msg = Message.from_dict(data)
        
        assert msg.role == "user"
        assert msg.content == "Test message"
        assert isinstance(msg.timestamp, datetime)


class TestConversation:
    """Tests for Conversation class."""
    
    def test_conversation_creation(self):
        """Test creating a conversation."""
        conv = Conversation()
        assert conv.conversation_id is not None
        assert isinstance(conv.created_at, datetime)
        assert isinstance(conv.updated_at, datetime)
        assert len(conv.messages) == 0
        assert conv.summary is None
    
    def test_conversation_with_summary(self):
        """Test creating conversation with summary."""
        summary = "This is a test summary"
        conv = Conversation(summary=summary)
        assert conv.summary == summary
    
    def test_add_message(self):
        """Test adding messages to conversation."""
        conv = Conversation()
        conv.add_message("user", "First message")
        conv.add_message("assistant", "First response")
        
        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[0].content == "First message"
        assert conv.messages[1].role == "assistant"
    
    def test_get_summary_with_messages(self):
        """Test getting conversation summary."""
        conv = Conversation()
        conv.add_message("user", "What is Python?")
        conv.add_message("assistant", "Python is a programming language...")
        
        summary = conv.get_summary(20)
        assert summary == "What is Python?"
    
    def test_get_summary_truncated(self):
        """Test summary truncation."""
        conv = Conversation()
        long_message = "a" * 150
        conv.add_message("user", long_message)
        
        summary = conv.get_summary(100)
        assert len(summary) <= 103  # 100 + "..."
        assert summary.endswith("...")
    
    def test_get_summary_empty(self):
        """Test summary of empty conversation."""
        conv = Conversation()
        summary = conv.get_summary()
        assert summary == "(empty conversation)"
    
    def test_estimate_tokens_no_messages(self):
        """Test token estimation for empty conversation."""
        conv = Conversation()
        tokens = conv.estimate_tokens()
        assert tokens == 0
    
    def test_estimate_tokens_with_messages(self):
        """Test token estimation with messages."""
        conv = Conversation()
        # Each character ~= 0.25 tokens, so 400 chars ~= 100 tokens
        conv.add_message("user", "a" * 200)
        conv.add_message("assistant", "b" * 200)
        
        tokens = conv.estimate_tokens()
        assert tokens == 100  # 400 chars / 4
    
    def test_estimate_tokens_with_summary(self):
        """Test token estimation includes summary."""
        conv = Conversation(summary="Summary text here" * 10)  # 170 chars
        conv.add_message("user", "a" * 230)  # 230 chars
        
        # Total: 400 chars / 4 = 100 tokens
        tokens = conv.estimate_tokens()
        assert tokens == 100
    
    def test_should_summarize_below_threshold(self):
        """Test should_summarize returns False below threshold."""
        conv = Conversation()
        conv.add_message("user", "a" * 100)
        conv.add_message("assistant", "b" * 100)
        
        # 200 chars = 50 tokens, below 8000 threshold
        assert not conv.should_summarize(threshold_tokens=8000)
    
    def test_should_summarize_above_threshold(self):
        """Test should_summarize returns True above threshold."""
        conv = Conversation()
        # Add enough messages to exceed 1000 token threshold
        for i in range(10):
            conv.add_message("user", "a" * 200)  # 200 chars = 50 tokens
            conv.add_message("assistant", "b" * 200)  # 200 chars = 50 tokens
        
        # Total: 2000 chars = 500 tokens, above 400 threshold
        assert conv.should_summarize(threshold_tokens=400)
    
    def test_should_summarize_too_few_messages(self):
        """Test should_summarize returns False with too few messages."""
        conv = Conversation()
        # Even with many tokens, need minimum message count
        conv.add_message("user", "a" * 4000)  # 1000 tokens
        
        assert not conv.should_summarize(threshold_tokens=500)
    
    def test_compress_messages_few_messages(self):
        """Test compress_messages with too few messages."""
        conv = Conversation()
        conv.add_message("user", "message 1")
        conv.add_message("assistant", "response 1")
        
        old, recent = conv.compress_messages(keep_recent=4)
        assert len(old) == 0
        assert len(recent) == 2
    
    def test_compress_messages_split(self):
        """Test compress_messages splits correctly."""
        conv = Conversation()
        for i in range(10):
            conv.add_message("user", f"message {i}")
            conv.add_message("assistant", f"response {i}")
        
        # Total: 20 messages, keep 4 recent
        old, recent = conv.compress_messages(keep_recent=4)
        assert len(old) == 16
        assert len(recent) == 4
        assert recent[0].content == "message 8"
        assert recent[-1].content == "response 9"
    
    def test_to_dict(self):
        """Test converting conversation to dictionary."""
        conv = Conversation()
        conv.add_message("user", "test")
        data = conv.to_dict()
        
        assert "conversation_id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "messages" in data
        assert len(data["messages"]) == 1
    
    def test_to_dict_with_summary(self):
        """Test to_dict includes summary."""
        conv = Conversation(summary="Test summary")
        data = conv.to_dict()
        
        assert data["summary"] == "Test summary"
    
    def test_from_dict(self):
        """Test creating conversation from dictionary."""
        data = {
            "conversation_id": "test_123",
            "created_at": "2024-01-09T12:00:00",
            "updated_at": "2024-01-09T12:05:00",
            "summary": "Test summary",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2024-01-09T12:01:00"
                }
            ]
        }
        
        conv = Conversation.from_dict(data)
        assert conv.conversation_id == "test_123"
        assert conv.summary == "Test summary"
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello"


class TestConversationHistory:
    """Tests for ConversationHistory class."""
    
    @pytest.fixture
    def temp_history_dir(self, tmp_path):
        """Create a temporary history directory."""
        return tmp_path / "history"
    
    @pytest.fixture
    def conv_history(self, temp_history_dir):
        """Create a ConversationHistory instance."""
        return ConversationHistory(temp_history_dir)
    
    def test_init_creates_directory(self, temp_history_dir):
        """Test initialization creates directory."""
        ConversationHistory(temp_history_dir)
        assert temp_history_dir.exists()
    
    def test_save_conversation(self, conv_history, temp_history_dir):
        """Test saving a conversation."""
        conv = Conversation()
        conv.add_message("user", "test")
        
        conv_history.save_conversation(conv)
        
        # Check file exists
        file_path = temp_history_dir / f"{conv.conversation_id}.json"
        assert file_path.exists()
        
        # Check content
        with open(file_path) as f:
            data = json.load(f)
        assert data["conversation_id"] == conv.conversation_id
        assert len(data["messages"]) == 1
    
    def test_load_conversation(self, conv_history):
        """Test loading a conversation."""
        # Save first
        conv = Conversation()
        conv.add_message("user", "test message")
        conv_history.save_conversation(conv)
        
        # Load
        loaded = conv_history.load_conversation(conv.conversation_id)
        assert loaded is not None
        assert loaded.conversation_id == conv.conversation_id
        assert len(loaded.messages) == 1
        assert loaded.messages[0].content == "test message"
    
    def test_load_nonexistent_conversation(self, conv_history):
        """Test loading a conversation that doesn't exist."""
        loaded = conv_history.load_conversation("nonexistent_id")
        assert loaded is None
    
    def test_list_conversations(self, conv_history):
        """Test listing conversations."""
        import time
        # Create multiple conversations with small delays to ensure ordering
        for i in range(3):
            conv = Conversation()
            conv.add_message("user", f"message {i}")
            conv_history.save_conversation(conv)
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        conversations = conv_history.list_conversations()
        assert len(conversations) == 3
    
    def test_list_conversations_with_limit(self, conv_history):
        """Test listing conversations with limit."""
        import time
        for i in range(5):
            conv = Conversation()
            conv.add_message("user", f"message {i}")
            conv_history.save_conversation(conv)
            time.sleep(0.01)
        
        conversations = conv_history.list_conversations(limit=2)
        assert len(conversations) == 2
    
    def test_list_conversations_with_search(self, conv_history):
        """Test searching conversations."""
        import time
        conv1 = Conversation()
        conv1.add_message("user", "Python programming")
        conv_history.save_conversation(conv1)
        time.sleep(0.01)
        
        conv2 = Conversation()
        conv2.add_message("user", "JavaScript coding")
        conv_history.save_conversation(conv2)
        
        # Search for Python
        results = conv_history.list_conversations(search_query="Python")
        assert len(results) == 1
        assert "Python" in results[0].messages[0].content
    
    def test_delete_conversation(self, conv_history, temp_history_dir):
        """Test deleting a conversation."""
        conv = Conversation()
        conv_history.save_conversation(conv)
        
        # Verify it exists
        file_path = temp_history_dir / f"{conv.conversation_id}.json"
        assert file_path.exists()
        
        # Delete
        result = conv_history.delete_conversation(conv.conversation_id)
        assert result is True
        assert not file_path.exists()
    
    def test_delete_nonexistent_conversation(self, conv_history):
        """Test deleting a conversation that doesn't exist."""
        result = conv_history.delete_conversation("nonexistent")
        assert result is False
    
    def test_get_latest_conversation(self, conv_history):
        """Test getting the latest conversation."""
        # Create conversations with delay to ensure ordering
        conv1 = Conversation()
        conv1.add_message("user", "first")
        conv_history.save_conversation(conv1)
        
        import time
        time.sleep(0.01)  # Small delay
        
        conv2 = Conversation()
        conv2.add_message("user", "second")
        conv_history.save_conversation(conv2)
        
        latest = conv_history.get_latest_conversation()
        assert latest is not None
        assert latest.messages[0].content == "second"
    
    def test_export_conversation_markdown(self, conv_history):
        """Test exporting conversation as markdown."""
        conv = Conversation()
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")
        conv_history.save_conversation(conv)
        
        markdown = conv_history.export_conversation(conv.conversation_id, "markdown")
        assert markdown is not None
        assert "Hello" in markdown
        assert "Hi there!" in markdown
        assert "**You:**" in markdown
        assert "**Claude:**" in markdown
    
    def test_export_conversation_json(self, conv_history):
        """Test exporting conversation as JSON."""
        conv = Conversation()
        conv.add_message("user", "Test")
        conv_history.save_conversation(conv)
        
        json_str = conv_history.export_conversation(conv.conversation_id, "json")
        assert json_str is not None
        
        data = json.loads(json_str)
        assert data["conversation_id"] == conv.conversation_id
    
    def test_export_nonexistent_conversation(self, conv_history):
        """Test exporting a conversation that doesn't exist."""
        result = conv_history.export_conversation("nonexistent", "markdown")
        assert result is None
    
    @patch('claude_dev_cli.core.ClaudeClient')
    def test_summarize_conversation(self, mock_client_class, conv_history):
        """Test summarizing a conversation."""
        # Setup mock
        mock_client = Mock()
        mock_client.call.return_value = "This is a test summary of the conversation."
        mock_client_class.return_value = mock_client
        
        # Create conversation with enough messages
        conv = Conversation()
        for i in range(6):
            conv.add_message("user", f"Question {i}")
            conv.add_message("assistant", f"Answer {i}")
        conv_history.save_conversation(conv)
        
        # Summarize
        summary = conv_history.summarize_conversation(conv.conversation_id, keep_recent=4)
        
        assert summary is not None
        assert "test summary" in summary
        
        # Verify conversation was updated
        updated_conv = conv_history.load_conversation(conv.conversation_id)
        assert updated_conv.summary == summary
        assert len(updated_conv.messages) == 4  # Only recent messages kept
    
    @patch('claude_dev_cli.core.ClaudeClient')
    def test_summarize_with_previous_summary(self, mock_client_class, conv_history):
        """Test summarizing with existing summary."""
        mock_client = Mock()
        mock_client.call.return_value = "Updated summary"
        mock_client_class.return_value = mock_client
        
        # Create conversation with existing summary
        conv = Conversation(summary="Previous summary")
        for i in range(6):
            conv.add_message("user", f"Message {i}")
            conv.add_message("assistant", f"Response {i}")
        conv_history.save_conversation(conv)
        
        # Summarize
        summary = conv_history.summarize_conversation(conv.conversation_id, keep_recent=2)
        
        # Check that call included previous summary
        call_args = mock_client.call.call_args[0][0]
        assert "Previous summary" in call_args
    
    def test_summarize_too_few_messages(self, conv_history):
        """Test summarizing with too few messages."""
        conv = Conversation()
        conv.add_message("user", "Only one message")
        conv_history.save_conversation(conv)
        
        result = conv_history.summarize_conversation(conv.conversation_id, keep_recent=4)
        assert "too few messages" in result.lower()
    
    def test_summarize_nonexistent_conversation(self, conv_history):
        """Test summarizing a conversation that doesn't exist."""
        result = conv_history.summarize_conversation("nonexistent")
        assert result is None


class TestConversationPersistence:
    """Tests for conversation persistence and data integrity."""
    
    def test_roundtrip_conversation(self, tmp_path):
        """Test saving and loading preserves all data."""
        history = ConversationHistory(tmp_path)
        
        # Create conversation with all features
        conv = Conversation(summary="Initial summary")
        conv.add_message("user", "First question")
        conv.add_message("assistant", "First answer")
        conv.add_message("user", "Second question")
        
        # Save
        history.save_conversation(conv)
        
        # Load
        loaded = history.load_conversation(conv.conversation_id)
        
        # Verify everything matches
        assert loaded.conversation_id == conv.conversation_id
        assert loaded.summary == conv.summary
        assert len(loaded.messages) == len(conv.messages)
        assert loaded.messages[0].content == conv.messages[0].content
        assert loaded.messages[1].role == conv.messages[1].role
    
    def test_conversation_update(self, tmp_path):
        """Test updating a conversation."""
        history = ConversationHistory(tmp_path)
        
        # Create and save
        conv = Conversation()
        conv.add_message("user", "Original message")
        history.save_conversation(conv)
        
        # Load, modify, save
        loaded = history.load_conversation(conv.conversation_id)
        loaded.add_message("assistant", "New response")
        loaded.summary = "Added summary"
        history.save_conversation(loaded)
        
        # Load again and verify
        final = history.load_conversation(conv.conversation_id)
        assert len(final.messages) == 2
        assert final.summary == "Added summary"
