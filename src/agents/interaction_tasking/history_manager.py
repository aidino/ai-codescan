"""
History Manager

Manages chat history and scan history for AI CodeScan.
Provides read-only access to historical data without allowing continuation
of conversations to avoid context issues.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from loguru import logger


class SessionType(Enum):
    """Session type enumeration."""
    REPOSITORY_ANALYSIS = "repository_analysis"
    PR_REVIEW = "pr_review"
    CODE_QNA = "code_qna"


class SessionStatus(Enum):
    """Session status enumeration."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ScanResult:
    """Scan result data structure."""
    repository_url: str
    repository_name: str
    analysis_type: str
    findings_count: int
    severity_breakdown: Dict[str, int]
    summary: str
    detailed_results: Dict[str, Any]
    timestamp: str


@dataclass
class ChatMessage:
    """Chat message data structure."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SessionHistory:
    """Session history data structure."""
    session_id: str
    session_type: SessionType
    status: SessionStatus
    title: str
    description: str
    created_at: str
    updated_at: str
    scan_result: Optional[ScanResult] = None
    chat_messages: List[ChatMessage] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.chat_messages is None:
            self.chat_messages = []


class HistoryManager:
    """
    Manages session history storage and retrieval.
    
    Stores history in JSON files for simplicity and reliability.
    Could be extended to use Redis or database in the future.
    """
    
    def __init__(self, storage_path: str = "logs/history"):
        """Initialize history manager."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.sessions_file = self.storage_path / "sessions.json"
        self.chats_dir = self.storage_path / "chats"
        self.scans_dir = self.storage_path / "scans"
        
        # Create subdirectories
        self.chats_dir.mkdir(exist_ok=True)
        self.scans_dir.mkdir(exist_ok=True)
        
        logger.info(f"History manager initialized with storage: {self.storage_path}")

    def create_session(
        self, 
        session_type: SessionType, 
        title: str, 
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new session and return session ID."""
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        session = SessionHistory(
            session_id=session_id,
            session_type=session_type,
            status=SessionStatus.IN_PROGRESS,
            title=title,
            description=description,
            created_at=timestamp,
            updated_at=timestamp,
            metadata=metadata or {}
        )
        
        self._save_session(session)
        logger.info(f"Created new session: {session_id} - {title}")
        return session_id

    def update_session_status(self, session_id: str, status: SessionStatus) -> bool:
        """Update session status."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.status = status
        session.updated_at = datetime.now().isoformat()
        self._save_session(session)
        return True

    def save_scan_result(self, session_id: str, scan_result: ScanResult) -> bool:
        """Save scan result to session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.scan_result = scan_result
        session.status = SessionStatus.COMPLETED
        session.updated_at = datetime.now().isoformat()
        
        self._save_session(session)
        
        # Also save detailed scan data separately
        scan_file = self.scans_dir / f"{session_id}.json"
        with open(scan_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(scan_result), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved scan result for session: {session_id}")
        return True

    def add_chat_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add chat message to session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
        
        session.chat_messages.append(message)
        session.updated_at = datetime.now().isoformat()
        
        self._save_session(session)
        
        # Also save chat messages separately for performance
        chat_file = self.chats_dir / f"{session_id}.json"
        messages = [asdict(msg) for msg in session.chat_messages]
        with open(chat_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        
        return True

    def get_session(self, session_id: str) -> Optional[SessionHistory]:
        """Get session by ID."""
        sessions = self._load_all_sessions()
        return sessions.get(session_id)

    def get_all_sessions(self, session_type: Optional[SessionType] = None) -> List[SessionHistory]:
        """Get all sessions, optionally filtered by type."""
        sessions = self._load_all_sessions()
        session_list = list(sessions.values())
        
        if session_type:
            session_list = [s for s in session_list if s.session_type == session_type]
        
        # Sort by updated_at descending (newest first)
        session_list.sort(key=lambda x: x.updated_at, reverse=True)
        return session_list

    def get_recent_sessions(self, limit: int = 10, session_type: Optional[SessionType] = None) -> List[SessionHistory]:
        """Get recent sessions."""
        all_sessions = self.get_all_sessions(session_type)
        return all_sessions[:limit]

    def delete_session(self, session_id: str) -> bool:
        """Delete session and associated data."""
        sessions = self._load_all_sessions()
        if session_id not in sessions:
            return False
        
        # Remove from sessions
        del sessions[session_id]
        self._save_all_sessions(sessions)
        
        # Remove associated files
        chat_file = self.chats_dir / f"{session_id}.json"
        scan_file = self.scans_dir / f"{session_id}.json"
        
        for file_path in [chat_file, scan_file]:
            if file_path.exists():
                file_path.unlink()
        
        logger.info(f"Deleted session: {session_id}")
        return True

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about sessions."""
        sessions = self._load_all_sessions()
        
        stats = {
            "total_sessions": len(sessions),
            "by_type": {},
            "by_status": {},
            "recent_activity": []
        }
        
        for session in sessions.values():
            # Count by type
            type_key = session.session_type.value
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
            
            # Count by status
            status_key = session.status.value
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
        
        # Recent activity (last 10 sessions)
        recent = self.get_recent_sessions(10)
        stats["recent_activity"] = [
            {
                "session_id": s.session_id,
                "title": s.title,
                "type": s.session_type.value,
                "status": s.status.value,
                "updated_at": s.updated_at
            }
            for s in recent
        ]
        
        return stats

    def _save_session(self, session: SessionHistory) -> None:
        """Save single session to storage."""
        sessions = self._load_all_sessions()
        sessions[session.session_id] = session
        self._save_all_sessions(sessions)

    def _load_all_sessions(self) -> Dict[str, SessionHistory]:
        """Load all sessions from storage."""
        if not self.sessions_file.exists():
            return {}
        
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            sessions = {}
            for session_id, session_data in data.items():
                # Convert enum strings back to enums
                session_data['session_type'] = SessionType(session_data['session_type'])
                session_data['status'] = SessionStatus(session_data['status'])
                
                # Convert scan_result dict back to dataclass if exists
                if session_data.get('scan_result'):
                    session_data['scan_result'] = ScanResult(**session_data['scan_result'])
                
                # Convert chat_messages dicts back to dataclasses if exist
                if session_data.get('chat_messages'):
                    session_data['chat_messages'] = [
                        ChatMessage(**msg) for msg in session_data['chat_messages']
                    ]
                
                sessions[session_id] = SessionHistory(**session_data)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            return {}

    def _save_all_sessions(self, sessions: Dict[str, SessionHistory]) -> None:
        """Save all sessions to storage."""
        try:
            # Convert to serializable format
            data = {}
            for session_id, session in sessions.items():
                session_dict = asdict(session)
                # Convert enums to strings
                session_dict['session_type'] = session.session_type.value
                session_dict['status'] = session.status.value
                data[session_id] = session_dict
            
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving sessions: {e}") 