#!/usr/bin/env python3
"""
AI CodeScan - Authenticated Session Manager

Enhanced session manager với user authentication support.
Replaces the original HistoryManager với multi-user functionality.
"""

import json
import uuid
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger

# Add paths for imports
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from .database import DatabaseManager
from .user_manager import User

# Define enums locally to avoid import issues
class SessionType(Enum):
    """Type of analysis session."""
    REPOSITORY_ANALYSIS = "repository_analysis"
    PR_REVIEW = "pr_review"
    CODE_QNA = "code_qna"

class SessionStatus(Enum):
    """Status of session."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class AuthenticatedScanResult:
    """Scan result với user association."""
    session_id: str
    user_id: int
    repository_url: Optional[str]
    repository_name: Optional[str]
    analysis_type: str
    findings_count: int
    severity_breakdown: Dict[str, int]
    summary: str
    detailed_results: Dict[str, Any]
    timestamp: str


@dataclass
class AuthenticatedChatMessage:
    """Chat message với user association."""
    session_id: str
    user_id: int
    role: str  # "user", "assistant"
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AuthenticatedSessionHistory:
    """Session history với user association."""
    session_id: str
    user_id: int
    session_type: SessionType
    status: SessionStatus
    title: str
    description: str
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None
    scan_result: Optional[AuthenticatedScanResult] = None
    chat_messages: List[AuthenticatedChatMessage] = None
    
    def __post_init__(self):
        if self.chat_messages is None:
            self.chat_messages = []


class AuthenticatedSessionManager:
    """
    Enhanced session manager với user authentication.
    
    Manages user-specific sessions, scan results, và chat history.
    Stores data in SQLite database với proper user isolation.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize authenticated session manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        logger.info("AuthenticatedSessionManager initialized")
    
    def create_session(
        self,
        user_id: int,
        session_type: SessionType,
        title: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create new session for user.
        
        Args:
            user_id: User ID
            session_type: Type of session
            title: Session title
            description: Session description
            metadata: Additional metadata
            
        Returns:
            str: Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # Insert session into database
            query = """
            INSERT INTO user_sessions 
            (session_id, user_id, session_type, title, description, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            self.db.execute_insert(
                query,
                (
                    session_id,
                    user_id,
                    session_type.value,
                    title,
                    description,
                    metadata_json
                )
            )
            
            logger.info(f"Created session for user {user_id}: {session_id} - {title}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    def update_session_status(self, session_id: str, user_id: int, status: SessionStatus) -> bool:
        """
        Update session status.
        
        Args:
            session_id: Session ID
            user_id: User ID (for security)
            status: New status
            
        Returns:
            bool: True if updated successfully
        """
        try:
            query = """
            UPDATE user_sessions 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ? AND user_id = ?
            """
            
            affected_rows = self.db.execute_update(
                query,
                (status.value, session_id, user_id)
            )
            
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Error updating session status: {str(e)}")
            return False
    
    def save_scan_result(
        self,
        session_id: str,
        user_id: int,
        scan_result: AuthenticatedScanResult
    ) -> bool:
        """
        Save scan result to session.
        
        Args:
            session_id: Session ID
            user_id: User ID (for security)
            scan_result: Scan result data
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Update session status
            self.update_session_status(session_id, user_id, SessionStatus.COMPLETED)
            
            # Insert scan result
            query = """
            INSERT INTO scan_results 
            (session_id, user_id, repository_url, repository_name, 
             analysis_type, findings_count, severity_breakdown, 
             summary, detailed_results)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_insert(
                query,
                (
                    session_id,
                    user_id,
                    scan_result.repository_url,
                    scan_result.repository_name,
                    scan_result.analysis_type,
                    scan_result.findings_count,
                    json.dumps(scan_result.severity_breakdown),
                    scan_result.summary,
                    json.dumps(scan_result.detailed_results)
                )
            )
            
            logger.info(f"Saved scan result for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving scan result: {str(e)}")
            return False
    
    def add_chat_message(
        self,
        session_id: str,
        user_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add chat message to session.
        
        Args:
            session_id: Session ID
            user_id: User ID (for security)
            role: Message role ("user" or "assistant")
            content: Message content
            metadata: Additional metadata
            
        Returns:
            bool: True if added successfully
        """
        try:
            # Insert chat message
            query = """
            INSERT INTO chat_messages 
            (session_id, user_id, role, content, metadata)
            VALUES (?, ?, ?, ?, ?)
            """
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            self.db.execute_insert(
                query,
                (session_id, user_id, role, content, metadata_json)
            )
            
            # Update session timestamp
            update_query = """
            UPDATE user_sessions 
            SET updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ? AND user_id = ?
            """
            
            self.db.execute_update(update_query, (session_id, user_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding chat message: {str(e)}")
            return False
    
    def get_session(self, session_id: str, user_id: int) -> Optional[AuthenticatedSessionHistory]:
        """
        Get session by ID (user-scoped).
        
        Args:
            session_id: Session ID
            user_id: User ID (for security)
            
        Returns:
            Optional[AuthenticatedSessionHistory]: Session or None if not found
        """
        try:
            # Get session basic info
            query = """
            SELECT session_id, user_id, session_type, status, title, 
                   description, created_at, updated_at, metadata
            FROM user_sessions 
            WHERE session_id = ? AND user_id = ?
            """
            
            result = self.db.execute_query(query, (session_id, user_id))
            
            if not result:
                return None
            
            session_data = result[0]
            
            # Parse metadata
            metadata = None
            if session_data['metadata']:
                try:
                    metadata = json.loads(session_data['metadata'])
                except json.JSONDecodeError:
                    pass
            
            # Get scan result if exists
            scan_result = self._get_scan_result(session_id, user_id)
            
            # Get chat messages
            chat_messages = self._get_chat_messages(session_id, user_id)
            
            return AuthenticatedSessionHistory(
                session_id=session_data['session_id'],
                user_id=session_data['user_id'],
                session_type=SessionType(session_data['session_type']),
                status=SessionStatus(session_data['status']),
                title=session_data['title'],
                description=session_data['description'],
                created_at=session_data['created_at'],
                updated_at=session_data['updated_at'],
                metadata=metadata,
                scan_result=scan_result,
                chat_messages=chat_messages
            )
            
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            return None
    
    def get_user_sessions(
        self,
        user_id: int,
        session_type: Optional[SessionType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AuthenticatedSessionHistory]:
        """
        Get all sessions for user với pagination.
        
        Args:
            user_id: User ID
            session_type: Optional session type filter
            limit: Maximum sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List[AuthenticatedSessionHistory]: List of sessions
        """
        try:
            conditions = ["user_id = ?"]
            params = [user_id]
            
            if session_type:
                conditions.append("session_type = ?")
                params.append(session_type.value)
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
            SELECT session_id, user_id, session_type, status, title, 
                   description, created_at, updated_at, metadata
            FROM user_sessions 
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """
            
            params.extend([limit, offset])
            result = self.db.execute_query(query, tuple(params))
            
            sessions = []
            for row in result:
                # Parse metadata
                metadata = None
                if row['metadata']:
                    try:
                        metadata = json.loads(row['metadata'])
                    except json.JSONDecodeError:
                        pass
                
                session = AuthenticatedSessionHistory(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    session_type=SessionType(row['session_type']),
                    status=SessionStatus(row['status']),
                    title=row['title'],
                    description=row['description'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    metadata=metadata
                    # Note: Not loading scan_result và chat_messages for list view performance
                )
                
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return []
    
    def delete_session(self, session_id: str, user_id: int) -> bool:
        """
        Delete session và all associated data.
        
        Args:
            session_id: Session ID
            user_id: User ID (for security)
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            # SQLite with foreign keys will automatically delete related records
            query = """
            DELETE FROM user_sessions 
            WHERE session_id = ? AND user_id = ?
            """
            
            affected_rows = self.db.execute_update(query, (session_id, user_id))
            
            if affected_rows > 0:
                logger.info(f"Deleted session: {session_id} for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False
    
    def get_user_session_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get session statistics for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: Session statistics
        """
        stats = {
            'total_sessions': 0,
            'by_type': {},
            'by_status': {},
            'recent_activity': []
        }
        
        try:
            # Total sessions
            result = self.db.execute_query("""
                SELECT COUNT(*) as total FROM user_sessions WHERE user_id = ?
            """, (user_id,))
            
            if result:
                stats['total_sessions'] = result[0]['total']
            
            # By type
            result = self.db.execute_query("""
                SELECT session_type, COUNT(*) as count
                FROM user_sessions 
                WHERE user_id = ?
                GROUP BY session_type
            """, (user_id,))
            
            for row in result:
                stats['by_type'][row['session_type']] = row['count']
            
            # By status
            result = self.db.execute_query("""
                SELECT status, COUNT(*) as count
                FROM user_sessions 
                WHERE user_id = ?
                GROUP BY status
            """, (user_id,))
            
            for row in result:
                stats['by_status'][row['status']] = row['count']
            
            # Recent activity
            result = self.db.execute_query("""
                SELECT session_id, title, session_type, status, updated_at
                FROM user_sessions 
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT 10
            """, (user_id,))
            
            stats['recent_activity'] = [
                {
                    'session_id': row['session_id'],
                    'title': row['title'],
                    'type': row['session_type'],
                    'status': row['status'],
                    'updated_at': row['updated_at']
                }
                for row in result
            ]
            
        except Exception as e:
            logger.error(f"Error getting user session stats: {str(e)}")
        
        return stats
    
    def _get_scan_result(self, session_id: str, user_id: int) -> Optional[AuthenticatedScanResult]:
        """Get scan result for session."""
        try:
            query = """
            SELECT session_id, user_id, repository_url, repository_name,
                   analysis_type, findings_count, severity_breakdown,
                   summary, detailed_results, timestamp
            FROM scan_results 
            WHERE session_id = ? AND user_id = ?
            """
            
            result = self.db.execute_query(query, (session_id, user_id))
            
            if not result:
                return None
            
            row = result[0]
            
            # Parse JSON fields
            severity_breakdown = {}
            detailed_results = {}
            
            try:
                if row['severity_breakdown']:
                    severity_breakdown = json.loads(row['severity_breakdown'])
                if row['detailed_results']:
                    detailed_results = json.loads(row['detailed_results'])
            except json.JSONDecodeError:
                pass
            
            return AuthenticatedScanResult(
                session_id=row['session_id'],
                user_id=row['user_id'],
                repository_url=row['repository_url'],
                repository_name=row['repository_name'],
                analysis_type=row['analysis_type'],
                findings_count=row['findings_count'],
                severity_breakdown=severity_breakdown,
                summary=row['summary'],
                detailed_results=detailed_results,
                timestamp=row['timestamp']
            )
            
        except Exception as e:
            logger.error(f"Error getting scan result: {str(e)}")
            return None
    
    def _get_chat_messages(self, session_id: str, user_id: int) -> List[AuthenticatedChatMessage]:
        """Get chat messages for session."""
        try:
            query = """
            SELECT session_id, user_id, role, content, timestamp, metadata
            FROM chat_messages 
            WHERE session_id = ? AND user_id = ?
            ORDER BY timestamp ASC
            """
            
            result = self.db.execute_query(query, (session_id, user_id))
            
            messages = []
            for row in result:
                # Parse metadata
                metadata = None
                if row['metadata']:
                    try:
                        metadata = json.loads(row['metadata'])
                    except json.JSONDecodeError:
                        pass
                
                message = AuthenticatedChatMessage(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    role=row['role'],
                    content=row['content'],
                    timestamp=row['timestamp'],
                    metadata=metadata
                )
                
                messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting chat messages: {str(e)}")
            return [] 