"""
Unit tests for HistoryManager

Tests history management functionality including session creation,
storage, retrieval, and history operations.
"""

import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from src.agents.interaction_tasking.history_manager import (
    HistoryManager, SessionType, SessionStatus, ScanResult, ChatMessage, SessionHistory
)


@pytest.fixture
def temp_storage():
    """Create temporary storage directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def history_manager(temp_storage):
    """Create HistoryManager instance with temporary storage."""
    return HistoryManager(storage_path=temp_storage)


class TestHistoryManager:
    """Test cases for HistoryManager."""
    
    def test_init_creates_directories(self, temp_storage):
        """Test that initialization creates required directories."""
        hm = HistoryManager(storage_path=temp_storage)
        
        assert Path(temp_storage).exists()
        assert (Path(temp_storage) / "chats").exists()
        assert (Path(temp_storage) / "scans").exists()
    
    def test_create_session(self, history_manager):
        """Test creating a new session."""
        session_id = history_manager.create_session(
            session_type=SessionType.REPOSITORY_ANALYSIS,
            title="Test Repository Scan",
            description="Testing repository analysis"
        )
        
        assert session_id is not None
        assert len(session_id) == 36  # UUID format
        
        # Verify session exists
        session = history_manager.get_session(session_id)
        assert session is not None
        assert session.title == "Test Repository Scan"
        assert session.session_type == SessionType.REPOSITORY_ANALYSIS
        assert session.status == SessionStatus.IN_PROGRESS
    
    def test_update_session_status(self, history_manager):
        """Test updating session status."""
        session_id = history_manager.create_session(
            session_type=SessionType.CODE_QNA,
            title="Test Chat Session"
        )
        
        # Update status
        result = history_manager.update_session_status(session_id, SessionStatus.COMPLETED)
        assert result is True
        
        # Verify update
        session = history_manager.get_session(session_id)
        assert session.status == SessionStatus.COMPLETED
        
        # Test updating non-existent session
        result = history_manager.update_session_status("invalid-id", SessionStatus.ERROR)
        assert result is False
    
    def test_save_scan_result(self, history_manager):
        """Test saving scan result to session."""
        session_id = history_manager.create_session(
            session_type=SessionType.REPOSITORY_ANALYSIS,
            title="Test Scan"
        )
        
        scan_result = ScanResult(
            repository_url="https://github.com/test/repo",
            repository_name="test-repo",
            analysis_type="Repository Analysis",
            findings_count=10,
            severity_breakdown={"error": 2, "warning": 5, "info": 3},
            summary="Test scan completed",
            detailed_results={"test": "data"},
            timestamp=datetime.now().isoformat()
        )
        
        result = history_manager.save_scan_result(session_id, scan_result)
        assert result is True
        
        # Verify scan result saved
        session = history_manager.get_session(session_id)
        assert session.scan_result is not None
        assert session.scan_result.repository_name == "test-repo"
        assert session.status == SessionStatus.COMPLETED
        
        # Verify scan file created
        scan_file = Path(history_manager.scans_dir) / f"{session_id}.json"
        assert scan_file.exists()
    
    def test_add_chat_message(self, history_manager):
        """Test adding chat messages to session."""
        session_id = history_manager.create_session(
            session_type=SessionType.CODE_QNA,
            title="Test Chat"
        )
        
        # Add user message
        result = history_manager.add_chat_message(
            session_id, "user", "How does this function work?"
        )
        assert result is True
        
        # Add assistant message
        result = history_manager.add_chat_message(
            session_id, "assistant", "This function does X, Y, Z..."
        )
        assert result is True
        
        # Verify messages saved
        session = history_manager.get_session(session_id)
        assert len(session.chat_messages) == 2
        assert session.chat_messages[0].role == "user"
        assert session.chat_messages[1].role == "assistant"
        
        # Verify chat file created
        chat_file = Path(history_manager.chats_dir) / f"{session_id}.json"
        assert chat_file.exists()
    
    def test_get_all_sessions(self, history_manager):
        """Test retrieving all sessions."""
        # Create multiple sessions
        session1_id = history_manager.create_session(
            SessionType.REPOSITORY_ANALYSIS, "Repo 1"
        )
        session2_id = history_manager.create_session(
            SessionType.CODE_QNA, "Chat 1"
        )
        session3_id = history_manager.create_session(
            SessionType.REPOSITORY_ANALYSIS, "Repo 2"
        )
        
        # Get all sessions
        all_sessions = history_manager.get_all_sessions()
        assert len(all_sessions) == 3
        
        # Get filtered sessions
        repo_sessions = history_manager.get_all_sessions(SessionType.REPOSITORY_ANALYSIS)
        assert len(repo_sessions) == 2
        
        chat_sessions = history_manager.get_all_sessions(SessionType.CODE_QNA)
        assert len(chat_sessions) == 1
    
    def test_get_recent_sessions(self, history_manager):
        """Test retrieving recent sessions."""
        # Create sessions
        for i in range(15):
            history_manager.create_session(
                SessionType.REPOSITORY_ANALYSIS,
                f"Repo {i}"
            )
        
        # Get recent sessions (default limit 10)
        recent = history_manager.get_recent_sessions()
        assert len(recent) == 10
        
        # Get recent with custom limit
        recent_5 = history_manager.get_recent_sessions(limit=5)
        assert len(recent_5) == 5
        
        # Sessions should be sorted by updated_at descending
        assert recent[0].title == "Repo 14"  # Most recent
    
    def test_delete_session(self, history_manager):
        """Test deleting a session."""
        session_id = history_manager.create_session(
            SessionType.REPOSITORY_ANALYSIS,
            "Test for deletion"
        )
        
        # Add some data
        history_manager.add_chat_message(session_id, "user", "test message")
        scan_result = ScanResult(
            repository_url="https://github.com/test/repo",
            repository_name="test-repo",
            analysis_type="Repository Analysis",
            findings_count=0,
            severity_breakdown={},
            summary="Test",
            detailed_results={},
            timestamp=datetime.now().isoformat()
        )
        history_manager.save_scan_result(session_id, scan_result)
        
        # Verify files exist
        chat_file = Path(history_manager.chats_dir) / f"{session_id}.json"
        scan_file = Path(history_manager.scans_dir) / f"{session_id}.json"
        assert chat_file.exists()
        assert scan_file.exists()
        
        # Delete session
        result = history_manager.delete_session(session_id)
        assert result is True
        
        # Verify session deleted
        session = history_manager.get_session(session_id)
        assert session is None
        
        # Verify files deleted
        assert not chat_file.exists()
        assert not scan_file.exists()
        
        # Test deleting non-existent session
        result = history_manager.delete_session("invalid-id")
        assert result is False
    
    def test_get_session_stats(self, history_manager):
        """Test getting session statistics."""
        # Create sessions of different types and statuses
        session1 = history_manager.create_session(
            SessionType.REPOSITORY_ANALYSIS, "Repo 1"
        )
        history_manager.update_session_status(session1, SessionStatus.COMPLETED)
        
        session2 = history_manager.create_session(
            SessionType.CODE_QNA, "Chat 1"
        )
        
        session3 = history_manager.create_session(
            SessionType.REPOSITORY_ANALYSIS, "Repo 2"
        )
        history_manager.update_session_status(session3, SessionStatus.ERROR)
        
        # Get stats
        stats = history_manager.get_session_stats()
        
        assert stats["total_sessions"] == 3
        assert stats["by_type"]["repository_analysis"] == 2
        assert stats["by_type"]["code_qna"] == 1
        assert stats["by_status"]["completed"] == 1
        assert stats["by_status"]["in_progress"] == 1
        assert stats["by_status"]["error"] == 1
        assert len(stats["recent_activity"]) == 3
    
    def test_session_persistence(self, history_manager):
        """Test that sessions persist across HistoryManager instances."""
        # Create session
        session_id = history_manager.create_session(
            SessionType.REPOSITORY_ANALYSIS,
            "Persistence Test"
        )
        
        # Create new HistoryManager instance with same storage
        new_hm = HistoryManager(storage_path=history_manager.storage_path)
        
        # Should be able to retrieve session
        session = new_hm.get_session(session_id)
        assert session is not None
        assert session.title == "Persistence Test"


class TestDataClasses:
    """Test cases for data classes."""
    
    def test_scan_result_creation(self):
        """Test ScanResult dataclass creation."""
        scan_result = ScanResult(
            repository_url="https://github.com/test/repo",
            repository_name="test-repo",
            analysis_type="Repository Analysis",
            findings_count=5,
            severity_breakdown={"error": 1, "warning": 2, "info": 2},
            summary="Test completed",
            detailed_results={"issues": []},
            timestamp="2024-01-01T12:00:00"
        )
        
        assert scan_result.repository_name == "test-repo"
        assert scan_result.findings_count == 5
        assert len(scan_result.severity_breakdown) == 3
    
    def test_chat_message_creation(self):
        """Test ChatMessage dataclass creation."""
        message = ChatMessage(
            role="user",
            content="Test message",
            timestamp="2024-01-01T12:00:00",
            metadata={"source": "web_ui"}
        )
        
        assert message.role == "user"
        assert message.content == "Test message"
        assert message.metadata["source"] == "web_ui"
    
    def test_session_history_post_init(self):
        """Test SessionHistory post_init method."""
        session = SessionHistory(
            session_id="test-id",
            session_type=SessionType.CODE_QNA,
            status=SessionStatus.IN_PROGRESS,
            title="Test Session",
            description="Test description",
            created_at="2024-01-01T12:00:00",
            updated_at="2024-01-01T12:00:00"
        )
        
        # chat_messages should be initialized as empty list
        assert session.chat_messages == []
        assert isinstance(session.chat_messages, list)


if __name__ == "__main__":
    pytest.main([__file__]) 