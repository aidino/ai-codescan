#!/usr/bin/env python3
"""
AI CodeScan - Authentication Service

Quản lý authentication sessions, tokens, và security operations.
"""

import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from loguru import logger

from .database import DatabaseManager
from .user_manager import UserManager, User, UserCredentials


@dataclass
class AuthSession:
    """Authentication session data."""
    session_token: str
    user_id: int
    user: Optional[User]
    created_at: str
    expires_at: str
    last_activity: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True


@dataclass
class AuthResult:
    """Authentication result."""
    success: bool
    user: Optional[User] = None
    session_token: Optional[str] = None
    expires_at: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SessionInfo:
    """Current session information."""
    user: User
    session_token: str
    expires_at: str
    time_remaining_seconds: int


class AuthService:
    """
    Authentication service.
    
    Handles login, logout, session management, và security operations.
    """
    
    def __init__(self, db_manager: DatabaseManager, session_duration_hours: int = 24):
        """
        Initialize AuthService.
        
        Args:
            db_manager: Database manager instance
            session_duration_hours: Session duration in hours
        """
        self.db = db_manager
        self.user_manager = UserManager(db_manager)
        self.session_duration_hours = session_duration_hours
        
        logger.info(f"AuthService initialized with {session_duration_hours}h session duration")
    
    def login(self, credentials: UserCredentials, 
              ip_address: Optional[str] = None,
              user_agent: Optional[str] = None) -> AuthResult:
        """
        Authenticate user và create session.
        
        Args:
            credentials: User login credentials
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            AuthResult: Authentication result with session info
        """
        try:
            # Authenticate user
            user = self.user_manager.authenticate_user(credentials)
            
            if not user:
                return AuthResult(
                    success=False,
                    error_message="Invalid username/email or password"
                )
            
            # Create session
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=self.session_duration_hours)
            
            # Save session to database
            query = """
            INSERT INTO auth_sessions 
            (session_token, user_id, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
            """
            
            self.db.execute_insert(
                query,
                (
                    session_token,
                    user.id,
                    expires_at.isoformat(),
                    ip_address,
                    user_agent
                )
            )
            
            logger.info(f"User logged in successfully: {user.username}")
            
            return AuthResult(
                success=True,
                user=user,
                session_token=session_token,
                expires_at=expires_at.isoformat()
            )
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return AuthResult(
                success=False,
                error_message="Login failed due to system error"
            )
    
    def logout(self, session_token: str) -> bool:
        """
        Logout user by invalidating session.
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            bool: True if logout successful
        """
        try:
            # Deactivate session
            query = """
            UPDATE auth_sessions 
            SET is_active = 0 
            WHERE session_token = ? AND is_active = 1
            """
            
            affected_rows = self.db.execute_update(query, (session_token,))
            
            if affected_rows > 0:
                logger.info(f"User logged out: session {session_token[:8]}...")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return False
    
    def validate_session(self, session_token: str) -> Optional[SessionInfo]:
        """
        Validate session token và return session info.
        
        Args:
            session_token: Session token to validate
            
        Returns:
            Optional[SessionInfo]: Session info if valid, None otherwise
        """
        try:
            # Get session from database
            query = """
            SELECT s.session_token, s.user_id, s.created_at, s.expires_at, 
                   s.last_activity, s.ip_address, s.user_agent, s.is_active,
                   u.id, u.username, u.email, u.role, u.is_active as user_active,
                   u.created_at as user_created, u.updated_at as user_updated,
                   u.last_login_at, u.profile_data, u.preferences
            FROM auth_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = ? AND s.is_active = 1 AND u.is_active = 1
            """
            
            result = self.db.execute_query(query, (session_token,))
            
            if not result:
                return None
            
            session_data = result[0]
            
            # Check if session expired
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            now = datetime.now()
            
            if now > expires_at:
                # Session expired, deactivate it
                self._deactivate_session(session_token)
                return None
            
            # Update last activity
            self._update_session_activity(session_token)
            
            # Create user object
            from .user_manager import UserRole
            user = User(
                id=session_data['id'],
                username=session_data['username'],
                email=session_data['email'],
                role=UserRole(session_data['role']),
                is_active=bool(session_data['user_active']),
                created_at=session_data['user_created'],
                updated_at=session_data['user_updated'],
                last_login_at=session_data['last_login_at'],
                profile_data=session_data['profile_data'],
                preferences=session_data['preferences']
            )
            
            # Calculate time remaining
            time_remaining = (expires_at - now).total_seconds()
            
            return SessionInfo(
                user=user,
                session_token=session_token,
                expires_at=expires_at.isoformat(),
                time_remaining_seconds=int(time_remaining)
            )
            
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return None
    
    def refresh_session(self, session_token: str) -> Optional[AuthResult]:
        """
        Refresh session expiration time.
        
        Args:
            session_token: Session token to refresh
            
        Returns:
            Optional[AuthResult]: New session info if successful
        """
        try:
            # Validate current session
            session_info = self.validate_session(session_token)
            
            if not session_info:
                return None
            
            # Extend expiration time
            new_expires_at = datetime.now() + timedelta(hours=self.session_duration_hours)
            
            query = """
            UPDATE auth_sessions 
            SET expires_at = ?, last_activity = CURRENT_TIMESTAMP
            WHERE session_token = ? AND is_active = 1
            """
            
            affected_rows = self.db.execute_update(
                query,
                (new_expires_at.isoformat(), session_token)
            )
            
            if affected_rows > 0:
                return AuthResult(
                    success=True,
                    user=session_info.user,
                    session_token=session_token,
                    expires_at=new_expires_at.isoformat()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Session refresh error: {str(e)}")
            return None
    
    def get_user_sessions(self, user_id: int) -> List[AuthSession]:
        """
        Get all active sessions for user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[AuthSession]: List of active sessions
        """
        try:
            query = """
            SELECT session_token, user_id, created_at, expires_at, 
                   last_activity, ip_address, user_agent, is_active
            FROM auth_sessions 
            WHERE user_id = ? AND is_active = 1
            ORDER BY last_activity DESC
            """
            
            result = self.db.execute_query(query, (user_id,))
            
            sessions = []
            for row in result:
                sessions.append(AuthSession(
                    session_token=row['session_token'],
                    user_id=row['user_id'],
                    user=None,  # Don't load user data for session list
                    created_at=row['created_at'],
                    expires_at=row['expires_at'],
                    last_activity=row['last_activity'],
                    ip_address=row['ip_address'],
                    user_agent=row['user_agent'],
                    is_active=bool(row['is_active'])
                ))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return []
    
    def logout_all_sessions(self, user_id: int, except_session: Optional[str] = None) -> int:
        """
        Logout all sessions for user.
        
        Args:
            user_id: User ID
            except_session: Session token to keep active (current session)
            
        Returns:
            int: Number of sessions logged out
        """
        try:
            if except_session:
                query = """
                UPDATE auth_sessions 
                SET is_active = 0
                WHERE user_id = ? AND session_token != ? AND is_active = 1
                """
                affected_rows = self.db.execute_update(query, (user_id, except_session))
            else:
                query = """
                UPDATE auth_sessions 
                SET is_active = 0
                WHERE user_id = ? AND is_active = 1
                """
                affected_rows = self.db.execute_update(query, (user_id,))
            
            logger.info(f"Logged out {affected_rows} sessions for user {user_id}")
            return affected_rows
            
        except Exception as e:
            logger.error(f"Error logging out sessions: {str(e)}")
            return 0
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            query = """
            UPDATE auth_sessions 
            SET is_active = 0
            WHERE expires_at < CURRENT_TIMESTAMP AND is_active = 1
            """
            
            affected_rows = self.db.execute_update(query)
            
            if affected_rows > 0:
                logger.info(f"Cleaned up {affected_rows} expired sessions")
            
            return affected_rows
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")
            return 0
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """
        Get authentication statistics.
        
        Returns:
            Dict[str, Any]: Authentication stats
        """
        stats = {
            'active_sessions': 0,
            'total_sessions_today': 0,
            'unique_users_today': 0,
            'sessions_by_user': {}
        }
        
        try:
            # Active sessions
            result = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM auth_sessions 
                WHERE is_active = 1 AND expires_at > CURRENT_TIMESTAMP
            """)
            
            if result:
                stats['active_sessions'] = result[0]['count']
            
            # Sessions today
            result = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM auth_sessions 
                WHERE created_at >= date('now')
            """)
            
            if result:
                stats['total_sessions_today'] = result[0]['count']
            
            # Unique users today
            result = self.db.execute_query("""
                SELECT COUNT(DISTINCT user_id) as count
                FROM auth_sessions 
                WHERE created_at >= date('now')
            """)
            
            if result:
                stats['unique_users_today'] = result[0]['count']
            
            # Sessions by user (active only)
            result = self.db.execute_query("""
                SELECT u.username, COUNT(*) as session_count
                FROM auth_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.is_active = 1 AND s.expires_at > CURRENT_TIMESTAMP
                GROUP BY u.id, u.username
                ORDER BY session_count DESC
            """)
            
            for row in result:
                stats['sessions_by_user'][row['username']] = row['session_count']
                
        except Exception as e:
            logger.error(f"Error getting auth stats: {str(e)}")
        
        return stats
    
    def _deactivate_session(self, session_token: str) -> None:
        """Deactivate expired session."""
        try:
            query = "UPDATE auth_sessions SET is_active = 0 WHERE session_token = ?"
            self.db.execute_update(query, (session_token,))
        except Exception as e:
            logger.warning(f"Failed to deactivate session: {str(e)}")
    
    def _update_session_activity(self, session_token: str) -> None:
        """Update session last activity timestamp."""
        try:
            query = """
            UPDATE auth_sessions 
            SET last_activity = CURRENT_TIMESTAMP 
            WHERE session_token = ?
            """
            self.db.execute_update(query, (session_token,))
        except Exception as e:
            logger.warning(f"Failed to update session activity: {str(e)}") 